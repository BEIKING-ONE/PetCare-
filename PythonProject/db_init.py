"""
宠物平台 - 数据库初始化脚本 (微信小程序对接版)
文件名：db_init.py
"""

import pymysql
import sys
import json

class PetDatabase:
    def __init__(self):
        self.config = {
            'host': 'localhost',
            'port': 3306,
            'user': 'root',
            'password': '123456',
            'database': 'pet_platform',
            'charset': 'utf8mb4'
        }

    def connect(self):
        """连接到数据库"""
        try:
            conn = pymysql.connect(**self.config)
            return conn
        except Exception as e:
            print(f"❌ 数据库连接失败: {e}")
            sys.exit(1)

    def drop_tables(self, cursor):
        """删除现有表"""
        print("🗑️  清理现有表...")
        cursor.execute("SET FOREIGN_KEY_CHECKS = 0")
        tables = [
            'feedback', 'faq', 'search_history', 'coupons', 'vaccines', 'favorites', 'addresses',
            'user_pets', 'pet_notes', 'order_items', 'orders',
            'cart', 'cart_items', 'news', 'products', 'pet_breeds',
            'pet_categories', 'product_categories', 'user_addresses', 'users', 'pets', 'banners'
        ]
        for table in tables:
            try:
                cursor.execute(f"DROP TABLE IF EXISTS {table}")
                print(f"   已删除: {table}")
            except Exception as e:
                print(f"   删除 {table} 失败: {e}")
        cursor.execute("SET FOREIGN_KEY_CHECKS = 1")
        print("✅ 清理完成")

    def create_tables(self):
        """创建所有表"""
        print("\n🚀 创建数据库表...")
        print("=" * 50)

        conn = self.connect()
        cursor = conn.cursor()

        try:
            # 清理旧表
            self.drop_tables(cursor)

            # 1. 用户表（更新）
            print("👤 创建用户表...")
            cursor.execute("""
            CREATE TABLE users (
                id INT AUTO_INCREMENT PRIMARY KEY,
                openid VARCHAR(100) UNIQUE NOT NULL COMMENT '微信openid',
                nickname VARCHAR(50) COMMENT '昵称',
                avatar_url VARCHAR(255) COMMENT '头像URL',
                phone VARCHAR(20) COMMENT '手机号',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间'
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
            """)
            print("   ✅ users表创建成功")

            # 2. 宠物表（更新，与文档一致）
            print("🐕 创建宠物表...")
            cursor.execute("""
            CREATE TABLE user_pets (
                id INT AUTO_INCREMENT PRIMARY KEY,
                user_id INT NOT NULL COMMENT '用户ID',
                name VARCHAR(50) NOT NULL COMMENT '宠物名称',
                type VARCHAR(20) NOT NULL COMMENT '宠物类型：dog/cat/rabbit等',
                breed VARCHAR(50) COMMENT '品种',
                age VARCHAR(20) COMMENT '年龄',
                weight VARCHAR(20) COMMENT '体重',
                gender VARCHAR(10) COMMENT '性别',
                birthday DATE COMMENT '生日',
                avatar_url VARCHAR(255) COMMENT '头像URL',
                health_notes TEXT COMMENT '健康记录',
                vaccine_records TEXT COMMENT '疫苗记录',
                status TINYINT DEFAULT 1 COMMENT '状态：1正常，0删除',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间'
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
            """)
            print("   ✅ user_pets表创建成功")

            # 3. 订单表（更新，与文档一致）
            print("📦 创建订单表...")
            cursor.execute("""
            CREATE TABLE orders (
                id INT AUTO_INCREMENT PRIMARY KEY,
                order_number VARCHAR(50) UNIQUE NOT NULL COMMENT '订单号',
                user_id INT NOT NULL COMMENT '用户ID',
                total_amount DECIMAL(10,2) NOT NULL COMMENT '订单总金额',
                status VARCHAR(20) NOT NULL DEFAULT 'pending' COMMENT '订单状态：pending/paid/shipping/completed/canceled',
                address_info TEXT COMMENT '地址信息',
                payment_method VARCHAR(20) COMMENT '支付方式',
                payment_status TINYINT DEFAULT 0 COMMENT '支付状态',
                shipping_status TINYINT DEFAULT 0 COMMENT '配送状态',
                remark TEXT COMMENT '备注',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间'
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
            """)
            print("   ✅ orders表创建成功")

            # 4. 订单商品表（更新）
            print("🛍️ 创建订单商品表...")
            cursor.execute("""
            CREATE TABLE order_items (
                id INT AUTO_INCREMENT PRIMARY KEY,
                order_id INT NOT NULL COMMENT '订单ID',
                product_id INT NOT NULL COMMENT '商品ID',
                product_name VARCHAR(100) NOT NULL COMMENT '商品名称',
                spec VARCHAR(50) COMMENT '规格',
                price DECIMAL(10,2) NOT NULL COMMENT '单价',
                quantity INT NOT NULL COMMENT '数量',
                image_url VARCHAR(255) COMMENT '商品图片'
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
            """)
            print("   ✅ order_items表创建成功")

            # 5. 笔记表（更新，与文档一致）
            print("📝 创建笔记表...")
            cursor.execute("""
            CREATE TABLE pet_notes (
                id INT AUTO_INCREMENT PRIMARY KEY,
                user_id INT NOT NULL COMMENT '用户ID',
                title VARCHAR(100) NOT NULL COMMENT '标题',
                content TEXT COMMENT '内容',
                category VARCHAR(20) NOT NULL DEFAULT 'daily' COMMENT '分类：medical/food/train/daily/health',
                images TEXT COMMENT '图片列表（JSON格式）',
                tags TEXT COMMENT '标签列表（JSON格式）',
                status TINYINT DEFAULT 1 COMMENT '状态：1正常，0删除',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间'
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
            """)
            print("   ✅ pet_notes表创建成功")

            # 6. 地址表（更新）
            print("📍 创建地址表...")
            cursor.execute("""
            CREATE TABLE addresses (
                id INT AUTO_INCREMENT PRIMARY KEY,
                user_id INT NOT NULL COMMENT '用户ID',
                name VARCHAR(50) NOT NULL COMMENT '收货人姓名',
                phone VARCHAR(20) NOT NULL COMMENT '联系电话',
                province VARCHAR(50) NOT NULL COMMENT '省份',
                city VARCHAR(50) NOT NULL COMMENT '城市',
                district VARCHAR(50) NOT NULL COMMENT '区县',
                detail VARCHAR(255) NOT NULL COMMENT '详细地址',
                is_default BOOLEAN DEFAULT FALSE COMMENT '是否默认地址',
                status TINYINT DEFAULT 1 COMMENT '状态：1正常，0删除',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间'
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
            """)
            print("   ✅ addresses表创建成功")

            # 7. 收藏表（新增）
            print("❤️ 创建收藏表...")
            cursor.execute("""
            CREATE TABLE favorites (
                id INT AUTO_INCREMENT PRIMARY KEY,
                user_id INT NOT NULL COMMENT '用户ID',
                product_id INT NOT NULL COMMENT '商品ID',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '收藏时间'
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
            """)
            print("   ✅ favorites表创建成功")

            # 8. 优惠券表（新增）
            print("🎫 创建优惠券表...")
            cursor.execute("""
            CREATE TABLE coupons (
                id INT AUTO_INCREMENT PRIMARY KEY,
                user_id INT NOT NULL COMMENT '用户ID',
                name VARCHAR(100) NOT NULL COMMENT '优惠券名称',
                amount DECIMAL(10,2) NOT NULL COMMENT '优惠金额',
                min_amount DECIMAL(10,2) NOT NULL COMMENT '最低使用金额',
                expire_time DATETIME NOT NULL COMMENT '过期时间',
                status VARCHAR(20) DEFAULT 'available' COMMENT '状态：available/used/expired',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间'
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
            """)
            print("   ✅ coupons表创建成功")

            # 9. 疫苗提醒表（疫苗记录）
            print("💉 创建疫苗记录表...")
            cursor.execute("""
            CREATE TABLE vaccines (
                id INT AUTO_INCREMENT PRIMARY KEY,
                user_id INT NOT NULL COMMENT '用户ID',
                pet_id INT NOT NULL COMMENT '宠物ID（关联user_pets）',
                pet_name VARCHAR(50) NOT NULL COMMENT '宠物名称',
                pet_type VARCHAR(20) NOT NULL COMMENT '宠物类型：dog/cat等',
                vaccine_name VARCHAR(100) NOT NULL COMMENT '疫苗名称',
                vaccine_date DATE NOT NULL COMMENT '接种日期',
                next_date DATE COMMENT '下次接种日期',
                clinic VARCHAR(200) COMMENT '接种医院',
                notes TEXT COMMENT '备注信息',
                status VARCHAR(20) DEFAULT 'pending' COMMENT '状态：pending=待接种，completed=已接种',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
                INDEX idx_user_id (user_id),
                INDEX idx_pet_id (pet_id),
                INDEX idx_next_date (next_date),
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT '疫苗提醒记录表'
            """)
            print("   ✅ vaccines表创建成功")

            # 10. 原有表保持不变
            print("🐱 创建宠物分类表...")
            cursor.execute("""
            CREATE TABLE pet_categories (
                id INT AUTO_INCREMENT PRIMARY KEY,
                name VARCHAR(50) NOT NULL,
                icon VARCHAR(50),
                sort_order INT DEFAULT 0,
                status TINYINT DEFAULT 1
            )
            """)
            print("   ✅ pet_categories表创建成功")

            print("🛒 创建商品表...")
            cursor.execute("""
            CREATE TABLE products (
                id INT AUTO_INCREMENT PRIMARY KEY,
                name VARCHAR(100) NOT NULL,
                category VARCHAR(50),
                price DECIMAL(10,2) NOT NULL,
                original_price DECIMAL(10,2),
                image_url VARCHAR(255),
                description TEXT,
                stock INT DEFAULT 0,
                sales INT DEFAULT 0,
                rating DECIMAL(3,2) DEFAULT 0.0,
                is_hot BOOLEAN DEFAULT FALSE,
                is_new BOOLEAN DEFAULT FALSE,
                status TINYINT DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """)
            print("   ✅ products表创建成功")

            # 搜索历史表（统一搜索功能）
            print("🔍 创建搜索历史表...")
            cursor.execute("""
            CREATE TABLE search_history (
                id INT AUTO_INCREMENT PRIMARY KEY,
                user_id INT NOT NULL COMMENT '用户ID',
                keyword VARCHAR(100) NOT NULL COMMENT '搜索关键词',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '搜索时间',
                INDEX idx_user_created (user_id, created_at DESC),
                INDEX idx_keyword (keyword(20))
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT '用户搜索历史'
            """)
            print("   ✅ search_history表创建成功")

            # 常见问题表（FAQ）
            print("❓ 创建常见问题表...")
            cursor.execute("""
            CREATE TABLE faq (
                id INT AUTO_INCREMENT PRIMARY KEY,
                category VARCHAR(50) NOT NULL COMMENT '问题分类',
                question VARCHAR(500) NOT NULL COMMENT '问题标题',
                answer TEXT NOT NULL COMMENT '问题答案',
                sort_order INT DEFAULT 0 COMMENT '排序权重',
                status TINYINT DEFAULT 1 COMMENT '状态：1启用，0禁用',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
                INDEX idx_category (category),
                INDEX idx_status (status)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT '常见问题表'
            """)
            print("   ✅ faq表创建成功")

            # 意见反馈表
            print("💬 创建意见反馈表...")
            cursor.execute("""
            CREATE TABLE feedback (
                id INT AUTO_INCREMENT PRIMARY KEY,
                user_id INT NOT NULL COMMENT '用户ID',
                type VARCHAR(50) NOT NULL COMMENT '反馈类型：bug/建议/投诉/其他',
                content TEXT NOT NULL COMMENT '反馈内容',
                contact VARCHAR(100) NOT NULL COMMENT '联系方式',
                images TEXT COMMENT '图片URL数组（JSON格式）',
                status TINYINT DEFAULT 0 COMMENT '处理状态：0待处理，1处理中，2已处理',
                reply TEXT COMMENT '回复内容',
                reply_at TIMESTAMP NULL COMMENT '回复时间',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
                INDEX idx_user_id (user_id),
                INDEX idx_status (status),
                INDEX idx_type (type),
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT '意见反馈表'
            """)
            print("   ✅ feedback表创建成功")

            print("🛍️ 创建购物车表...")
            cursor.execute("""
            CREATE TABLE cart (
                id INT AUTO_INCREMENT PRIMARY KEY,
                user_id INT,
                product_id INT,
                quantity INT DEFAULT 1,
                selected BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """)
            print("   ✅ cart表创建成功")

            conn.commit()
            print("\n" + "=" * 50)
            print("✅ 所有表创建成功！")
            print("=" * 50)

            return True

        except Exception as e:
            print(f"❌ 创建表失败: {e}")
            conn.rollback()
            return False
        finally:
            cursor.close()
            conn.close()

    def insert_sample_data(self):
        """插入示例数据"""
        print("\n📝 插入示例数据...")
        print("=" * 50)

        conn = self.connect()
        cursor = conn.cursor()

        try:
            # 1. 测试用户
            print("👤 插入测试用户...")
            users = [
                ('wx_001', '宠物爱好者小王', 'https://example.com/avatar1.jpg', '13800138001'),
                ('wx_002', '资深铲屎官小李', 'https://example.com/avatar2.jpg', '13800138002')
            ]
            cursor.executemany(
                "INSERT INTO users (openid, nickname, avatar_url, phone) VALUES (%s, %s, %s, %s)",
                users
            )
            print(f"   ✅ 插入 {len(users)} 个用户")

            # 2. 测试宠物
            print("🐕 插入测试宠物...")
            pets = [
                (1, '旺财', 'dog', '金毛', '3岁', '25kg', '公', '2021-01-15', '', '身体健康，活泼好动', '已完成狂犬疫苗、六联疫苗'),
                (1, '咪咪', 'cat', '布偶猫', '2岁', '4kg', '母', '2022-03-20', '', '肠胃敏感，需注意饮食', '已完成猫三联')
            ]
            cursor.executemany(
                "INSERT INTO user_pets (user_id, name, type, breed, age, weight, gender, birthday, avatar_url, health_notes, vaccine_records) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)",
                pets
            )
            print(f"   ✅ 插入 {len(pets)} 只宠物")

            # 3. 测试地址
            print("📍 插入测试地址...")
            addresses = [
                (1, '张三', '13800138001', '北京市', '北京市', '朝阳区', '望京街道101号', 1, 1),
                (1, '李四', '13800138002', '上海市', '上海市', '浦东新区', '陆家嘴街道202号', 0, 1)
            ]
            cursor.executemany(
                "INSERT INTO addresses (user_id, name, phone, province, city, district, detail, is_default, status) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)",
                addresses
            )
            print(f"   ✅ 插入 {len(addresses)} 个地址")

            # 4. 测试笔记
            print("📝 插入测试笔记...")
            notes = [
                (1, '旺财今天去打疫苗', '今天带旺财去宠物医院打了年度加强疫苗，表现很好，没有出现不良反应。',
                 'medical', json.dumps(['https://example.com/vaccine1.jpg']),
                 json.dumps(['疫苗', '健康'])),
                (1, '咪咪的饮食记录', '今天给咪咪换了新的猫粮，添加了益生菌，胃口不错，吃了平时两倍的量。',
                 'food', json.dumps([]),
                 json.dumps(['饮食', '记录']))
            ]
            cursor.executemany(
                "INSERT INTO pet_notes (user_id, title, content, category, images, tags) VALUES (%s, %s, %s, %s, %s, %s)",
                notes
            )
            print(f"   ✅ 插入 {len(notes)} 条笔记")

            # 5. 测试优惠券
            print("🎫 插入测试优惠券...")
            coupons = [
                (1, '新用户专享券', 20.00, 100.00, '2024-12-31 23:59:59', 'available'),
                (1, '满减优惠券', 10.00, 50.00, '2024-06-30 23:59:59', 'available')
            ]
            cursor.executemany(
                "INSERT INTO coupons (user_id, name, amount, min_amount, expire_time, status) VALUES (%s, %s, %s, %s, %s, %s)",
                coupons
            )
            print(f"   ✅ 插入 {len(coupons)} 张优惠券")

            # 6. 测试疫苗记录
            print("💉 插入测试疫苗记录...")
            vaccines = [
                (1, 1, '旺财', 'dog', '狂犬疫苗', '2024-01-15', '2025-01-15', '宠物医院', '', 'completed'),
                (1, 1, '旺财', 'dog', '六联疫苗', '2024-01-20', '2024-04-20', '', '待加强', 'pending')
            ]
            cursor.executemany(
                "INSERT INTO vaccines (user_id, pet_id, pet_name, pet_type, vaccine_name, vaccine_date, next_date, clinic, notes, status) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)",
                vaccines
            )
            print(f"   ✅ 插入 {len(vaccines)} 条疫苗记录")

            # 7. 原有数据保持不变
            print("🐱 插入宠物分类...")
            categories = [
                ('狗狗', '🐶', 1, 1),
                ('猫咪', '🐱', 2, 1),
                ('小宠', '🐰', 3, 1)
            ]
            cursor.executemany(
                "INSERT INTO pet_categories (name, icon, sort_order, status) VALUES (%s, %s, %s, %s)",
                categories
            )
            print(f"   ✅ 插入 {len(categories)} 个分类")

            print("🛒 插入商品...")
            products = [
                (1, '皇家狗粮 小型犬成犬粮 1.5kg', '狗粮', 89.00, 109.00, '', '营养均衡，适口性好', 100, 1250, 4.8, True, False, 1),
                (2, '渴望猫粮 六种鱼 1.8kg', '猫粮', 158.00, 198.00, '', '高蛋白，美毛护肤', 80, 890, 4.9, True, False, 1),
                (3, '宠物零食 鸡肉干 200g', '零食', 29.90, 39.90, '', '天然无添加，磨牙洁齿', 200, 560, 4.7, False, True, 1),
                (4, '渴望猫粮 无谷鸡肉味 5.4kg', '猫粮', 499.00, 599.00, '', '无谷配方，高蛋白，适合敏感肠胃猫咪', 50, 890, 4.9, 1, 1, 1),
                (5, '顽皮狗零食 牛肉干 500g', '零食', 39.90, 49.90, '', '天然牛肉，磨牙洁齿，适口性好', 200, 2300, 4.7, 1, 0, 1),
                (6, 'Petstages猫玩具 逗猫棒', '玩具', 29.90, 39.90, '', '互动玩具，锻炼猫咪反应能力', 80, 560, 4.6, 0, 1, 1),
                (7, '宝路狗粮 大型犬幼犬粮 10kg', '狗粮', 199.00, 249.00, '', '营养均衡，促进骨骼发育', 60, 780, 4.5, 0, 0, 1),
                (8, '伟嘉猫粮 海洋鱼味 2kg', '猫粮', 79.90, 99.90, '', '深海鱼肉，美毛护肤', 90, 1100, 4.7, 1, 0, 1),
                (9, '麦德氏猫零食 冻干三文鱼 100g', '零食', 69.90, 89.90, '', '低温冻干，保留营养', 70, 340, 4.8, 0, 1, 1),
                (10, 'KONG狗玩具 经典橡胶球', '玩具', 59.00, 79.00, '', '耐咬橡胶球，适合中大型犬', 40, 280, 4.9, 0, 0, 1),
                (11, '福来恩体外驱虫滴剂', '医疗', 129.00, 159.00, '', '广谱驱虫，安全有效', 120, 450, 4.9, 1, 0, 1),
                (12, '宠物专用沐浴露 500ml', '洗护', 49.90, 69.90, '', '温和配方，不刺激皮肤', 150, 890, 4.6, 0, 1, 1),
                (13, '猫砂 膨润土结团猫砂 10kg', '用品', 59.90, 79.90, '', '快速结团，除臭效果好', 200, 1500, 4.7, 1, 0, 1),
                (14, '宠物牵引绳 小型犬专用', '用品', 39.90, 59.90, '', '防拉扯设计，舒适耐用', 120, 890, 4.6, 0, 1, 1),
                (15, '宠物指甲剪 安全指甲钳', '用品', 29.90, 39.90, '', '安全设计，防止剪伤', 80, 670, 4.8, 0, 0, 1),
                (16, '宠物窝 四季通用', '用品', 89.90, 129.90, '', '四季通用，保暖透气', 60, 450, 4.7, 0, 1, 1),
                (17, '宠物梳子 长毛猫专用', '用品', 19.90, 29.90, '', '防静电设计，适合长毛猫', 150, 980, 4.6, 0, 0, 1),
                (18, '宠物罐头 猫湿粮 85g', '零食', 12.90, 16.90, '', '真肉制作，营养丰富', 500, 3200, 4.9, 1, 0, 1),
                (19, '宠物益生菌 调理肠胃', '医疗', 69.90, 89.90, '', '调理肠胃，增强免疫力', 100, 780, 4.8, 1, 1, 1),
                (20, '宠物口腔清洁喷剂', '医疗', 49.90, 69.90, '', '清洁口腔，预防牙结石', 80, 340, 4.5, 0, 0, 1),
                (21, '宠物眼药水 抗菌消炎', '医疗', 39.90, 59.90, '', '抗菌消炎，缓解眼部不适', 120, 560, 4.7, 0, 1, 1),
                (22, '宠物专用指甲打磨器', '用品', 79.90, 99.90, '', '电动打磨，安全方便', 50, 280, 4.6, 0, 0, 1)
            ]
            cursor.executemany(
                "INSERT INTO products (id, name, category, price, original_price, image_url, description, stock, sales, rating, is_hot, is_new, status) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)",
                products
            )
            print(f"   ✅ 插入 {len(products)} 个商品")

            # 8. 测试收藏
            print("❤️ 插入测试收藏...")
            favorites = [
                (1, 1),
                (1, 2)
            ]
            cursor.executemany(
                "INSERT INTO favorites (user_id, product_id) VALUES (%s, %s)",
                favorites
            )
            print(f"   ✅ 插入 {len(favorites)} 个收藏")

            # 9. 测试订单
            print("📦 插入测试订单...")
            orders = [
                ('OD20240115001', 1, 89.00, 'completed', '{"name":"张三","phone":"13800138001","address":"北京市朝阳区望京街道101号"}', '微信支付'),
                ('OD20240115002', 1, 158.00, 'pending', '{"name":"张三","phone":"13800138001","address":"北京市朝阳区望京街道101号"}', '微信支付')
            ]
            cursor.executemany(
                "INSERT INTO orders (order_number, user_id, total_amount, status, address_info, payment_method) VALUES (%s, %s, %s, %s, %s, %s)",
                orders
            )
            print(f"   ✅ 插入 {len(orders)} 个订单")

            # 10. 测试订单商品
            print("🛍️ 插入测试订单商品...")
            order_items = [
                (1, 1, '皇家狗粮 小型犬成犬粮 1.5kg', '1.5kg', 89.00, 1, ''),
                (2, 2, '渴望猫粮 六种鱼 1.8kg', '1.8kg', 158.00, 1, '')
            ]
            cursor.executemany(
                "INSERT INTO order_items (order_id, product_id, product_name, spec, price, quantity, image_url) VALUES (%s, %s, %s, %s, %s, %s, %s)",
                order_items
            )
            print(f"   ✅ 插入 {len(order_items)} 个订单商品")

            conn.commit()
            print("\n" + "=" * 50)
            print("🎉 示例数据插入完成！")
            print("=" * 50)
            return True

        except Exception as e:
            print(f"❌ 插入数据失败: {e}")
            print(f"   错误详情: {e}")
            conn.rollback()
            return False
        finally:
            cursor.close()
            conn.close()

    def show_tables(self):
        """显示所有表和数据"""
        print("\n🔍 数据库状态检查...")
        print("=" * 50)

        conn = self.connect()
        cursor = conn.cursor()

        try:
            # 显示所有表
            cursor.execute("SHOW TABLES")
            tables = cursor.fetchall()

            print("📊 数据库表清单:")
            for table in tables:
                table_name = table[0]
                cursor.execute(f"SELECT COUNT(*) as count FROM {table_name}")
                count = cursor.fetchone()[0]
                print(f"   • {table_name}: {count} 条记录")

            # 显示示例数据预览
            print("\n📋 示例数据预览:")
            cursor.execute("SELECT id, nickname, phone FROM users LIMIT 3")
            users = cursor.fetchall()
            print("   👤 用户:", users)

            cursor.execute("SELECT id, name, type FROM user_pets LIMIT 3")
            pets = cursor.fetchall()
            print("   🐕 宠物:", pets)

            return True

        except Exception as e:
            print(f"❌ 检查失败: {e}")
            return False
        finally:
            cursor.close()
            conn.close()

def main():
    """主函数"""
    print("=" * 60)
    print("🐾 宠物平台 - 数据库初始化 (微信小程序对接版)")
    print("=" * 60)

    db = PetDatabase()

    try:
        # 步骤1：创建表
        print("\n[步骤1/3] 创建数据库表")
        if not db.create_tables():
            print("❌ 创建表失败，程序退出")
            return

        # 步骤2：插入数据
        print("\n[步骤2/3] 插入示例数据")
        choice = input("是否插入示例数据？(y/n, 默认y): ").strip().lower()
        if choice != 'n':
            if not db.insert_sample_data():
                print("⚠️  部分数据插入失败，但表结构已创建")

        # 步骤3：验证
        print("\n[步骤3/3] 验证数据库")
        db.show_tables()

        print("\n" + "=" * 60)
        print("🎉 数据库初始化完成！")
        print("=" * 60)
        print("🎯 微信小程序对接说明：")
        print("1. 用户登录: POST /api/user/login")
        print("2. 获取宠物: GET /api/pets (需要认证)")
        print("3. 获取订单: GET /api/orders (需要认证)")
        print("4. 获取笔记: GET /api/notes (需要认证)")
        print("5. 获取地址: GET /api/addresses (需要认证)")
        print("=" * 60)

    except KeyboardInterrupt:
        print("\n\n⚠️  用户中断操作")
    except Exception as e:
        print(f"\n❌ 初始化失败: {e}")

if __name__ == '__main__':
    main()
