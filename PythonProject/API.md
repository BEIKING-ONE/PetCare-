# 宠物平台 API 文档

## 基础信息

- 基础URL: `http://localhost:5000`
- API版本: v3.0
- 认证方式: JWT Bearer Token

## 通用响应格式

所有API响应遵循统一格式：

```json
{
  "code": 0,
  "message": "success",
  "data": {}
}
```

- `code`: 状态码，0表示成功，其他表示失败
- `message`: 响应消息
- `data`: 响应数据

## 认证说明

需要认证的接口需要在请求头中携带Token：

```
Authorization: Bearer {token}
```

---

## 用户相关 API

### 1. 用户登录

**接口**: `POST /api/user/login`

**请求参数**:
```json
{
  "code": "微信登录code",
  "nickname": "用户昵称",
  "avatarUrl": "头像URL",
  "phone": "手机号"
}
```

**响应示例**:
```json
{
  "code": 0,
  "message": "登录成功",
  "data": {
    "userInfo": {
      "id": 1,
      "nickname": "微信用户",
      "avatar": "https://...",
      "phone": "13800138000"
    },
    "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
  }
}
```

### 2. 获取用户信息

**接口**: `GET /api/user/info`

**认证**: 需要

**响应示例**:
```json
{
  "code": 0,
  "message": "success",
  "data": {
    "id": 1,
    "nickname": "微信用户",
    "avatar": "https://...",
    "phone": "13800138000",
    "created_at": "2024-01-01 00:00:00"
  }
}
```

### 3. 更新用户信息

**接口**: `PUT /api/user/info`

**认证**: 需要

**请求参数**:
```json
{
  "nickname": "新昵称",
  "phone": "13800138000",
  "avatarUrl": "https://..."
}
```

---

## 宠物相关 API

### 1. 获取宠物列表

**接口**: `GET /api/pets`

**认证**: 需要

**响应示例**:
```json
{
  "code": 0,
  "message": "success",
  "data": [
    {
      "id": 1,
      "name": "旺财",
      "type": "dog",
      "breed": "金毛",
      "age": "3岁",
      "weight": "25kg",
      "gender": "公",
      "birthday": "2021-01-15",
      "avatar": "https://...",
      "healthStatus": "健康",
      "vaccineRecords": "已完成狂犬疫苗"
    }
  ]
}
```

### 2. 添加宠物

**接口**: `POST /api/pets`

**认证**: 需要

**请求参数**:
```json
{
  "name": "宠物名称",
  "type": "dog",
  "breed": "品种",
  "age": "年龄",
  "weight": "体重",
  "gender": "性别",
  "birthday": "2021-01-01",
  "avatar": "头像URL",
  "healthStatus": "健康状态",
  "vaccineRecords": "疫苗记录"
}
```

### 3. 删除宠物

**接口**: `DELETE /api/pets/{pet_id}`

**认证**: 需要

---

## 购物车相关 API

### 1. 获取购物车

**接口**: `GET /api/cart`

**认证**: 需要

**响应示例**:
```json
{
  "code": 0,
  "message": "success",
  "data": [
    {
      "id": 1,
      "product_id": 1,
      "quantity": 2,
      "selected": true,
      "name": "商品名称",
      "price": 89.00,
      "image": "https://...",
      "stock": 100
    }
  ]
}
```

### 2. 添加商品到购物车

**接口**: `POST /api/cart`

**认证**: 需要

**请求参数**:
```json
{
  "productId": 1,
  "quantity": 2
}
```

### 3. 修改购物车

**接口**: `PUT /api/cart/{cart_id}`

**认证**: 需要

**请求参数**:
```json
{
  "quantity": 3,
  "selected": true
}
```

### 4. 删除购物车项

**接口**: `DELETE /api/cart/{cart_id}`

**认证**: 需要

### 5. 清空购物车

**接口**: `POST /api/cart/clear`

**认证**: 需要

---

## 订单相关 API

### 1. 获取订单列表

**接口**: `GET /api/orders`

**认证**: 需要

**查询参数**:
- `status`: 订单状态（可选）
- `page`: 页码，默认1
- `pageSize`: 每页数量，默认10

**响应示例**:
```json
{
  "code": 0,
  "message": "success",
  "data": [
    {
      "id": 1,
      "orderNo": "OD20240115001234567",
      "totalAmount": 89.00,
      "status": "paid",
      "paymentMethod": "微信支付",
      "address": {...},
      "createdAt": "2024-01-15 10:00:00",
      "items": [...]
    }
  ]
}
```

### 2. 获取订单详情

**接口**: `GET /api/orders/{order_id}`

**认证**: 需要

### 3. 创建订单

**接口**: `POST /api/orders`

**认证**: 需要

**请求参数**:
```json
{
  "addressId": 1,
  "items": [
    {
      "productId": 1,
      "quantity": 2
    }
  ],
  "couponId": 1,
  "remark": "订单备注"
}
```

### 4. 支付订单

**接口**: `POST /api/orders/pay`

**认证**: 需要

**请求参数**:
```json
{
  "orderId": 1,
  "paymentMethod": "微信支付"
}
```

### 5. 取消订单

**接口**: `POST /api/orders/cancel`

**认证**: 需要

**请求参数**:
```json
{
  "orderId": 1
}
```

---

## 笔记相关 API

### 1. 获取笔记列表

**接口**: `GET /api/notes`

**认证**: 需要

**查询参数**:
- `category`: 分类（可选）

**响应示例**:
```json
{
  "code": 0,
  "message": "success",
  "data": [
    {
      "id": 1,
      "title": "笔记标题",
      "content": "笔记内容",
      "category": "daily",
      "images": ["https://..."],
      "tags": ["标签1", "标签2"],
      "createdAt": "2024-01-15 10:00:00"
    }
  ]
}
```

### 2. 添加笔记

**接口**: `POST /api/notes`

**认证**: 需要

**请求参数**:
```json
{
  "title": "笔记标题",
  "content": "笔记内容",
  "category": "daily",
  "images": ["https://..."],
  "tags": ["标签1", "标签2"]
}
```

### 3. 删除笔记

**接口**: `DELETE /api/notes/{note_id}`

**认证**: 需要

---

## 地址相关 API

### 1. 获取地址列表

**接口**: `GET /api/addresses`

**认证**: 需要

**响应示例**:
```json
{
  "code": 0,
  "message": "success",
  "data": [
    {
      "id": 1,
      "name": "张三",
      "phone": "13800138001",
      "province": "北京市",
      "city": "北京市",
      "district": "朝阳区",
      "detail": "望京街道101号",
      "isDefault": true,
      "createdAt": "2024-01-15 10:00:00"
    }
  ]
}
```

### 2. 添加地址

**接口**: `POST /api/addresses`

**认证**: 需要

**请求参数**:
```json
{
  "name": "张三",
  "phone": "13800138001",
  "province": "北京市",
  "city": "北京市",
  "district": "朝阳区",
  "detail": "望京街道101号",
  "isDefault": true
}
```

### 3. 更新地址

**接口**: `PUT /api/addresses/{address_id}`

**认证**: 需要

### 4. 删除地址

**接口**: `DELETE /api/addresses/{address_id}`

**认证**: 需要

---

## 收藏相关 API

### 1. 获取收藏列表

**接口**: `GET /api/favorites`

**认证**: 需要

**响应示例**:
```json
{
  "code": 0,
  "message": "success",
  "data": [
    {
      "id": 1,
      "product_id": 1,
      "createdAt": "2024-01-15 10:00:00",
      "name": "商品名称",
      "price": 89.00,
      "image": "https://...",
      "original_price": 109.00,
      "stock": 100,
      "sales": 1250,
      "is_hot": true
    }
  ]
}
```

### 2. 添加收藏

**接口**: `POST /api/favorites`

**认证**: 需要

**请求参数**:
```json
{
  "productId": 1
}
```

### 3. 取消收藏

**接口**: `DELETE /api/favorites/{favorite_id}`

**认证**: 需要

---

## 优惠券相关 API

### 1. 获取优惠券列表

**接口**: `GET /api/coupons`

**认证**: 需要

**响应示例**:
```json
{
  "code": 0,
  "message": "success",
  "data": [
    {
      "id": 1,
      "name": "新用户专享券",
      "amount": 20.00,
      "min_amount": 100.00,
      "expireTime": "2024-12-31 23:59:59",
      "status": "available",
      "createdAt": "2024-01-15 10:00:00"
    }
  ]
}
```

---

## 商品相关 API

### 1. 获取商品列表

**接口**: `GET /api/products`

**认证**: 不需要

**查询参数**:
- `limit`: 返回数量，默认10
- `category`: 分类
- `isHot`: 是否热门（0/1）
- `keyword`: 搜索关键词

**响应示例**:
```json
{
  "code": 0,
  "message": "success",
  "data": [
    {
      "id": 1,
      "name": "商品名称",
      "category": "狗粮",
      "price": 89.00,
      "original_price": 109.00,
      "image_url": "https://...",
      "description": "商品描述",
      "stock": 100,
      "sales": 1250,
      "is_hot": true
    }
  ],
  "count": 10
}
```

### 2. 获取商品详情

**接口**: `GET /api/products/{product_id}`

**认证**: 不需要

---

## 搜索 API

### 1. 搜索

**接口**: `GET /api/search`

**认证**: 不需要

**查询参数**:
- `keyword`: 搜索关键词（必填）
- `type`: 搜索类型（product/note），默认product
- `page`: 页码，默认1
- `pageSize`: 每页数量，默认10

**响应示例**:
```json
{
  "code": 0,
  "message": "success",
  "data": [...],
  "keyword": "狗粮",
  "type": "product"
}
```

---

## 文件上传 API

### 1. 上传文件

**接口**: `POST /api/upload`

**认证**: 需要

**请求类型**: multipart/form-data

**请求参数**:
- `file`: 文件（支持png, jpg, jpeg, gif）

**响应示例**:
```json
{
  "code": 0,
  "message": "上传成功",
  "data": {
    "url": "/uploads/1234567890_image.jpg",
    "filename": "1234567890_image.jpg"
  }
}
```

---

## 公共 API

### 1. 健康检查

**接口**: `GET /api/health`

**认证**: 不需要

**响应示例**:
```json
{
  "code": 0,
  "message": "服务正常",
  "data": {
    "status": "running",
    "database": "connected",
    "timestamp": "2024-01-15 10:00:00"
  }
}
```

### 2. 获取宠物分类

**接口**: `GET /api/pets/categories`

**认证**: 不需要

**响应示例**:
```json
{
  "code": 0,
  "message": "success",
  "data": [
    {
      "id": 1,
      "name": "狗狗",
      "icon": "🐶",
      "sort_order": 1,
      "status": 1
    }
  ],
  "count": 3
}
```

---

## 错误码说明

| 错误码 | 说明 |
|--------|------|
| 0 | 成功 |
| 400 | 请求参数错误 |
| 401 | 未认证或认证失败 |
| 404 | 资源不存在 |
| 500 | 服务器内部错误 |

---

## 微信小程序对接注意事项

1. **登录流程**:
   - 前端调用`wx.login()`获取code
   - 将code发送到`POST /api/user/login`
   - 获取token并存储在本地

2. **认证请求**:
   - 所有需要认证的接口需要在请求头中携带token
   - Token格式：`Authorization: Bearer {token}`

3. **微信配置**:
   - 请在`.env`文件中配置正确的`WX_APP_ID`和`WX_APP_SECRET`
   - 需要在微信小程序后台配置服务器域名白名单

4. **图片上传**:
   - 使用`POST /api/upload`上传图片
   - 支持的格式：png, jpg, jpeg, gif
   - 最大文件大小：16MB

5. **订单流程**:
   - 添加商品到购物车 → 创建订单 → 支付订单
   - 创建订单时会自动清空购物车中的相关商品
