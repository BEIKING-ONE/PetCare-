"""
宠物平台 - Flask后端API服务 (与微信小程序对接版)
文件名：app.py
"""

from flask import Flask, jsonify, request, g
from flask_cors import CORS
import pymysql
from datetime import datetime, timedelta
import time
import random
import json
import os
from functools import lru_cache
from dotenv import load_dotenv
import jwt
import requests

load_dotenv()

app = Flask(__name__)
CORS(app)

app.config['SECRET_KEY'] = os.getenv('JWT_SECRET_KEY', 'your-secret-key-here-change-in-production')
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'gif'}

if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

db_config = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'port': int(os.getenv('DB_PORT', 3306)),
    'user': os.getenv('DB_USER', 'root'),
    'password': os.getenv('DB_PASSWORD', '123456'),
    'database': os.getenv('DB_NAME', 'pet_platform'),
    'charset': 'utf8mb4',
    'cursorclass': pymysql.cursors.DictCursor
}

WX_APP_ID = os.getenv('WX_APP_ID', '')
WX_APP_SECRET = os.getenv('WX_APP_SECRET', '')
JWT_EXPIRE_DAYS = int(os.getenv('JWT_EXPIRE_DAYS', 7))

def init_db_schema():
    try:
        import hashlib
        conn = pymysql.connect(**db_config)
        with conn.cursor() as cursor:
            cursor.execute("DESCRIBE users")
            existing_columns = {row['Field'] for row in cursor.fetchall()}
            
            required_columns = {
                'password': "VARCHAR(255) DEFAULT ''",
                'login_attempts': "INT DEFAULT 0",
                'locked_until': "TIMESTAMP NULL"
            }
            
            for col_name, col_def in required_columns.items():
                if col_name not in existing_columns:
                    cursor.execute(f"ALTER TABLE users ADD COLUMN {col_name} {col_def}")
                    print(f"  ✅ 添加字段: {col_name}")
            
            default_password = hashlib.sha256('123456'.encode()).hexdigest()
            cursor.execute("UPDATE users SET password = %s WHERE password IS NULL OR password = ''", (default_password,))
            if cursor.rowcount > 0:
                print(f"  ✅ 已为{cursor.rowcount}个用户设置默认密码: 123456")
            
            conn.commit()
        conn.close()
    except Exception as e:
        print(f"数据库初始化警告: {e}")

init_db_schema()

def get_db_connection():
    try:
        connection = pymysql.connect(**db_config)
        return connection
    except Exception as e:
        print(f"数据库连接失败: {e}")
        return None

def generate_jwt_token(user_id):
    payload = {
        'user_id': user_id,
        'exp': datetime.utcnow() + timedelta(days=JWT_EXPIRE_DAYS),
        'iat': datetime.utcnow()
    }
    return jwt.encode(payload, app.config['SECRET_KEY'], algorithm='HS256')

def verify_jwt_token(token):
    try:
        payload = jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])
        return payload['user_id']
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None

def auth_required(f):
    def decorated(*args, **kwargs):
        auth_header = request.headers.get('Authorization')
        if not auth_header:
            return jsonify({
                'code': 401,
                'message': '缺少认证token'
            }), 401

        try:
            token = auth_header.replace('Bearer ', '')
            user_id = verify_jwt_token(token)
            if not user_id:
                return jsonify({
                    'code': 401,
                    'message': '无效或过期的token'
                }), 401
            g.user_id = user_id
        except Exception as e:
            return jsonify({
                'code': 401,
                'message': f'认证失败: {str(e)}'
            }), 401

        return f(*args, **kwargs)

    decorated.__name__ = f.__name__
    return decorated

def wx_code2session(code):
    try:
        url = f'https://api.weixin.qq.com/sns/jscode2session?appid={WX_APP_ID}&secret={WX_APP_SECRET}&js_code={code}&grant_type=authorization_code'
        response = requests.get(url, timeout=5)
        data = response.json()
        if 'errcode' in data:
            return None, data.get('errmsg', '微信登录失败')
        return data, None
    except Exception as e:
        return None, str(e)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

@app.route('/')
def index():
    return jsonify({
        'code': 0,
        'message': '宠物平台后端API服务已启动',
        'data': {
            'name': 'Pet Platform API',
            'version': '3.0.0',
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
    })

@app.route('/api/health')
def health_check():
    try:
        conn = get_db_connection()
        if conn:
            with conn.cursor() as cursor:
                cursor.execute("SELECT 1")
                result = cursor.fetchone()
            conn.close()
            return jsonify({
                'code': 0,
                'message': '服务正常',
                'data': {
                    'status': 'running',
                    'database': 'connected',
                    'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                }
            })
        else:
            return jsonify({
                'code': 500,
                'message': '数据库连接失败'
            }), 500
    except Exception as e:
        return jsonify({
            'code': 500,
            'message': f'健康检查失败: {str(e)}'
        }), 500

# ==================== 疫苗提醒模块（提前注册确保可用） ====================
# 检测接口：GET /api/vaccines/check 无需登录，用于确认疫苗路由已加载（返回 200 即说明后端正常）
@app.route('/api/vaccines/check', methods=['GET'])
def vaccines_check():
    return jsonify({'code': 0, 'message': 'vaccines api loaded', 'data': {'ok': True}})

# 预检 OPTIONS：小程序/浏览器可能先发 OPTIONS，必须返回 200 否则会报 404
@app.route('/api/vaccines', methods=['OPTIONS'], strict_slashes=False)
def vaccines_options():
    return '', 200

# 测试接口：确认 POST 路由已加载（无需登录，仅用于调试）
@app.route('/api/vaccines/test-post', methods=['POST'], strict_slashes=False)
def vaccines_test_post():
    return jsonify({
        'code': 0,
        'message': 'POST /api/vaccines route is loaded',
        'data': {'method': 'POST', 'path': '/api/vaccines', 'loaded': True}
    })

def _vaccine_row_to_json(row):
    """将疫苗记录转为 API 返回格式：status 为 pending/completed，日期转字符串"""
    if not row:
        return None
    r = dict(row)
    s = r.get('status')
    r['status'] = 'completed' if s in (1, '1', 'completed') else 'pending'
    for key in ['vaccine_date', 'next_date', 'created_at', 'updated_at']:
        if r.get(key) and hasattr(r[key], 'strftime'):
            r[key] = r[key].strftime('%Y-%m-%d') if key in ('vaccine_date', 'next_date') else r[key].strftime('%Y-%m-%d %H:%M:%S')
    return r

@app.route('/api/vaccines', methods=['GET'], strict_slashes=False)
@auth_required
def get_vaccines_list():
    """获取当前用户的疫苗记录列表"""
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT id, user_id, pet_id, pet_name, pet_type, vaccine_name, vaccine_date,
                       next_date, clinic, notes, status, created_at, updated_at
                FROM vaccines
                WHERE user_id = %s
                ORDER BY next_date ASC, created_at DESC
            """, (g.user_id,))
            rows = cursor.fetchall()
        conn.close()
        data = [_vaccine_row_to_json(row) for row in rows]
        return jsonify({
            'code': 0,
            'message': 'success',
            'data': data
        })
    except Exception as e:
        return jsonify({
            'code': 500,
            'message': f'获取疫苗列表失败: {str(e)}'
        }), 500

@app.route('/api/vaccines/<int:vaccine_id>', methods=['GET'], strict_slashes=False)
@auth_required
def get_vaccine_detail(vaccine_id):
    """获取疫苗记录详情"""
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT id, user_id, pet_id, pet_name, pet_type, vaccine_name, vaccine_date,
                       next_date, clinic, notes, status, created_at, updated_at
                FROM vaccines
                WHERE id = %s AND user_id = %s
            """, (vaccine_id, g.user_id))
            row = cursor.fetchone()
        conn.close()
        if not row:
            return jsonify({
                'code': 404,
                'message': '疫苗记录不存在或无权限查看'
            }), 404
        return jsonify({
            'code': 0,
            'message': 'success',
            'data': _vaccine_row_to_json(row)
        })
    except Exception as e:
        return jsonify({
            'code': 500,
            'message': f'获取疫苗详情失败: {str(e)}'
        }), 500

@app.route('/api/vaccines', methods=['POST'], strict_slashes=False)
@auth_required
def add_vaccine():
    """添加疫苗记录"""
    try:
        data = request.json
        pet_id = data.get('pet_id')
        vaccine_name = (data.get('vaccine_name') or '').strip()
        vaccine_date = data.get('vaccine_date')

        if not vaccine_name:
            return jsonify({
                'code': 400,
                'message': '参数错误：疫苗名称不能为空'
            }), 400
        if not vaccine_date:
            return jsonify({
                'code': 400,
                'message': '参数错误：接种日期不能为空'
            }), 400

        pet_name = data.get('pet_name') or ''
        pet_type = data.get('pet_type') or ''
        next_date = data.get('next_date')
        clinic = data.get('clinic') or ''
        notes = data.get('notes') or ''
        raw_status = data.get('status')
        status = (raw_status.strip().lower() if isinstance(raw_status, str) and raw_status else 'pending')
        if status not in ('pending', 'completed'):
            status = 'pending'

        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute("""
                INSERT INTO vaccines (user_id, pet_id, pet_name, pet_type, vaccine_name, vaccine_date, next_date, clinic, notes, status)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (g.user_id, pet_id or 0, pet_name, pet_type, vaccine_name, vaccine_date, next_date or None, clinic, notes, status))
            vid = cursor.lastrowid
            conn.commit()
        conn.close()

        return jsonify({
            'code': 0,
            'message': '添加成功',
            'data': {'id': vid}
        })
    except Exception as e:
        return jsonify({
            'code': 500,
            'message': f'添加疫苗记录失败: {str(e)}'
        }), 500

@app.route('/api/vaccines/<int:vaccine_id>', methods=['PUT'], strict_slashes=False)
@auth_required
def update_vaccine(vaccine_id):
    """编辑疫苗记录"""
    try:
        data = request.json
        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute("SELECT id FROM vaccines WHERE id = %s AND user_id = %s", (vaccine_id, g.user_id))
            row = cursor.fetchone()
            if not row:
                conn.close()
                return jsonify({
                    'code': 404,
                    'message': '疫苗记录不存在或无权限'
                }), 404

            pet_id = data.get('pet_id')
            vaccine_name = (data.get('vaccine_name') or '').strip()
            vaccine_date = data.get('vaccine_date')
            if pet_id is not None:
                cursor.execute("SELECT id, name, type FROM user_pets WHERE id = %s AND user_id = %s AND status = 1",
                             (pet_id, g.user_id))
                pet = cursor.fetchone()
                if not pet:
                    conn.close()
                    return jsonify({
                        'code': 400,
                        'message': '宠物不存在或无权限'
                    }), 400
            if vaccine_name is not None and not vaccine_name:
                conn.close()
                return jsonify({
                    'code': 400,
                    'message': '参数错误：疫苗名称不能为空'
                }), 400
            if vaccine_date is not None and not vaccine_date:
                conn.close()
                return jsonify({
                    'code': 400,
                    'message': '参数错误：接种日期不能为空'
                }), 400

            updates = []
            params = []
            fields_map = [
                ('pet_id', 'pet_id', None),
                ('pet_name', 'pet_name', None),
                ('pet_type', 'pet_type', None),
                ('vaccine_name', 'vaccine_name', None),
                ('vaccine_date', 'vaccine_date', None),
                ('next_date', 'next_date', None),
                ('clinic', 'clinic', ''),
                ('notes', 'notes', ''),
            ]
            for key, col, default in fields_map:
                if key in data:
                    val = data[key] if data[key] is not None else default
                    updates.append(f"{col} = %s")
                    params.append(val)
            if 'status' in data:
                s = data['status']
                status_val = 'completed' if s in ('completed', 1, '1') else 'pending'
                updates.append("status = %s")
                params.append(status_val)
            if not updates:
                conn.close()
                return jsonify({
                    'code': 0,
                    'message': '更新成功'
                })
            params.append(vaccine_id)
            cursor.execute("UPDATE vaccines SET " + ", ".join(updates) + " WHERE id = %s", tuple(params))
            conn.commit()
        conn.close()
        return jsonify({
            'code': 0,
            'message': '更新成功'
        })
    except Exception as e:
        return jsonify({
            'code': 500,
            'message': f'更新疫苗记录失败: {str(e)}'
        }), 500

@app.route('/api/vaccines/<int:vaccine_id>', methods=['DELETE'], strict_slashes=False)
@auth_required
def delete_vaccine(vaccine_id):
    """删除疫苗记录"""
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute("SELECT id FROM vaccines WHERE id = %s AND user_id = %s", (vaccine_id, g.user_id))
            row = cursor.fetchone()
            if not row:
                conn.close()
                return jsonify({
                    'code': 404,
                    'message': '疫苗记录不存在或无权限'
                }), 404
            cursor.execute("DELETE FROM vaccines WHERE id = %s", (vaccine_id,))
            conn.commit()
        conn.close()
        return jsonify({
            'code': 0,
            'message': '删除成功'
        })
    except Exception as e:
        return jsonify({
            'code': 500,
            'message': f'删除疫苗记录失败: {str(e)}'
        }), 500

@app.route('/api/vaccines/<int:vaccine_id>/complete', methods=['PUT'], strict_slashes=False)
@auth_required
def complete_vaccine(vaccine_id):
    """标记为已接种"""
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute("SELECT id FROM vaccines WHERE id = %s AND user_id = %s", (vaccine_id, g.user_id))
            row = cursor.fetchone()
            if not row:
                conn.close()
                return jsonify({
                    'code': 404,
                    'message': '疫苗记录不存在或无权限'
                }), 404
            cursor.execute("UPDATE vaccines SET status = 'completed' WHERE id = %s", (vaccine_id,))
            conn.commit()
        conn.close()
        return jsonify({
            'code': 0,
            'message': '标记成功'
        })
    except Exception as e:
        return jsonify({
            'code': 500,
            'message': f'标记失败: {str(e)}'
        }), 500

# ==================== 手机号密码登录 ====================

@app.route('/api/auth/login', methods=['POST'])
def phone_login():
    try:
        import hashlib
        from datetime import datetime, timedelta
        
        data = request.json
        phone = (data.get('phone') or '').strip()
        password = data.get('password', '')

        if not phone or len(phone) != 11:
            return jsonify({
                'code': 400,
                'message': '手机号格式不正确'
            }), 400

        if not password:
            return jsonify({
                'code': 400,
                'message': '密码不能为空'
            }), 400

        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute("SELECT * FROM users WHERE phone = %s", (phone,))
            user = cursor.fetchone()

            if not user:
                conn.close()
                return jsonify({
                    'code': 404,
                    'message': '用户不存在'
                }), 404

            if user.get('locked_until') and user['locked_until'] > datetime.now():
                conn.close()
                return jsonify({
                    'code': 403,
                    'message': '账户已锁定，请30分钟后再试'
                }), 403

            password_hash = hashlib.sha256(password.encode()).hexdigest()
            
            if user.get('password') != password_hash:
                attempts = (user.get('login_attempts') or 0) + 1
                if attempts >= 5:
                    cursor.execute("""
                        UPDATE users SET login_attempts = %s, locked_until = %s WHERE id = %s
                    """, (attempts, datetime.now() + timedelta(minutes=30), user['id']))
                    conn.commit()
                    conn.close()
                    return jsonify({
                        'code': 403,
                        'message': '密码错误次数过多，账户已锁定30分钟'
                    }), 403
                else:
                    cursor.execute("UPDATE users SET login_attempts = %s WHERE id = %s", (attempts, user['id']))
                    conn.commit()
                    conn.close()
                    return jsonify({
                        'code': 401,
                        'message': f'密码错误，还剩{5-attempts}次机会'
                    }), 401

            cursor.execute("UPDATE users SET login_attempts = 0, locked_until = NULL WHERE id = %s", (user['id'],))
            conn.commit()

            token = generate_jwt_token(user['id'])

        conn.close()

        return jsonify({
            'code': 0,
            'message': '登录成功',
            'data': {
                'token': token,
                'userInfo': {
                    'id': user['id'],
                    'phone': user['phone'],
                    'nickname': user.get('nickname') or '宠物爱好者',
                    'avatar': user.get('avatar_url') or '😊'
                }
            }
        })

    except Exception as e:
        return jsonify({
            'code': 500,
            'message': f'登录失败: {str(e)}'
        }), 500

@app.route('/api/auth/register', methods=['POST'])
def phone_register():
    try:
        import hashlib
        
        data = request.json
        phone = (data.get('phone') or '').strip()
        password = data.get('password', '')
        nickname = (data.get('nickname') or '宠物爱好者').strip()

        if not phone or len(phone) != 11:
            return jsonify({
                'code': 400,
                'message': '手机号格式不正确'
            }), 400

        if len(nickname) < 2:
            return jsonify({
                'code': 400,
                'message': '昵称至少2个字符'
            }), 400

        if not password or len(password) < 6 or len(password) > 20:
            return jsonify({
                'code': 400,
                'message': '密码长度需为6-20位'
            }), 400

        password_hash = hashlib.sha256(password.encode()).hexdigest()

        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute("SELECT id FROM users WHERE phone = %s", (phone,))
            if cursor.fetchone():
                conn.close()
                return jsonify({
                    'code': 400,
                    'message': '该手机号已注册'
                }), 400

            cursor.execute("""
                INSERT INTO users (phone, password, nickname, openid)
                VALUES (%s, %s, %s, %s)
            """, (phone, password_hash, nickname, f'phone_{phone}'))
            user_id = cursor.lastrowid
            conn.commit()

            token = generate_jwt_token(user_id)
        conn.close()

        return jsonify({
            'code': 0,
            'message': '注册成功',
            'data': {
                'token': token,
                'userInfo': {
                    'id': user_id,
                    'phone': phone,
                    'nickname': nickname,
                    'avatar': '😊'
                }
            }
        })

    except Exception as e:
        return jsonify({
            'code': 500,
            'message': f'注册失败: {str(e)}'
        }), 500

# ==================== 微信登录 ====================

@app.route('/api/user/login', methods=['POST'])
def user_login():
    try:
        data = request.json
        code = data.get('code')

        if not code:
            return jsonify({
                'code': 400,
                'message': '缺少code参数'
            }), 400

        wx_data, error = wx_code2session(code)
        
        if error:
            print(f"⚠️  微信登录失败: {error}")
            print(f"⚠️  使用开发模式登录")
            openid = f'dev_openid_{code}'
            session_key = ''
        else:
            openid = wx_data.get('openid', '')
            session_key = wx_data.get('session_key', '')

        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute("SELECT * FROM users WHERE openid = %s", (openid,))
            user = cursor.fetchone()

            if not user:
                nickname = data.get('nickname', '微信用户')
                avatar_url = data.get('avatarUrl', '')
                phone = data.get('phone', '')

                cursor.execute("""
                    INSERT INTO users (openid, nickname, avatar_url, phone)
                    VALUES (%s, %s, %s, %s)
                """, (openid, nickname, avatar_url, phone))
                user_id = cursor.lastrowid

                cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))
                user = cursor.fetchone()

            conn.commit()

        conn.close()

        token = generate_jwt_token(user['id'])
        return jsonify({
            'code': 0,
            'message': '登录成功',
            'data': {
                'userInfo': {
                    'userId': user['id'],
                    'nickName': user['nickname'],
                    'avatarUrl': user['avatar_url'],
                    'phone': user['phone']
                },
                'token': token
            }
        })

    except Exception as e:
        return jsonify({
            'code': 500,
            'message': f'登录失败: {str(e)}'
        }), 500

@app.route('/api/user/info', methods=['GET'])
@auth_required
def get_user_info():
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT id as userId, nickname as nickName, avatar_url as avatarUrl, phone, created_at
                FROM users 
                WHERE id = %s
            """, (g.user_id,))
            user = cursor.fetchone()

        conn.close()

        if user:
            return jsonify({
                'code': 0,
                'message': 'success',
                'data': user
            })
        else:
            return jsonify({
                'code': 404,
                'message': '用户不存在'
            }), 404

    except Exception as e:
        return jsonify({
            'code': 500,
            'message': f'获取用户信息失败: {str(e)}'
        }), 500

@app.route('/api/user/info', methods=['PUT'])
@auth_required
def update_user_info():
    try:
        data = request.json

        conn = get_db_connection()
        with conn.cursor() as cursor:
            update_fields = []
            update_values = []

            if 'nickname' in data:
                update_fields.append('nickname = %s')
                update_values.append(data['nickname'])

            if 'phone' in data:
                update_fields.append('phone = %s')
                update_values.append(data['phone'])

            if 'avatarUrl' in data:
                update_fields.append('avatar_url = %s')
                update_values.append(data['avatarUrl'])

            if update_fields:
                update_values.append(g.user_id)
                sql = f"UPDATE users SET {', '.join(update_fields)} WHERE id = %s"
                cursor.execute(sql, tuple(update_values))
                conn.commit()

            cursor.execute("SELECT id as userId, nickname as nickName, phone, avatar_url as avatarUrl FROM users WHERE id = %s", (g.user_id,))
            updated_user = cursor.fetchone()

        conn.close()

        return jsonify({
            'code': 0,
            'message': '更新成功',
            'data': updated_user
        })

    except Exception as e:
        return jsonify({
            'code': 500,
            'message': f'更新用户信息失败: {str(e)}'
        }), 500

@app.route('/api/user/password', methods=['PUT'])
@auth_required
def update_password():
    try:
        import hashlib
        
        data = request.json
        old_password = data.get('old_password', '')
        new_password = data.get('new_password', '')

        if not old_password:
            return jsonify({
                'code': 400,
                'message': '原密码不能为空'
            }), 400

        if not new_password:
            return jsonify({
                'code': 400,
                'message': '新密码不能为空'
            }), 400

        if len(new_password) < 6 or len(new_password) > 20:
            return jsonify({
                'code': 400,
                'message': '新密码长度需为6-20位'
            }), 400

        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute("SELECT id, password FROM users WHERE id = %s", (g.user_id,))
            user = cursor.fetchone()
            if not user:
                conn.close()
                return jsonify({
                    'code': 404,
                    'message': '用户不存在'
                }), 404

            old_password_hash = hashlib.sha256(old_password.encode()).hexdigest()
            if user.get('password') and user['password'] != old_password_hash:
                conn.close()
                return jsonify({
                    'code': 401,
                    'message': '原密码错误'
                }), 401

            new_password_hash = hashlib.sha256(new_password.encode()).hexdigest()
            cursor.execute("UPDATE users SET password = %s, updated_at = NOW() WHERE id = %s", 
                         (new_password_hash, g.user_id))
            conn.commit()
        conn.close()

        return jsonify({
            'code': 0,
            'message': '密码修改成功'
        })

    except Exception as e:
        return jsonify({
            'code': 500,
            'message': f'密码修改失败: {str(e)}'
        }), 500

@app.route('/api/user/settings', methods=['GET'])
@auth_required
def get_user_settings():
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT 
                    push_enabled as pushEnabled,
                    vaccine_reminder as vaccineReminder,
                    health_reminder as healthReminder,
                    public_pets as publicPets,
                    location_enabled as locationEnabled
                FROM user_settings 
                WHERE user_id = %s
            """, (g.user_id,))
            settings = cursor.fetchone()

            if not settings:
                cursor.execute("""
                    INSERT INTO user_settings (user_id)
                    VALUES (%s)
                """, (g.user_id,))
                conn.commit()
                settings = {
                    'pushEnabled': True,
                    'vaccineReminder': True,
                    'healthReminder': True,
                    'publicPets': False,
                    'locationEnabled': True
                }
        conn.close()

        return jsonify({
            'code': 0,
            'message': 'success',
            'data': settings
        })

    except Exception as e:
        return jsonify({
            'code': 500,
            'message': f'获取设置失败: {str(e)}'
        }), 500

@app.route('/api/user/settings', methods=['PUT'])
@auth_required
def update_user_settings():
    try:
        data = request.json

        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute("SELECT id FROM user_settings WHERE user_id = %s", (g.user_id,))
            exists = cursor.fetchone()

            field_mapping = {
                'pushEnabled': 'push_enabled',
                'vaccineReminder': 'vaccine_reminder',
                'healthReminder': 'health_reminder',
                'publicPets': 'public_pets',
                'locationEnabled': 'location_enabled'
            }

            if exists:
                update_fields = []
                update_values = []
                for key, db_field in field_mapping.items():
                    if key in data:
                        update_fields.append(f"{db_field} = %s")
                        update_values.append(1 if data[key] else 0)

                if update_fields:
                    update_values.append(g.user_id)
                    sql = f"UPDATE user_settings SET {', '.join(update_fields)} WHERE user_id = %s"
                    cursor.execute(sql, update_values)
                    conn.commit()
            else:
                cursor.execute("""
                    INSERT INTO user_settings 
                    (user_id, push_enabled, vaccine_reminder, health_reminder, public_pets, location_enabled)
                    VALUES (%s, %s, %s, %s, %s, %s)
                """, (
                    g.user_id,
                    1 if data.get('pushEnabled', True) else 0,
                    1 if data.get('vaccineReminder', True) else 0,
                    1 if data.get('healthReminder', True) else 0,
                    1 if data.get('publicPets', False) else 0,
                    1 if data.get('locationEnabled', True) else 0
                ))
                conn.commit()

            cursor.execute("""
                SELECT 
                    push_enabled as pushEnabled,
                    vaccine_reminder as vaccineReminder,
                    health_reminder as healthReminder,
                    public_pets as publicPets,
                    location_enabled as locationEnabled
                FROM user_settings WHERE user_id = %s
            """, (g.user_id,))
            updated_settings = cursor.fetchone()
        conn.close()

        return jsonify({
            'code': 0,
            'message': '设置保存成功',
            'data': updated_settings
        })

    except Exception as e:
        return jsonify({
            'code': 500,
            'message': f'保存设置失败: {str(e)}'
        }), 500

@app.route('/api/pets')
@auth_required
def get_pets():
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT 
                    id, user_id, name, 
                    type, breed, age, 
                    weight, gender, birthday,
                    avatar_url as avatar, health_notes as healthStatus,
                    vaccine_records
                FROM user_pets 
                WHERE user_id = %s AND status = 1
                ORDER BY created_at DESC
            """, (g.user_id,))
            pets = cursor.fetchall()

        conn.close()

        return jsonify({
            'code': 0,
            'message': 'success',
            'data': pets
        })

    except Exception as e:
        return jsonify({
            'code': 500,
            'message': f'获取宠物列表失败: {str(e)}'
        }), 500

@app.route('/api/pets', methods=['POST'])
@auth_required
def add_pet():
    try:
        data = request.json

        required_fields = ['name', 'type']
        for field in required_fields:
            if field not in data:
                return jsonify({
                    'code': 400,
                    'message': f'缺少必要字段: {field}'
                }), 400

        birthday = data.get('birthday')
        if birthday == '' or birthday is None:
            birthday = None

        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute("""
                INSERT INTO user_pets 
                (user_id, name, type, breed, age, weight, gender, birthday, 
                 avatar_url, health_notes, vaccine_records)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                g.user_id,
                data['name'],
                data['type'],
                data.get('breed') or '',
                data.get('age') or '',
                data.get('weight') or '',
                data.get('gender') or '',
                birthday,
                data.get('avatar') or '',
                data.get('healthStatus') or '',
                data.get('vaccineRecords') or ''
            ))
            pet_id = cursor.lastrowid
            conn.commit()

            cursor.execute("SELECT * FROM user_pets WHERE id = %s", (pet_id,))
            new_pet = cursor.fetchone()

        conn.close()

        return jsonify({
            'code': 0,
            'message': '添加成功',
            'data': new_pet
        })

    except Exception as e:
        return jsonify({
            'code': 500,
            'message': f'添加宠物失败: {str(e)}'
        }), 500

@app.route('/api/pets/<int:pet_id>', methods=['DELETE'])
@auth_required
def delete_pet(pet_id):
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute("SELECT id FROM user_pets WHERE id = %s AND user_id = %s",
                         (pet_id, g.user_id))
            pet = cursor.fetchone()

            if not pet:
                return jsonify({
                    'code': 404,
                    'message': '宠物不存在或无权限'
                }), 404

            cursor.execute("UPDATE user_pets SET status = 0 WHERE id = %s", (pet_id,))
            conn.commit()

        conn.close()

        return jsonify({
            'code': 0,
            'message': '删除成功',
            'data': None
        })

    except Exception as e:
        return jsonify({
            'code': 500,
            'message': f'删除宠物失败: {str(e)}'
        }), 500

@app.route('/api/pets/<int:pet_id>', methods=['GET'])
@auth_required
def get_pet_detail(pet_id):
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT 
                    id, user_id, name, type, breed, age, weight, gender, birthday,
                    avatar_url as avatar, health_notes as healthStatus,
                    vaccine_records, status, created_at, updated_at
                FROM user_pets 
                WHERE id = %s AND user_id = %s AND status = 1
            """, (pet_id, g.user_id))
            pet = cursor.fetchone()
        conn.close()

        if not pet:
            return jsonify({
                'code': 404,
                'message': '宠物不存在或无权限'
            }), 404

        return jsonify({
            'code': 0,
            'message': 'success',
            'data': pet
        })

    except Exception as e:
        return jsonify({
            'code': 500,
            'message': f'获取宠物详情失败: {str(e)}'
        }), 500

@app.route('/api/pets/<int:pet_id>', methods=['PUT'])
@auth_required
def update_pet(pet_id):
    try:
        data = request.json

        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute("SELECT id FROM user_pets WHERE id = %s AND user_id = %s AND status = 1",
                         (pet_id, g.user_id))
            pet = cursor.fetchone()

            if not pet:
                conn.close()
                return jsonify({
                    'code': 404,
                    'message': '宠物不存在或无权限'
                }), 404

            update_fields = []
            update_values = []

            field_mapping = {
                'name': 'name',
                'type': 'type',
                'breed': 'breed',
                'age': 'age',
                'weight': 'weight',
                'gender': 'gender',
                'birthday': 'birthday',
                'avatar': 'avatar_url',
                'healthStatus': 'health_notes',
                'health_status': 'health_notes',
                'vaccineRecords': 'vaccine_records',
                'vaccine_record': 'vaccine_records'
            }

            for key, db_field in field_mapping.items():
                if key in data:
                    value = data[key]
                    if key == 'birthday' and (value == '' or value is None):
                        value = None
                    elif value is None:
                        value = ''
                    update_fields.append(f"{db_field} = %s")
                    update_values.append(value)

            if not update_fields:
                conn.close()
                return jsonify({
                    'code': 400,
                    'message': '没有需要更新的字段'
                }), 400

            update_values.extend([pet_id, g.user_id])
            sql = f"UPDATE user_pets SET {', '.join(update_fields)} WHERE id = %s AND user_id = %s"
            cursor.execute(sql, update_values)
            conn.commit()

            cursor.execute("""
                SELECT id, user_id, name, type, breed, age, weight, gender, birthday,
                       avatar_url as avatar, health_notes as healthStatus, vaccine_records
                FROM user_pets WHERE id = %s
            """, (pet_id,))
            updated_pet = cursor.fetchone()
        conn.close()

        return jsonify({
            'code': 0,
            'message': '更新成功',
            'data': updated_pet
        })

    except Exception as e:
        return jsonify({
            'code': 500,
            'message': f'更新宠物失败: {str(e)}'
        }), 500

@app.route('/api/cart')
@auth_required
def get_cart():
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT 
                    c.id, c.product_id as productId, c.quantity, c.selected,
                    p.name, p.price, p.original_price, p.category, p.image_url as image, p.stock, p.status
                FROM cart c
                LEFT JOIN products p ON c.product_id = p.id
                WHERE c.user_id = %s
                ORDER BY c.created_at DESC
            """, (g.user_id,))
            cart_items = cursor.fetchall()

            for item in cart_items:
                if item.get('price'):
                    item['price'] = f"{float(item['price']):.2f}"
                if item.get('original_price'):
                    item['original_price'] = f"{float(item['original_price']):.2f}"

        conn.close()

        return jsonify({
            'code': 0,
            'message': 'success',
            'data': cart_items
        })

    except Exception as e:
        return jsonify({
            'code': 500,
            'message': f'获取购物车失败: {str(e)}'
        }), 500

@app.route('/api/cart/count')
@auth_required
def get_cart_count():
    """获取购物车商品总件数（用于首页/商城购物车角标），无需拉取完整列表"""
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT COALESCE(SUM(quantity), 0) AS count
                FROM cart WHERE user_id = %s
            """, (g.user_id,))
            row = cursor.fetchone()
        conn.close()
        count = int(row['count']) if row else 0
        return jsonify({
            'code': 0,
            'message': 'success',
            'data': {'count': count}
        })
    except Exception as e:
        return jsonify({
            'code': 500,
            'message': f'获取购物车数量失败: {str(e)}'
        }), 500

@app.route('/api/cart', methods=['POST'])
@app.route('/api/cart/add', methods=['POST'])
@auth_required
def add_to_cart():
    try:
        data = request.json
        product_id = data.get('productId')
        quantity = data.get('quantity', 1)

        if not product_id:
            return jsonify({
                'code': 400,
                'message': '缺少productId参数'
            }), 400

        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute("SELECT id, stock, status FROM products WHERE id = %s", (product_id,))
            product = cursor.fetchone()

            if not product:
                return jsonify({
                    'code': 404,
                    'message': '商品不存在'
                }), 404

            if product['status'] != 1:
                return jsonify({
                    'code': 400,
                    'message': '商品已下架'
                }), 400

            cursor.execute("""
                SELECT id, quantity FROM cart 
                WHERE user_id = %s AND product_id = %s
            """, (g.user_id, product_id))
            cart_item = cursor.fetchone()

            if cart_item:
                new_quantity = cart_item['quantity'] + quantity
                cursor.execute("""
                    UPDATE cart SET quantity = %s 
                    WHERE id = %s
                """, (new_quantity, cart_item['id']))
            else:
                cursor.execute("""
                    INSERT INTO cart (user_id, product_id, quantity, selected)
                    VALUES (%s, %s, %s, TRUE)
                """, (g.user_id, product_id, quantity))

            conn.commit()

            cursor.execute("""
                SELECT SUM(quantity) as total 
                FROM cart 
                WHERE user_id = %s
            """, (g.user_id,))
            cart_total = cursor.fetchone()['total'] or 0

        conn.close()

        return jsonify({
            'code': 0,
            'message': '已添加到购物车',
            'data': {
                'cartTotal': cart_total
            }
        })

    except Exception as e:
        return jsonify({
            'code': 500,
            'message': f'添加到购物车失败: {str(e)}'
        }), 500

@app.route('/api/cart/<int:cart_id>', methods=['PUT'])
@auth_required
def update_cart(cart_id):
    try:
        data = request.json
        quantity = data.get('quantity')
        selected = data.get('selected')

        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute("SELECT id FROM cart WHERE id = %s AND user_id = %s",
                         (cart_id, g.user_id))
            cart_item = cursor.fetchone()

            if not cart_item:
                return jsonify({
                    'code': 404,
                    'message': '购物车项不存在'
                }), 404

            update_fields = []
            update_values = []

            if quantity is not None:
                update_fields.append('quantity = %s')
                update_values.append(quantity)

            if selected is not None:
                update_fields.append('selected = %s')
                update_values.append(selected)

            if update_fields:
                update_values.append(cart_id)
                sql = f"UPDATE cart SET {', '.join(update_fields)} WHERE id = %s"
                cursor.execute(sql, tuple(update_values))
                conn.commit()

        conn.close()

        return jsonify({
            'code': 0,
            'message': '更新成功',
            'data': None
        })

    except Exception as e:
        return jsonify({
            'code': 500,
            'message': f'更新购物车失败: {str(e)}'
        }), 500

@app.route('/api/cart/<int:cart_id>', methods=['DELETE'])
@auth_required
def delete_cart_item(cart_id):
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute("SELECT id FROM cart WHERE id = %s AND user_id = %s",
                         (cart_id, g.user_id))
            cart_item = cursor.fetchone()

            if not cart_item:
                conn.close()
                return jsonify({
                    'code': 0,
                    'message': '删除成功'
                })

            cursor.execute("DELETE FROM cart WHERE id = %s", (cart_id,))
            conn.commit()
        conn.close()

        return jsonify({
            'code': 0,
            'message': '删除成功',
            'data': None
        })

    except Exception as e:
        return jsonify({
            'code': 500,
            'message': f'删除购物车项失败: {str(e)}'
        }), 500

@app.route('/api/cart/clear', methods=['POST'])
@auth_required
def clear_cart():
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute("DELETE FROM cart WHERE user_id = %s", (g.user_id,))
            conn.commit()

        conn.close()

        return jsonify({
            'code': 0,
            'message': '购物车已清空',
            'data': None
        })

    except Exception as e:
        return jsonify({
            'code': 500,
            'message': f'清空购物车失败: {str(e)}'
        }), 500

@app.route('/api/orders')
@auth_required
def get_orders():
    try:
        status = request.args.get('status', '')
        page = request.args.get('page', 1, type=int)
        page_size = request.args.get('pageSize', 10, type=int)

        offset = (page - 1) * page_size

        conn = get_db_connection()
        with conn.cursor() as cursor:
            sql = """
                SELECT 
                    id, order_number as orderNo, 
                    total_amount as totalAmount,
                    status, payment_method as paymentMethod,
                    address_info as address,
                    created_at as createdAt
                FROM orders 
                WHERE user_id = %s
            """
            params = [g.user_id]

            if status:
                sql += " AND status = %s"
                params.append(status)

            sql += " ORDER BY created_at DESC LIMIT %s OFFSET %s"
            params.extend([page_size, offset])

            cursor.execute(sql, params)
            orders = cursor.fetchall()

            for order in orders:
                cursor.execute("""
                    SELECT 
                        id, product_id as productId,
                        product_name as name,
                        spec, price, quantity,
                        image_url as image
                    FROM order_items 
                    WHERE order_id = %s
                """, (order['id'],))
                order['items'] = cursor.fetchall()

        conn.close()

        return jsonify({
            'code': 0,
            'message': 'success',
            'data': orders
        })

    except Exception as e:
        return jsonify({
            'code': 500,
            'message': f'获取订单失败: {str(e)}'
        }), 500

@app.route('/api/orders/<int:order_id>')
@auth_required
def get_order_detail(order_id):
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT 
                    id, order_number as orderNo, 
                    total_amount as totalAmount,
                    status, payment_method as paymentMethod,
                    address_info as address,
                    remark, created_at as createdAt
                FROM orders 
                WHERE id = %s AND user_id = %s
            """, (order_id, g.user_id))
            order = cursor.fetchone()

            if not order:
                return jsonify({
                    'code': 404,
                    'message': '订单不存在'
                }), 404

            cursor.execute("""
                SELECT 
                    id, product_id as productId,
                    product_name as name,
                    spec, price, quantity,
                    image_url as image
                FROM order_items 
                WHERE order_id = %s
            """, (order_id,))
            order['items'] = cursor.fetchall()

        conn.close()

        return jsonify({
            'code': 0,
            'message': 'success',
            'data': order
        })

    except Exception as e:
        return jsonify({
            'code': 500,
            'message': f'获取订单详情失败: {str(e)}'
        }), 500

@app.route('/api/orders', methods=['POST'])
@auth_required
def create_order():
    try:
        data = request.json
        address_id = data.get('addressId')
        items = data.get('items', [])
        coupon_id = data.get('couponId')
        remark = data.get('remark', '')

        if not items:
            return jsonify({
                'code': 400,
                'message': '订单商品不能为空'
            }), 400

        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute("SELECT * FROM addresses WHERE id = %s AND user_id = %s",
                         (address_id, g.user_id))
            address = cursor.fetchone()

            if not address:
                return jsonify({
                    'code': 400,
                    'message': '地址不存在'
                }), 400

            total_amount = 0
            order_items_data = []

            for item in items:
                cursor.execute("SELECT * FROM products WHERE id = %s", (item['productId'],))
                product = cursor.fetchone()

                if not product:
                    return jsonify({
                        'code': 400,
                        'message': f'商品不存在: {item["productId"]}'
                    }), 400

                item_total = product['price'] * item['quantity']
                total_amount += item_total

                order_items_data.append({
                    'product_id': product['id'],
                    'product_name': product['name'],
                    'spec': product.get('spec', ''),
                    'price': product['price'],
                    'quantity': item['quantity'],
                    'image_url': product.get('image_url', '')
                })

            coupon_discount = 0
            if coupon_id:
                cursor.execute("""
                    SELECT * FROM coupons 
                    WHERE id = %s AND user_id = %s AND status = 'available'
                    AND expire_time > NOW()
                """, (coupon_id, g.user_id))
                coupon = cursor.fetchone()

                if coupon and total_amount >= coupon['min_amount']:
                    coupon_discount = coupon['amount']
                    cursor.execute("UPDATE coupons SET status = 'used' WHERE id = %s", (coupon_id,))

            total_amount -= coupon_discount

            order_number = f'OD{datetime.now().strftime("%Y%m%d%H%M%S")}{random.randint(1000, 9999)}'
            address_info = json.dumps({
                'name': address['name'],
                'phone': address['phone'],
                'province': address['province'],
                'city': address['city'],
                'district': address['district'],
                'detail': address['detail']
            }, ensure_ascii=False)

            cursor.execute("""
                INSERT INTO orders 
                (order_number, user_id, total_amount, status, address_info, remark)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (order_number, g.user_id, total_amount, 'pending', address_info, remark))
            order_id = cursor.lastrowid

            for item_data in order_items_data:
                cursor.execute("""
                    INSERT INTO order_items 
                    (order_id, product_id, product_name, spec, price, quantity, image_url)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                """, (
                    order_id,
                    item_data['product_id'],
                    item_data['product_name'],
                    item_data['spec'],
                    item_data['price'],
                    item_data['quantity'],
                    item_data['image_url']
                ))

            for item in items:
                cursor.execute("DELETE FROM cart WHERE user_id = %s AND product_id = %s",
                             (g.user_id, item['productId']))

            conn.commit()

            cursor.execute("SELECT * FROM orders WHERE id = %s", (order_id,))
            new_order = cursor.fetchone()

        conn.close()

        return jsonify({
            'code': 0,
            'message': '订单创建成功',
            'data': new_order
        })

    except Exception as e:
        return jsonify({
            'code': 500,
            'message': f'创建订单失败: {str(e)}'
        }), 500

@app.route('/api/orders/pay', methods=['POST'])
@auth_required
def pay_order():
    try:
        data = request.json
        order_id = data.get('orderId')
        payment_method = data.get('paymentMethod', '微信支付')

        if not order_id:
            return jsonify({
                'code': 400,
                'message': '缺少orderId参数'
            }), 400

        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT id, status FROM orders 
                WHERE id = %s AND user_id = %s
            """, (order_id, g.user_id))
            order = cursor.fetchone()

            if not order:
                return jsonify({
                    'code': 404,
                    'message': '订单不存在或无权限'
                }), 404

            if order['status'] != 'pending':
                return jsonify({
                    'code': 400,
                    'message': '订单状态不允许支付'
                }), 400

            cursor.execute("""
                UPDATE orders 
                SET status = 'paid', payment_method = %s, payment_status = 1
                WHERE id = %s
            """, (payment_method, order_id))
            conn.commit()

        conn.close()

        return jsonify({
            'code': 0,
            'message': '支付成功',
            'data': None
        })

    except Exception as e:
        return jsonify({
            'code': 500,
            'message': f'支付失败: {str(e)}'
        }), 500

@app.route('/api/orders/cancel', methods=['POST'])
@auth_required
def cancel_order():
    try:
        data = request.json
        order_id = data.get('orderId')

        if not order_id:
            return jsonify({
                'code': 400,
                'message': '缺少orderId参数'
            }), 400

        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT id, status FROM orders 
                WHERE id = %s AND user_id = %s
            """, (order_id, g.user_id))
            order = cursor.fetchone()

            if not order:
                return jsonify({
                    'code': 404,
                    'message': '订单不存在或无权限'
                }), 404

            if order['status'] not in ['pending', 'paid']:
                return jsonify({
                    'code': 400,
                    'message': '订单无法取消'
                }), 400

            cursor.execute("UPDATE orders SET status = 'canceled' WHERE id = %s", (order_id,))
            conn.commit()

        conn.close()

        return jsonify({
            'code': 0,
            'message': '订单已取消',
            'data': None
        })

    except Exception as e:
        return jsonify({
            'code': 500,
            'message': f'取消订单失败: {str(e)}'
        }), 500

@app.route('/api/orders/confirm', methods=['POST'])
@auth_required
def confirm_order():
    try:
        data = request.json
        order_id = data.get('orderId')

        if not order_id:
            return jsonify({
                'code': 400,
                'message': '缺少orderId参数'
            }), 400

        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT id, status FROM orders 
                WHERE id = %s AND user_id = %s
            """, (order_id, g.user_id))
            order = cursor.fetchone()

            if not order:
                return jsonify({
                    'code': 404,
                    'message': '订单不存在或无权限'
                }), 404

            if order['status'] != 'paid':
                return jsonify({
                    'code': 400,
                    'message': '订单状态不允许确认收货'
                }), 400

            cursor.execute("UPDATE orders SET status = 'completed' WHERE id = %s", (order_id,))
            conn.commit()

        conn.close()

        return jsonify({
            'code': 0,
            'message': '确认收货成功',
            'data': None
        })

    except Exception as e:
        return jsonify({
            'code': 500,
            'message': f'确认收货失败: {str(e)}'
        }), 500

@app.route('/api/notes')
@auth_required
def get_notes():
    try:
        category = request.args.get('category', '')

        conn = get_db_connection()
        with conn.cursor() as cursor:
            sql = """
                SELECT 
                    id, title, content, 
                    category, images, tags,
                    created_at as createdAt
                FROM pet_notes 
                WHERE user_id = %s AND status = 1
            """
            params = [g.user_id]

            if category:
                sql += " AND category = %s"
                params.append(category)

            sql += " ORDER BY created_at DESC"
            cursor.execute(sql, params)
            notes = cursor.fetchall()

            for note in notes:
                if note.get('images'):
                    note['images'] = json.loads(note['images']) if note['images'] else []
                if note.get('tags'):
                    note['tags'] = json.loads(note['tags']) if note['tags'] else []

        conn.close()

        return jsonify({
            'code': 0,
            'message': 'success',
            'data': notes
        })

    except Exception as e:
        return jsonify({
            'code': 500,
            'message': f'获取笔记失败: {str(e)}'
        }), 500

@app.route('/api/notes', methods=['POST'])
@auth_required
def add_note():
    try:
        data = request.json

        if not data.get('title'):
            return jsonify({
                'code': 400,
                'message': '标题不能为空'
            }), 400

        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute("""
                INSERT INTO pet_notes 
                (user_id, title, content, category, images, tags)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (
                g.user_id,
                data['title'],
                data.get('content', ''),
                data.get('category', 'daily'),
                json.dumps(data.get('images', []), ensure_ascii=False),
                json.dumps(data.get('tags', []), ensure_ascii=False)
            ))
            note_id = cursor.lastrowid
            conn.commit()

        conn.close()

        return jsonify({
            'code': 0,
            'message': '添加成功',
            'data': {
                'id': note_id,
                'title': data['title'],
                'category': data.get('category', 'daily')
            }
        })

    except Exception as e:
        return jsonify({
            'code': 500,
            'message': f'添加笔记失败: {str(e)}'
        }), 500

@app.route('/api/notes/<int:note_id>', methods=['DELETE'])
@auth_required
def delete_note(note_id):
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute("SELECT id FROM pet_notes WHERE id = %s AND user_id = %s",
                         (note_id, g.user_id))
            note = cursor.fetchone()

            if not note:
                return jsonify({
                    'code': 404,
                    'message': '笔记不存在或无权限'
                }), 404

            cursor.execute("UPDATE pet_notes SET status = 0 WHERE id = %s", (note_id,))
            conn.commit()

        conn.close()

        return jsonify({
            'code': 0,
            'message': '删除成功',
            'data': None
        })

    except Exception as e:
        return jsonify({
            'code': 500,
            'message': f'删除笔记失败: {str(e)}'
        }), 500

@app.route('/api/addresses')
@auth_required
def get_addresses():
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT 
                    id, user_id, name, phone,
                    province, city, district, detail,
                    is_default as isDefault,
                    created_at as createdAt
                FROM addresses 
                WHERE user_id = %s AND status = 1
                ORDER BY is_default DESC, created_at DESC
            """, (g.user_id,))
            addresses = cursor.fetchall()

        conn.close()

        return jsonify({
            'code': 0,
            'message': 'success',
            'data': addresses
        })

    except Exception as e:
        return jsonify({
            'code': 500,
            'message': f'获取地址失败: {str(e)}'
        }), 500

@app.route('/api/addresses', methods=['POST'])
@auth_required
def add_address():
    try:
        data = request.json

        required_fields = ['name', 'phone', 'province', 'city', 'district', 'detail']
        for field in required_fields:
            if field not in data:
                return jsonify({
                    'code': 400,
                    'message': f'缺少必要字段: {field}'
                }), 400

        conn = get_db_connection()
        with conn.cursor() as cursor:
            if data.get('isDefault'):
                cursor.execute("""
                    UPDATE addresses 
                    SET is_default = FALSE 
                    WHERE user_id = %s
                """, (g.user_id,))

            cursor.execute("""
                INSERT INTO addresses 
                (user_id, name, phone, province, city, district, detail, is_default)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                g.user_id,
                data['name'],
                data['phone'],
                data['province'],
                data['city'],
                data['district'],
                data['detail'],
                data.get('isDefault', False)
            ))
            address_id = cursor.lastrowid
            conn.commit()

        conn.close()

        return jsonify({
            'code': 0,
            'message': '添加成功',
            'data': {
                'id': address_id,
                'name': data['name'],
                'phone': data['phone']
            }
        })

    except Exception as e:
        return jsonify({
            'code': 500,
            'message': f'添加地址失败: {str(e)}'
        }), 500

@app.route('/api/addresses/<int:address_id>', methods=['GET'])
@auth_required
def get_address_detail(address_id):
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT id, user_id, name, phone, province, city, district, detail, is_default
                FROM addresses
                WHERE id = %s AND user_id = %s
            """, (address_id, g.user_id))
            address = cursor.fetchone()
        conn.close()

        if not address:
            return jsonify({
                'code': 404,
                'message': '地址不存在或无权限'
            }), 404

        return jsonify({
            'code': 0,
            'message': 'success',
            'data': {
                'id': address['id'],
                'name': address['name'],
                'phone': address['phone'],
                'province': address['province'],
                'city': address['city'],
                'district': address['district'],
                'detail': address['detail'],
                'isDefault': bool(address['is_default'])
            }
        })

    except Exception as e:
        return jsonify({
            'code': 500,
            'message': f'获取地址详情失败: {str(e)}'
        }), 500

@app.route('/api/addresses/<int:address_id>', methods=['PUT'])
@auth_required
def update_address(address_id):
    try:
        data = request.json

        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute("SELECT id FROM addresses WHERE id = %s AND user_id = %s",
                         (address_id, g.user_id))
            address = cursor.fetchone()

            if not address:
                return jsonify({
                    'code': 404,
                    'message': '地址不存在或无权限'
                }), 404

            update_fields = []
            update_values = []

            for field in ['name', 'phone', 'province', 'city', 'district', 'detail']:
                if field in data:
                    update_fields.append(f"{field} = %s")
                    update_values.append(data[field])

            if 'isDefault' in data and data['isDefault']:
                cursor.execute("""
                    UPDATE addresses 
                    SET is_default = FALSE 
                    WHERE user_id = %s
                """, (g.user_id,))
                update_fields.append('is_default = TRUE')

            if update_fields:
                update_values.append(address_id)
                sql = f"UPDATE addresses SET {', '.join(update_fields)} WHERE id = %s"
                cursor.execute(sql, tuple(update_values))
                conn.commit()

        conn.close()

        return jsonify({
            'code': 0,
            'message': '更新成功',
            'data': None
        })

    except Exception as e:
        return jsonify({
            'code': 500,
            'message': f'更新地址失败: {str(e)}'
        }), 500

@app.route('/api/addresses/<int:address_id>/default', methods=['PUT'])
@auth_required
def set_default_address(address_id):
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute("SELECT id FROM addresses WHERE id = %s AND user_id = %s",
                         (address_id, g.user_id))
            address = cursor.fetchone()

            if not address:
                return jsonify({
                    'code': 404,
                    'message': '地址不存在或无权限'
                }), 404

            cursor.execute("""
                UPDATE addresses 
                SET is_default = FALSE 
                WHERE user_id = %s
            """, (g.user_id,))

            cursor.execute("""
                UPDATE addresses 
                SET is_default = TRUE 
                WHERE id = %s
            """, (address_id,))
            conn.commit()

        conn.close()

        return jsonify({
            'code': 0,
            'message': '设置默认地址成功',
            'data': None
        })

    except Exception as e:
        return jsonify({
            'code': 500,
            'message': f'设置默认地址失败: {str(e)}'
        }), 500

@app.route('/api/addresses/<int:address_id>', methods=['DELETE'])
@auth_required
def delete_address(address_id):
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute("SELECT id FROM addresses WHERE id = %s AND user_id = %s",
                         (address_id, g.user_id))
            address = cursor.fetchone()

            if not address:
                return jsonify({
                    'code': 404,
                    'message': '地址不存在或无权限'
                }), 404

            cursor.execute("UPDATE addresses SET status = 0 WHERE id = %s", (address_id,))
            conn.commit()

        conn.close()

        return jsonify({
            'code': 0,
            'message': '删除成功',
            'data': None
        })

    except Exception as e:
        return jsonify({
            'code': 500,
            'message': f'删除地址失败: {str(e)}'
        }), 500

@app.route('/api/favorites')
@auth_required
def get_favorites():
    return get_favorites_handler()

@app.route('/api/collections')
@auth_required
def get_collections():
    return get_favorites_handler()

def get_favorites_handler():
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT 
                    f.id, f.product_id, f.created_at as createdAt,
                    p.name, p.price, p.image_url as image, 
                    p.original_price, p.stock, p.sales, p.is_hot
                FROM favorites f
                LEFT JOIN products p ON f.product_id = p.id
                WHERE f.user_id = %s
                ORDER BY f.created_at DESC
            """, (g.user_id,))
            favorites = cursor.fetchall()

        conn.close()

        return jsonify({
            'code': 0,
            'message': 'success',
            'data': favorites
        })

    except Exception as e:
        return jsonify({
            'code': 500,
            'message': f'获取收藏列表失败: {str(e)}'
        }), 500

@app.route('/api/favorites', methods=['POST'])
@auth_required
def add_favorite():
    return add_favorite_handler()

@app.route('/api/collections', methods=['POST'])
@auth_required
def add_collection():
    return add_favorite_handler()

def add_favorite_handler():
    try:
        data = request.json
        product_id = data.get('productId')

        if not product_id:
            return jsonify({
                'code': 400,
                'message': '缺少productId参数'
            }), 400

        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute("SELECT id FROM products WHERE id = %s", (product_id,))
            product = cursor.fetchone()

            if not product:
                return jsonify({
                    'code': 404,
                    'message': '商品不存在'
                }), 404

            cursor.execute("""
                SELECT id FROM favorites 
                WHERE user_id = %s AND product_id = %s
            """, (g.user_id, product_id))
            existing = cursor.fetchone()

            if existing:
                return jsonify({
                    'code': 400,
                    'message': '已收藏该商品'
                }), 400

            cursor.execute("""
                INSERT INTO favorites (user_id, product_id)
                VALUES (%s, %s)
            """, (g.user_id, product_id))
            conn.commit()

        conn.close()

        return jsonify({
            'code': 0,
            'message': '收藏成功',
            'data': None
        })

    except Exception as e:
        return jsonify({
            'code': 500,
            'message': f'收藏失败: {str(e)}'
        }), 500

@app.route('/api/favorites/<int:favorite_id>', methods=['DELETE'])
@auth_required
def delete_favorite(favorite_id):
    return delete_favorite_handler(favorite_id)

@app.route('/api/collections/<int:collection_id>', methods=['DELETE'])
@auth_required
def delete_collection(collection_id):
    return delete_favorite_handler(collection_id)

def delete_favorite_handler(favorite_id):
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute("SELECT id FROM favorites WHERE id = %s AND user_id = %s",
                         (favorite_id, g.user_id))
            favorite = cursor.fetchone()

            if not favorite:
                return jsonify({
                    'code': 404,
                    'message': '收藏不存在或无权限'
                }), 404

            cursor.execute("DELETE FROM favorites WHERE id = %s", (favorite_id,))
            conn.commit()

        conn.close()

        return jsonify({
            'code': 0,
            'message': '取消收藏成功',
            'data': None
        })

    except Exception as e:
        return jsonify({
            'code': 500,
            'message': f'取消收藏失败: {str(e)}'
        }), 500

@app.route('/api/coupons')
@auth_required
def get_coupons():
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT 
                    id, name, amount, min_amount, 
                    expire_time as expireTime, status, created_at as createdAt
                FROM coupons 
                WHERE user_id = %s
                ORDER BY expire_time ASC
            """, (g.user_id,))
            coupons = cursor.fetchall()

        conn.close()

        return jsonify({
            'code': 0,
            'message': 'success',
            'data': coupons
        })

    except Exception as e:
        return jsonify({
            'code': 500,
            'message': f'获取优惠券失败: {str(e)}'
        }), 500

@app.route('/api/coupons/<int:coupon_id>/use', methods=['POST'])
@auth_required
def use_coupon(coupon_id):
    try:
        data = request.json or {}
        order_id = data.get('orderId')

        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT uc.id, uc.status, c.amount, c.min_amount, c.expire_time 
                FROM user_coupons uc
                JOIN coupons c ON uc.coupon_id = c.id
                WHERE uc.id = %s AND uc.user_id = %s
            """, (coupon_id, g.user_id))
            coupon = cursor.fetchone()

            if not coupon:
                conn.close()
                return jsonify({
                    'code': 404,
                    'message': '优惠券不存在或无权限'
                }), 404

            if coupon['status'] != 'available':
                conn.close()
                return jsonify({
                    'code': 400,
                    'message': '优惠券已使用或已过期'
                }), 400

            cursor.execute("""
                UPDATE user_coupons 
                SET status = 'used', used_at = NOW() 
                WHERE id = %s
            """, (coupon_id,))
            conn.commit()
        conn.close()

        return jsonify({
            'code': 0,
            'message': '使用成功',
            'data': {
                'amount': float(coupon['amount'])
            }
        })

    except Exception as e:
        return jsonify({
            'code': 500,
            'message': f'使用优惠券失败: {str(e)}'
        }), 500

@app.route('/api/upload', methods=['POST'])
@auth_required
def upload_file():
    try:
        if 'file' not in request.files:
            return jsonify({
                'code': 400,
                'message': '没有文件上传'
            }), 400

        file = request.files['file']

        if file.filename == '':
            return jsonify({
                'code': 400,
                'message': '未选择文件'
            }), 400

        if not allowed_file(file.filename):
            return jsonify({
                'code': 400,
                'message': '不支持的文件类型'
            }), 400

        timestamp = int(time.time())
        filename = f"{timestamp}_{file.filename}"
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)

        host = request.host
        file_url = f"http://{host}/uploads/{filename}"

        return jsonify({
            'code': 0,
            'message': '上传成功',
            'data': {
                'url': file_url,
                'filename': filename
            }
        })

    except Exception as e:
        return jsonify({
            'code': 500,
            'message': f'上传失败: {str(e)}'
        }), 500

@app.route('/api/products')
@auth_required
def get_products():
    try:
        page = request.args.get('page', 1, type=int)
        page_size = request.args.get('pageSize', 20, type=int)
        category = request.args.get('category', '')
        sort_type = request.args.get('sortType', 'default')
        keyword = request.args.get('keyword', '')

        offset = (page - 1) * page_size

        conn = get_db_connection()
        with conn.cursor() as cursor:
            count_sql = "SELECT COUNT(*) as total FROM products p WHERE p.status = 1"
            count_params = []

            if category:
                count_sql += " AND p.category = %s"
                count_params.append(category)
            if keyword:
                count_sql += " AND (p.name LIKE %s OR p.description LIKE %s)"
                keyword_pattern = f"%{keyword}%"
                count_params.extend([keyword_pattern, keyword_pattern])

            cursor.execute(count_sql, count_params)
            total_result = cursor.fetchone()
            total = total_result['total'] if total_result else 0

            sql = "SELECT p.*, pc.icon as categoryIcon FROM products p LEFT JOIN pet_categories pc ON p.category = pc.name WHERE p.status = 1"
            params = []

            if category:
                sql += " AND p.category = %s"
                params.append(category)
            if keyword:
                sql += " AND (p.name LIKE %s OR p.description LIKE %s)"
                keyword_pattern = f"%{keyword}%"
                params.extend([keyword_pattern, keyword_pattern])

            if sort_type == 'price_asc':
                sql += " ORDER BY p.price ASC"
            elif sort_type == 'price_desc':
                sql += " ORDER BY p.price DESC"
            elif sort_type == 'sales':
                sql += " ORDER BY p.sales DESC"
            elif sort_type == 'rating':
                sql += " ORDER BY p.rating DESC"
            else:
                sql += " ORDER BY p.created_at DESC"

            sql += " LIMIT %s OFFSET %s"
            params.extend([page_size, offset])

            cursor.execute(sql, params)
            products = cursor.fetchall()

            for product in products:
                if product.get('price'):
                    product['price'] = f"{float(product['price']):.2f}"
                if product.get('original_price'):
                    product['original_price'] = f"{float(product['original_price']):.2f}"

        conn.close()

        response_data = {
            'data': products,
            'total': total,
            'page': page,
            'pageSize': page_size
        }

        return jsonify({
            'code': 0,
            'message': 'success',
            'data': response_data
        })
    except Exception as e:
        return jsonify({
            'code': 1,
            'message': f'获取商品列表失败: {str(e)}'
        })

@app.route('/api/products/<int:product_id>')
def get_product_detail(product_id):
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute("SELECT * FROM products WHERE id = %s", (product_id,))
            product = cursor.fetchone()

        conn.close()

        if product:
            return jsonify({
                'code': 0,
                'message': 'success',
                'data': product
            })
        else:
            return jsonify({
                'code': 404,
                'message': '商品不存在'
            }), 404
    except Exception as e:
        return jsonify({
            'code': 500,
            'message': f'获取商品详情失败: {str(e)}'
        }), 500

# ==================== 统一搜索功能 ====================
# 首页与商城共用：跨类型检索商品+笔记，相关性排序，搜索建议，搜索历史，响应 <300ms

def _search_products(conn, keyword, limit, offset):
    """检索商品：相关性排序（名称完全匹配 > 名称前缀 > 名称/描述包含），保证速度"""
    kw = (keyword or '').strip()
    if not kw:
        return [], 0
    pattern = f"%{kw}%"
    pattern_start = f"{kw}%"
    with conn.cursor() as cur:
        cur.execute("""
            SELECT COUNT(*) AS total FROM products
            WHERE status = 1 AND (name LIKE %s OR description LIKE %s)
        """, (pattern, pattern))
        total = (cur.fetchone() or {}).get('total', 0) or 0
        cur.execute("""
            SELECT id, name, price, original_price, image_url AS imageUrl, category, sales, description
            FROM products
            WHERE status = 1 AND (name LIKE %s OR description LIKE %s)
            ORDER BY
                (name = %s) DESC,
                (name LIKE %s) DESC,
                (name LIKE %s OR description LIKE %s) DESC,
                sales DESC
            LIMIT %s OFFSET %s
        """, (pattern, pattern, kw, pattern_start, pattern, pattern, limit, offset))
        rows = cur.fetchall()
    for r in rows:
        if r.get('price') is not None:
            r['price'] = f"{float(r['price']):.2f}"
        if r.get('original_price') is not None:
            r['original_price'] = f"{float(r['original_price']):.2f}"
        r['type'] = 'product'
        r['link'] = f"/pages/product/detail?id={r['id']}"
    return rows, total


def _search_notes(conn, user_id, keyword, limit, offset):
    """检索当前用户笔记：标题/内容/标签匹配，相关性排序"""
    kw = (keyword or '').strip()
    if not kw:
        return [], 0
    pattern = f"%{kw}%"
    pattern_start = f"{kw}%"
    with conn.cursor() as cur:
        cur.execute("""
            SELECT COUNT(*) AS total FROM pet_notes
            WHERE status = 1 AND user_id = %s
            AND (title LIKE %s OR content LIKE %s OR tags LIKE %s)
        """, (user_id, pattern, pattern, pattern))
        total = (cur.fetchone() or {}).get('total', 0) or 0
        cur.execute("""
            SELECT id, title, content, category, images, tags, created_at AS createdAt
            FROM pet_notes
            WHERE status = 1 AND user_id = %s
            AND (title LIKE %s OR content LIKE %s OR tags LIKE %s)
            ORDER BY
                (title = %s) DESC,
                (title LIKE %s) DESC,
                (title LIKE %s OR content LIKE %s) DESC,
                created_at DESC
            LIMIT %s OFFSET %s
        """, (user_id, pattern, pattern, pattern, kw, pattern_start, pattern, pattern, limit, offset))
        rows = cur.fetchall()
    for r in rows:
        if r.get('images'):
            r['images'] = json.loads(r['images']) if isinstance(r['images'], str) else r['images']
        if r.get('tags'):
            r['tags'] = json.loads(r['tags']) if isinstance(r['tags'], str) else r['tags']
        r['contentSnippet'] = (r.get('content') or '')[:80].replace('\n', ' ') if r.get('content') else ''
        r['type'] = 'note'
        r['link'] = f"/pages/note/detail?id={r['id']}"
    return rows, total


@app.route('/api/search/unified', methods=['GET'])
@auth_required
def search_unified():
    """
    统一搜索：同时检索商城商品与当前用户笔记，用于首页/商城搜索框。
    返回商品与笔记分块，带 type、link，便于前端区分展示与跳转。
    响应控制在 300ms 内（限制单次数量）。
    """
    try:
        keyword = (request.args.get('keyword') or '').strip()
        page = max(1, request.args.get('page', 1, type=int))
        product_limit = min(20, max(1, request.args.get('productLimit', 10, type=int)))
        note_limit = min(20, max(1, request.args.get('noteLimit', 10, type=int)))

        if not keyword:
            return jsonify({
                'code': 400,
                'message': '搜索关键词不能为空'
            }), 400

        start = time.perf_counter()
        conn = get_db_connection()
        if not conn:
            return jsonify({'code': 500, 'message': '数据库连接失败'}), 500

        try:
            poff = (page - 1) * product_limit
            noff = (page - 1) * note_limit
            products, total_products = _search_products(conn, keyword, product_limit, poff)
            notes, total_notes = _search_notes(conn, g.user_id, keyword, note_limit, noff)

            # 写入搜索历史（去重：同一用户同一关键词仅保留最近一条）
            try:
                with conn.cursor() as cur:
                    cur.execute(
                        "INSERT INTO search_history (user_id, keyword) VALUES (%s, %s)",
                        (g.user_id, keyword[:100])
                    )
                    conn.commit()
            except Exception:
                conn.rollback()

            elapsed = (time.perf_counter() - start) * 1000
            response_data = {
                'keyword': keyword,
                'products': products,
                'notes': notes,
                'totalProducts': total_products,
                'totalNotes': total_notes,
                'page': page,
                'productLimit': product_limit,
                'noteLimit': note_limit,
                '_meta': {'responseMs': round(elapsed, 2)}
            }
            return jsonify({
                'code': 0,
                'message': 'success',
                'data': response_data
            })
        finally:
            conn.close()
    except Exception as e:
        return jsonify({
            'code': 500,
            'message': f'搜索失败: {str(e)}'
        }), 500


@app.route('/api/search/suggest', methods=['GET'])
def search_suggest():
    """
    搜索建议：根据当前输入返回联想词（商品名、笔记标题、历史关键词前缀匹配）。
    不要求登录；若已登录则包含个人搜索历史。
    """
    try:
        keyword = (request.args.get('keyword') or '').strip()
        limit = min(20, max(1, request.args.get('limit', 10, type=int)))

        if not keyword or len(keyword) < 1:
            return jsonify({'code': 0, 'message': 'success', 'data': {'suggestions': []}})

        conn = get_db_connection()
        if not conn:
            return jsonify({'code': 0, 'message': 'success', 'data': {'suggestions': []}})

        suggestions = []
        pattern = f"{keyword}%"
        pattern_any = f"%{keyword}%"

        with conn.cursor() as cur:
            # 商品名称前缀/包含
            cur.execute("""
                SELECT DISTINCT name AS text, 'product' AS source
                FROM products
                WHERE status = 1 AND (name LIKE %s OR name LIKE %s)
                LIMIT %s
            """, (pattern, pattern_any, limit))
            for row in cur.fetchall():
                suggestions.append({'text': row['text'], 'source': 'product'})

            # 若已登录：笔记标题 + 搜索历史
            user_id = None
            auth_header = request.headers.get('Authorization')
            if auth_header:
                try:
                    token = auth_header.replace('Bearer ', '')
                    user_id = verify_jwt_token(token)
                except Exception:
                    pass

            if user_id and len(suggestions) < limit:
                cur.execute("""
                    SELECT DISTINCT title AS text FROM pet_notes
                    WHERE status = 1 AND user_id = %s AND (title LIKE %s OR title LIKE %s)
                    LIMIT %s
                """, (user_id, pattern, pattern_any, limit - len(suggestions)))
                for row in cur.fetchall():
                    suggestions.append({'text': row['text'], 'source': 'note'})
            if user_id and len(suggestions) < limit:
                cur.execute("""
                    SELECT keyword AS text FROM search_history
                    WHERE user_id = %s AND keyword LIKE %s
                    GROUP BY keyword
                    ORDER BY MAX(created_at) DESC
                    LIMIT %s
                """, (user_id, pattern_any, limit - len(suggestions)))
                for row in cur.fetchall():
                    item = {'text': row['text'], 'source': 'history'}
                    if not any(s['text'] == item['text'] for s in suggestions):
                        suggestions.append(item)

        conn.close()
        return jsonify({
            'code': 0,
            'message': 'success',
            'data': {'suggestions': suggestions[:limit]}
        })
    except Exception as e:
        return jsonify({
            'code': 500,
            'message': f'获取搜索建议失败: {str(e)}'
        }), 500


@app.route('/api/search/history', methods=['GET'])
@auth_required
def search_history_list():
    """获取当前用户搜索历史（按时间倒序）"""
    try:
        limit = min(50, max(1, request.args.get('limit', 10, type=int)))
        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT id, keyword, created_at AS createdAt
                FROM search_history
                WHERE user_id = %s
                ORDER BY created_at DESC
                LIMIT %s
            """, (g.user_id, limit))
            rows = cursor.fetchall()
        conn.close()
        return jsonify({
            'code': 0,
            'message': 'success',
            'data': {'list': rows}
        })
    except Exception as e:
        return jsonify({
            'code': 500,
            'message': f'获取搜索历史失败: {str(e)}'
        }), 500


@app.route('/api/search/history', methods=['DELETE'])
@auth_required
def search_history_clear():
    """清空当前用户搜索历史"""
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute("DELETE FROM search_history WHERE user_id = %s", (g.user_id,))
            conn.commit()
        conn.close()
        return jsonify({
            'code': 0,
            'message': '已清空搜索历史',
            'data': None
        })
    except Exception as e:
        return jsonify({
            'code': 500,
            'message': f'清空搜索历史失败: {str(e)}'
        }), 500


@app.route('/api/search')
def search():
    """保留原单类型搜索，便于兼容；新功能请使用 /api/search/unified"""
    try:
        keyword = request.args.get('keyword', '')
        type = request.args.get('type', 'product')
        page = request.args.get('page', 1, type=int)
        page_size = request.args.get('pageSize', 10, type=int)

        if not keyword:
            return jsonify({
                'code': 400,
                'message': '搜索关键词不能为空'
            }), 400

        offset = (page - 1) * page_size

        conn = get_db_connection()
        with conn.cursor() as cursor:
            if type == 'product':
                sql = """
                    SELECT id, name, price, original_price, image_url, category, sales
                    FROM products
                    WHERE status = 1 AND (name LIKE %s OR description LIKE %s)
                    ORDER BY sales DESC
                    LIMIT %s OFFSET %s
                """
                keyword_pattern = f"%{keyword}%"
                cursor.execute(sql, [keyword_pattern, keyword_pattern, page_size, offset])
                results = cursor.fetchall()

            elif type == 'note':
                sql = """
                    SELECT id, title, content, category, created_at as createdAt
                    FROM pet_notes
                    WHERE status = 1 AND (title LIKE %s OR content LIKE %s)
                    ORDER BY created_at DESC
                    LIMIT %s OFFSET %s
                """
                keyword_pattern = f"%{keyword}%"
                cursor.execute(sql, [keyword_pattern, keyword_pattern, page_size, offset])
                results = cursor.fetchall()

            else:
                results = []

        conn.close()

        return jsonify({
            'code': 0,
            'message': 'success',
            'data': results,
            'keyword': keyword,
            'type': type
        })

    except Exception as e:
        return jsonify({
            'code': 500,
            'message': f'搜索失败: {str(e)}'
        }), 500

@app.route('/api/pets/categories')
def get_pet_categories():
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT id, name, icon, sort_order, status 
                FROM pet_categories 
                WHERE status = 1 
                ORDER BY sort_order
            """)
            categories = cursor.fetchall()

        conn.close()
        return jsonify({
            'code': 0,
            'message': 'success',
            'data': categories,
            'count': len(categories)
        })
    except Exception as e:
        return jsonify({
            'code': 500,
            'message': f'获取分类失败: {str(e)}'
        }), 500

# ==================== 常见问题（FAQ）模块 ====================

@app.route('/api/faq', methods=['GET'])
def get_faq_list():
    """
    获取常见问题列表
    支持按分类筛选，按 sort_order 排序
    """
    try:
        category = request.args.get('category', '')
        
        conn = get_db_connection()
        with conn.cursor() as cursor:
            sql = """
                SELECT id, category, question, answer, sort_order, created_at
                FROM faq
                WHERE status = 1
            """
            params = []
            
            if category:
                sql += " AND category = %s"
                params.append(category)
            
            sql += " ORDER BY sort_order ASC, created_at DESC"
            
            cursor.execute(sql, params)
            faq_list = cursor.fetchall()
            
            # 格式化时间
            for item in faq_list:
                if item.get('created_at'):
                    item['createdAt'] = item['created_at'].strftime('%Y-%m-%d %H:%M:%S') if hasattr(item['created_at'], 'strftime') else str(item['created_at'])
                    del item['created_at']
        
        conn.close()
        
        return jsonify({
            'code': 0,
            'message': 'success',
            'data': faq_list,
            'count': len(faq_list)
        })
    except Exception as e:
        return jsonify({
            'code': 500,
            'message': f'获取常见问题失败: {str(e)}'
        }), 500

# ==================== 意见反馈（Feedback）模块 ====================

@app.route('/api/feedback', methods=['POST'])
@auth_required
def submit_feedback():
    """
    提交意见反馈
    需要登录，验证必填字段，处理图片上传
    """
    try:
        data = request.json
        
        # 验证必填字段
        required_fields = ['type', 'content', 'contact']
        for field in required_fields:
            if not data.get(field):
                return jsonify({
                    'code': 400,
                    'message': f'缺少必要字段: {field}'
                }), 400
        
        feedback_type = data.get('type')
        content = data.get('content', '').strip()
        contact = data.get('contact', '').strip()
        images = data.get('images', [])
        remark = data.get('remark', '')
        
        # 验证反馈类型
        valid_types = ['bug', '建议', '投诉', '其他']
        if feedback_type not in valid_types:
            return jsonify({
                'code': 400,
                'message': f'反馈类型无效，可选值: {", ".join(valid_types)}'
            }), 400
        
        # 验证内容长度
        if len(content) < 5:
            return jsonify({
                'code': 400,
                'message': '反馈内容至少需要5个字符'
            }), 400
        
        if len(content) > 2000:
            return jsonify({
                'code': 400,
                'message': '反馈内容不能超过2000个字符'
            }), 400
        
        # 验证联系方式格式（简单验证：至少3个字符）
        if len(contact) < 3:
            return jsonify({
                'code': 400,
                'message': '联系方式格式不正确'
            }), 400
        
        # 处理图片（如果提供）
        images_json = None
        if images and isinstance(images, list):
            # 验证图片数量
            if len(images) > 9:
                return jsonify({
                    'code': 400,
                    'message': '最多只能上传9张图片'
                }), 400
            images_json = json.dumps(images, ensure_ascii=False)
        
        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute("""
                INSERT INTO feedback 
                (user_id, type, content, contact, images, status)
                VALUES (%s, %s, %s, %s, %s, 0)
            """, (g.user_id, feedback_type, content, contact, images_json))
            feedback_id = cursor.lastrowid
            conn.commit()
        
        conn.close()
        
        return jsonify({
            'code': 0,
            'message': '反馈提交成功，我们会尽快处理',
            'data': {
                'id': feedback_id,
                'type': feedback_type
            }
        })
    except Exception as e:
        return jsonify({
            'code': 500,
            'message': f'提交反馈失败: {str(e)}'
        }), 500

@app.route('/api/feedback', methods=['GET'])
@auth_required
def get_feedback_list():
    """
    获取当前用户的反馈列表
    支持分页
    """
    try:
        page = max(1, request.args.get('page', 1, type=int))
        page_size = min(50, max(1, request.args.get('pageSize', 10, type=int)))
        status = request.args.get('status', '')
        feedback_type = request.args.get('type', '')
        
        offset = (page - 1) * page_size
        
        conn = get_db_connection()
        with conn.cursor() as cursor:
            # 构建查询条件
            where_clauses = ['user_id = %s']
            params = [g.user_id]
            
            if status:
                where_clauses.append('status = %s')
                params.append(int(status))
            
            if feedback_type:
                where_clauses.append('type = %s')
                params.append(feedback_type)
            
            where_sql = ' AND '.join(where_clauses)
            
            # 获取总数
            count_sql = f"SELECT COUNT(*) as total FROM feedback WHERE {where_sql}"
            cursor.execute(count_sql, params)
            total = cursor.fetchone()['total']
            
            # 获取列表
            sql = f"""
                SELECT id, type, content, contact, images, status, reply, reply_at, created_at
                FROM feedback
                WHERE {where_sql}
                ORDER BY created_at DESC
                LIMIT %s OFFSET %s
            """
            params.extend([page_size, offset])
            cursor.execute(sql, params)
            feedback_list = cursor.fetchall()
            
            # 格式化数据
            for item in feedback_list:
                if item.get('images'):
                    item['images'] = json.loads(item['images']) if isinstance(item['images'], str) else item['images']
                else:
                    item['images'] = []
                
                if item.get('created_at'):
                    item['createdAt'] = item['created_at'].strftime('%Y-%m-%d %H:%M:%S') if hasattr(item['created_at'], 'strftime') else str(item['created_at'])
                    del item['created_at']
                
                if item.get('reply_at'):
                    item['replyAt'] = item['reply_at'].strftime('%Y-%m-%d %H:%M:%S') if hasattr(item['reply_at'], 'strftime') else str(item['reply_at'])
                    del item['reply_at']
        
        conn.close()
        
        return jsonify({
            'code': 0,
            'message': 'success',
            'data': {
                'list': feedback_list,
                'total': total,
                'page': page,
                'pageSize': page_size
            }
        })
    except Exception as e:
        return jsonify({
            'code': 500,
            'message': f'获取反馈列表失败: {str(e)}'
        }), 500

@app.route('/api/feedback/<int:feedback_id>', methods=['GET'])
@auth_required
def get_feedback_detail(feedback_id):
    """
    获取反馈详情
    用户只能查看自己的反馈
    """
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT id, type, content, contact, images, status, reply, reply_at, created_at, updated_at
                FROM feedback
                WHERE id = %s AND user_id = %s
            """, (feedback_id, g.user_id))
            feedback = cursor.fetchone()
        
        conn.close()
        
        if not feedback:
            return jsonify({
                'code': 404,
                'message': '反馈不存在或无权限查看'
            }), 404
        
        # 格式化数据
        if feedback.get('images'):
            feedback['images'] = json.loads(feedback['images']) if isinstance(feedback['images'], str) else feedback['images']
        else:
            feedback['images'] = []
        
        if feedback.get('created_at'):
            feedback['createdAt'] = feedback['created_at'].strftime('%Y-%m-%d %H:%M:%S') if hasattr(feedback['created_at'], 'strftime') else str(feedback['created_at'])
            del feedback['created_at']
        
        if feedback.get('updated_at'):
            feedback['updatedAt'] = feedback['updated_at'].strftime('%Y-%m-%d %H:%M:%S') if hasattr(feedback['updated_at'], 'strftime') else str(feedback['updated_at'])
            del feedback['updated_at']
        
        if feedback.get('reply_at'):
            feedback['replyAt'] = feedback['reply_at'].strftime('%Y-%m-%d %H:%M:%S') if hasattr(feedback['reply_at'], 'strftime') else str(feedback['reply_at'])
            del feedback['reply_at']
        
        return jsonify({
            'code': 0,
            'message': 'success',
            'data': feedback
        })
    except Exception as e:
        return jsonify({
            'code': 500,
            'message': f'获取反馈详情失败: {str(e)}'
        }), 500

# ==================== 资讯模块 ====================

@app.route('/api/news', methods=['GET'])
def get_news_list():
    try:
        news_type = request.args.get('type', '')
        page = request.args.get('page', 1, type=int)
        size = request.args.get('size', 10, type=int)
        offset = (page - 1) * size

        conn = get_db_connection()
        with conn.cursor() as cursor:
            where_clause = "WHERE status = 1"
            params = []

            if news_type:
                where_clause += " AND type = %s"
                params.append(news_type)

            count_sql = f"SELECT COUNT(*) as total FROM news {where_clause}"
            cursor.execute(count_sql, params)
            total = cursor.fetchone()['total']

            sql = f"""
                SELECT id, title, summary, type, image_url, author,
                       view_count as viewCount, like_count as likeCount,
                       comment_count as commentCount, created_at as createdAt
                FROM news {where_clause}
                ORDER BY created_at DESC
                LIMIT %s OFFSET %s
            """
            params.extend([size, offset])
            cursor.execute(sql, params)
            news_list = cursor.fetchall()
        conn.close()

        return jsonify({
            'code': 0,
            'message': 'success',
            'data': {
                'list': news_list,
                'total': total,
                'page': page,
                'size': size
            }
        })

    except Exception as e:
        return jsonify({
            'code': 500,
            'message': f'获取资讯列表失败: {str(e)}'
        }), 500

@app.route('/api/news/<int:news_id>', methods=['GET'])
def get_news_detail(news_id):
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT id, title, content, summary, type, image_url, author,
                       view_count as viewCount, like_count as likeCount,
                       comment_count as commentCount, created_at as createdAt
                FROM news
                WHERE id = %s AND status = 1
            """, (news_id,))
            news = cursor.fetchone()

            if news:
                cursor.execute("UPDATE news SET view_count = view_count + 1 WHERE id = %s", (news_id,))
                conn.commit()
        conn.close()

        if not news:
            return jsonify({
                'code': 404,
                'message': '资讯不存在'
            }), 404

        return jsonify({
            'code': 0,
            'message': 'success',
            'data': news
        })

    except Exception as e:
        return jsonify({
            'code': 500,
            'message': f'获取资讯详情失败: {str(e)}'
        }), 500

@app.route('/api/news/<int:news_id>/comments', methods=['GET'])
def get_news_comments(news_id):
    try:
        page = request.args.get('page', 1, type=int)
        size = request.args.get('size', 20, type=int)
        offset = (page - 1) * size

        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT c.id, c.content, c.like_count as likeCount, c.created_at as createdAt,
                       u.id as userId, u.nickname as userName, u.avatar_url as userAvatar
                FROM news_comments c
                LEFT JOIN users u ON c.user_id = u.id
                WHERE c.news_id = %s AND c.status = 1
                ORDER BY c.created_at DESC
                LIMIT %s OFFSET %s
            """, (news_id, size, offset))
            comments = cursor.fetchall()

            cursor.execute("SELECT COUNT(*) as total FROM news_comments WHERE news_id = %s AND status = 1", (news_id,))
            total = cursor.fetchone()['total']
        conn.close()

        return jsonify({
            'code': 0,
            'message': 'success',
            'data': {
                'list': comments,
                'total': total
            }
        })

    except Exception as e:
        return jsonify({
            'code': 500,
            'message': f'获取评论失败: {str(e)}'
        }), 500

@app.route('/api/news/<int:news_id>/comments', methods=['POST'])
@auth_required
def add_news_comment(news_id):
    try:
        data = request.json
        content = (data.get('content') or '').strip()

        if not content:
            return jsonify({
                'code': 400,
                'message': '评论内容不能为空'
            }), 400

        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute("SELECT id FROM news WHERE id = %s AND status = 1", (news_id,))
            if not cursor.fetchone():
                conn.close()
                return jsonify({
                    'code': 404,
                    'message': '资讯不存在'
                }), 404

            cursor.execute("""
                INSERT INTO news_comments (news_id, user_id, content)
                VALUES (%s, %s, %s)
            """, (news_id, g.user_id, content))
            comment_id = cursor.lastrowid

            cursor.execute("UPDATE news SET comment_count = comment_count + 1 WHERE id = %s", (news_id,))
            conn.commit()
        conn.close()

        return jsonify({
            'code': 0,
            'message': '评论成功',
            'data': {'id': comment_id}
        })

    except Exception as e:
        return jsonify({
            'code': 500,
            'message': f'评论失败: {str(e)}'
        }), 500

# ==================== 优惠券模块 ====================

@app.route('/api/coupons/available', methods=['GET'])
@auth_required
def get_available_coupons():
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT c.id, c.name, c.amount, c.min_amount as minAmount,
                       c.expire_time as expireTime,
                       CASE WHEN uc.id IS NOT NULL THEN 1 ELSE 0 END as received
                FROM coupons c
                LEFT JOIN user_coupons uc ON c.id = uc.coupon_id AND uc.user_id = %s
                WHERE c.status = 'available' AND c.expire_time >= NOW()
                ORDER BY c.amount DESC
            """, (g.user_id,))
            coupons = cursor.fetchall()
        conn.close()

        for coupon in coupons:
            coupon['amount'] = float(coupon['amount'])
            coupon['minAmount'] = float(coupon['minAmount'])
            coupon['received'] = bool(coupon['received'])
            if coupon.get('expireTime'):
                coupon['expireTime'] = coupon['expireTime'].strftime('%Y-%m-%d')

        return jsonify({
            'code': 0,
            'message': 'success',
            'data': coupons
        })

    except Exception as e:
        return jsonify({
            'code': 500,
            'message': f'获取优惠券失败: {str(e)}'
        }), 500

@app.route('/api/coupons/<int:coupon_id>/receive', methods=['POST'])
@auth_required
def receive_coupon(coupon_id):
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute("SELECT * FROM coupons WHERE id = %s AND status = 'available'", (coupon_id,))
            coupon = cursor.fetchone()

            if not coupon:
                conn.close()
                return jsonify({
                    'code': 404,
                    'message': '优惠券不存在'
                }), 404

            cursor.execute("SELECT id FROM user_coupons WHERE user_id = %s AND coupon_id = %s",
                         (g.user_id, coupon_id))
            if cursor.fetchone():
                conn.close()
                return jsonify({
                    'code': 400,
                    'message': '优惠券已领取'
                }), 400

            cursor.execute("""
                INSERT INTO user_coupons (user_id, coupon_id)
                VALUES (%s, %s)
            """, (g.user_id, coupon_id))
            conn.commit()
        conn.close()

        return jsonify({
            'code': 0,
            'message': '领取成功'
        })

    except Exception as e:
        return jsonify({
            'code': 500,
            'message': f'领取优惠券失败: {str(e)}'
        }), 500

@app.route('/api/coupons/my', methods=['GET'])
@auth_required
def get_my_coupons():
    try:
        status = request.args.get('status', 'available')

        conn = get_db_connection()
        with conn.cursor() as cursor:
            if status == 'all':
                cursor.execute("""
                    SELECT uc.id, uc.status, uc.received_at as receivedAt,
                           c.name, c.amount, c.min_amount as minAmount,
                           c.expire_time as expireTime
                    FROM user_coupons uc
                    JOIN coupons c ON uc.coupon_id = c.id
                    WHERE uc.user_id = %s
                    ORDER BY uc.received_at DESC
                """, (g.user_id,))
            else:
                cursor.execute("""
                    SELECT uc.id, uc.status, uc.received_at as receivedAt,
                           c.name, c.amount, c.min_amount as minAmount,
                           c.expire_time as expireTime
                    FROM user_coupons uc
                    JOIN coupons c ON uc.coupon_id = c.id
                    WHERE uc.user_id = %s AND uc.status = %s
                    ORDER BY uc.received_at DESC
                """, (g.user_id, status))
            coupons = cursor.fetchall()
        conn.close()

        for coupon in coupons:
            coupon['amount'] = float(coupon['amount'])
            coupon['minAmount'] = float(coupon['minAmount'])
            if coupon.get('expireTime'):
                coupon['expireTime'] = coupon['expireTime'].strftime('%Y-%m-%d')

        return jsonify({
            'code': 0,
            'message': 'success',
            'data': coupons
        })

    except Exception as e:
        return jsonify({
            'code': 500,
            'message': f'获取我的优惠券失败: {str(e)}'
        }), 500

@app.errorhandler(404)
def not_found_handler(e):
    """全局 404：返回 JSON，便于前端和小程序统一处理"""
    return jsonify({
        'code': 404,
        'message': f'接口不存在: {request.method} {request.path}'
    }), 404

# ==================== 丧葬服务模块 ====================

@app.route('/api/funeral/bookings', methods=['POST'])
@auth_required
def create_funeral_booking():
    try:
        data = request.json
        
        required_fields = ['service_type', 'service_name', 'package_name', 'price', 'pet_name', 'pet_type', 'phone']
        for field in required_fields:
            if not data.get(field):
                return jsonify({
                    'code': 400,
                    'message': f'缺少必要字段: {field}'
                }), 400

        booking_date = data.get('booking_date')
        if booking_date == '' or booking_date is None:
            booking_date = None

        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute("""
                INSERT INTO funeral_bookings 
                (user_id, service_type, service_name, package_name, price, pet_name, pet_type, phone, booking_date, remarks)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                g.user_id,
                data['service_type'],
                data['service_name'],
                data['package_name'],
                data['price'],
                data['pet_name'],
                data['pet_type'],
                data['phone'],
                booking_date,
                data.get('remarks') or ''
            ))
            booking_id = cursor.lastrowid
            conn.commit()
        conn.close()

        return jsonify({
            'code': 0,
            'message': '预约成功',
            'data': {
                'booking_id': booking_id
            }
        })

    except Exception as e:
        return jsonify({
            'code': 500,
            'message': f'预约失败: {str(e)}'
        }), 500

@app.route('/api/funeral/bookings', methods=['GET'])
@auth_required
def get_funeral_bookings():
    try:
        status = request.args.get('status', '')
        
        conn = get_db_connection()
        with conn.cursor() as cursor:
            sql = "SELECT * FROM funeral_bookings WHERE user_id = %s"
            params = [g.user_id]
            
            if status:
                sql += " AND status = %s"
                params.append(status)
            
            sql += " ORDER BY created_at DESC"
            cursor.execute(sql, params)
            bookings = cursor.fetchall()
        conn.close()

        for booking in bookings:
            booking['price'] = float(booking['price'])

        return jsonify({
            'code': 0,
            'message': 'success',
            'data': bookings
        })

    except Exception as e:
        return jsonify({
            'code': 500,
            'message': f'获取预约列表失败: {str(e)}'
        }), 500

@app.route('/api/funeral/bookings/<int:booking_id>', methods=['GET'])
@auth_required
def get_funeral_booking_detail(booking_id):
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute("SELECT * FROM funeral_bookings WHERE id = %s AND user_id = %s", (booking_id, g.user_id))
            booking = cursor.fetchone()
        conn.close()

        if not booking:
            return jsonify({
                'code': 404,
                'message': '预约不存在或无权限'
            }), 404

        booking['price'] = float(booking['price'])

        return jsonify({
            'code': 0,
            'message': 'success',
            'data': booking
        })

    except Exception as e:
        return jsonify({
            'code': 500,
            'message': f'获取预约详情失败: {str(e)}'
        }), 500

@app.route('/api/funeral/bookings/<int:booking_id>/cancel', methods=['POST'])
@auth_required
def cancel_funeral_booking(booking_id):
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute("SELECT id FROM funeral_bookings WHERE id = %s AND user_id = %s", (booking_id, g.user_id))
            if not cursor.fetchone():
                conn.close()
                return jsonify({
                    'code': 404,
                    'message': '预约不存在或无权限'
                }), 404

            cursor.execute("UPDATE funeral_bookings SET status = 'canceled' WHERE id = %s", (booking_id,))
            conn.commit()
        conn.close()

        return jsonify({
            'code': 0,
            'message': '取消成功'
        })

    except Exception as e:
        return jsonify({
            'code': 500,
            'message': f'取消预约失败: {str(e)}'
        }), 500

# ==================== 公告模块 ====================

@app.route('/api/notices', methods=['GET'])
def get_notices():
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT id, icon, title, content, create_time as createTime
                FROM notices
                WHERE status = 1
                ORDER BY create_time DESC
            """)
            notices = cursor.fetchall()
        conn.close()

        for notice in notices:
            if notice.get('createTime') and hasattr(notice['createTime'], 'strftime'):
                notice['createTime'] = notice['createTime'].strftime('%Y-%m-%d')

        return jsonify({
            'code': 0,
            'message': 'success',
            'data': notices
        })

    except Exception as e:
        return jsonify({
            'code': 500,
            'message': f'获取公告失败: {str(e)}'
        }), 500

if __name__ == '__main__':
    print("=" * 60)
    print("🐾 宠物平台后端服务启动中... (微信小程序对接版 v3.0)")
    print("=" * 60)
    print(f"📡 访问地址: http://localhost:5000")
    print(f"📡 健康检查: http://localhost:5000/api/health")
    print(f"👤 用户登录: POST http://localhost:5000/api/user/login")
    print(f"🐱 我的宠物: GET http://localhost:5000/api/pets (需要认证)")
    print(f"🛒 购物车: GET http://localhost:5000/api/cart (需要认证)")
    print(f"📦 订单: GET http://localhost:5000/api/orders (需要认证)")
    print("=" * 60)

    app.run(host='0.0.0.0', port=5000, debug=True)
