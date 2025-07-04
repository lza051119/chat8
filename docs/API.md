# Chat8 API 文档

本文档描述了 Chat8 项目的 REST API 接口和 WebSocket 连接。

## 目录

- [基础信息](#基础信息)
- [认证接口](#认证接口)
- [用户管理](#用户管理)
- [好友管理](#好友管理)
- [消息接口](#消息接口)
- [文件上传](#文件上传)
- [加密接口](#加密接口)
- [WebSocket 接口](#websocket-接口)
- [错误处理](#错误处理)
- [示例代码](#示例代码)

## 基础信息

### 服务器地址

- **开发环境**: `http://localhost:8000`
- **生产环境**: `https://your-domain.com`

### API 版本

当前 API 版本: `v1`

所有 API 接口都以 `/api/v1` 为前缀。

### 认证方式

使用 JWT (JSON Web Token) 进行身份认证。

在请求头中包含：
```
Authorization: Bearer <your-jwt-token>
```

### 响应格式

所有 API 响应都使用 JSON 格式：

```json
{
  "success": true,
  "data": {},
  "message": "操作成功",
  "timestamp": "2024-01-01T00:00:00Z"
}
```

错误响应：
```json
{
  "success": false,
  "error": {
    "code": "ERROR_CODE",
    "message": "错误描述",
    "details": {}
  },
  "timestamp": "2024-01-01T00:00:00Z"
}
```

## 认证接口

### 用户注册

**POST** `/api/v1/auth/register`

注册新用户账户。

**请求体：**
```json
{
  "username": "string",
  "email": "string",
  "password": "string",
  "confirm_password": "string"
}
```

**响应：**
```json
{
  "success": true,
  "data": {
    "user_id": "integer",
    "username": "string",
    "email": "string",
    "access_token": "string",
    "token_type": "bearer"
  }
}
```

### 用户登录

**POST** `/api/v1/auth/login`

用户登录获取访问令牌。

**请求体：**
```json
{
  "username": "string",
  "password": "string"
}
```

**响应：**
```json
{
  "success": true,
  "data": {
    "access_token": "string",
    "token_type": "bearer",
    "expires_in": 1800,
    "user": {
      "id": "integer",
      "username": "string",
      "email": "string",
      "avatar": "string"
    }
  }
}
```

### 刷新令牌

**POST** `/api/v1/auth/refresh`

刷新访问令牌。

**请求头：**
```
Authorization: Bearer <current-token>
```

**响应：**
```json
{
  "success": true,
  "data": {
    "access_token": "string",
    "token_type": "bearer",
    "expires_in": 1800
  }
}
```

### 用户登出

**POST** `/api/v1/auth/logout`

用户登出，使令牌失效。

**请求头：**
```
Authorization: Bearer <token>
```

**响应：**
```json
{
  "success": true,
  "message": "登出成功"
}
```

## 用户管理

### 获取当前用户信息

**GET** `/api/v1/user/profile`

获取当前登录用户的详细信息。

**请求头：**
```
Authorization: Bearer <token>
```

**响应：**
```json
{
  "success": true,
  "data": {
    "id": "integer",
    "username": "string",
    "email": "string",
    "avatar": "string",
    "status": "online|offline|away",
    "created_at": "string",
    "last_login": "string"
  }
}
```

### 更新用户资料

**PUT** `/api/v1/user/profile`

更新当前用户的资料信息。

**请求头：**
```
Authorization: Bearer <token>
```

**请求体：**
```json
{
  "username": "string",
  "email": "string",
  "avatar": "string"
}
```

**响应：**
```json
{
  "success": true,
  "data": {
    "id": "integer",
    "username": "string",
    "email": "string",
    "avatar": "string"
  }
}
```

### 修改密码

**PUT** `/api/v1/user/password`

修改用户密码。

**请求头：**
```
Authorization: Bearer <token>
```

**请求体：**
```json
{
  "current_password": "string",
  "new_password": "string",
  "confirm_password": "string"
}
```

**响应：**
```json
{
  "success": true,
  "message": "密码修改成功"
}
```

### 更新用户状态

**PUT** `/api/v1/user/status`

更新用户在线状态。

**请求头：**
```
Authorization: Bearer <token>
```

**请求体：**
```json
{
  "status": "online|offline|away"
}
```

**响应：**
```json
{
  "success": true,
  "data": {
    "status": "string"
  }
}
```

## 好友管理

### 获取好友列表

**GET** `/api/v1/friends`

获取当前用户的好友列表。

**请求头：**
```
Authorization: Bearer <token>
```

**响应：**
```json
{
  "success": true,
  "data": [
    {
      "id": "integer",
      "username": "string",
      "avatar": "string",
      "status": "online|offline|away",
      "last_seen": "string"
    }
  ]
}
```

### 搜索用户

**GET** `/api/v1/friends/search?q={query}`

根据用户名或邮箱搜索用户。

**请求头：**
```
Authorization: Bearer <token>
```

**查询参数：**
- `q`: 搜索关键词

**响应：**
```json
{
  "success": true,
  "data": [
    {
      "id": "integer",
      "username": "string",
      "avatar": "string",
      "is_friend": "boolean"
    }
  ]
}
```

### 发送好友请求

**POST** `/api/v1/friends/request`

向其他用户发送好友请求。

**请求头：**
```
Authorization: Bearer <token>
```

**请求体：**
```json
{
  "user_id": "integer",
  "message": "string"
}
```

**响应：**
```json
{
  "success": true,
  "message": "好友请求已发送"
}
```

### 处理好友请求

**PUT** `/api/v1/friends/request/{request_id}`

接受或拒绝好友请求。

**请求头：**
```
Authorization: Bearer <token>
```

**请求体：**
```json
{
  "action": "accept|reject"
}
```

**响应：**
```json
{
  "success": true,
  "message": "好友请求已处理"
}
```

### 删除好友

**DELETE** `/api/v1/friends/{friend_id}`

删除指定好友。

**请求头：**
```
Authorization: Bearer <token>
```

**响应：**
```json
{
  "success": true,
  "message": "好友已删除"
}
```

## 消息接口

### 获取聊天记录

**GET** `/api/v1/messages/{friend_id}?page={page}&limit={limit}`

获取与指定好友的聊天记录。

**请求头：**
```
Authorization: Bearer <token>
```

**查询参数：**
- `page`: 页码（默认：1）
- `limit`: 每页数量（默认：50）

**响应：**
```json
{
  "success": true,
  "data": {
    "messages": [
      {
        "id": "integer",
        "sender_id": "integer",
        "receiver_id": "integer",
        "content": "string",
        "message_type": "text|image|file|audio|video",
        "timestamp": "string",
        "is_read": "boolean",
        "is_encrypted": "boolean"
      }
    ],
    "pagination": {
      "page": "integer",
      "limit": "integer",
      "total": "integer",
      "pages": "integer"
    }
  }
}
```

### 发送消息

**POST** `/api/v1/messages`

发送消息给指定用户。

**请求头：**
```
Authorization: Bearer <token>
```

**请求体：**
```json
{
  "receiver_id": "integer",
  "content": "string",
  "message_type": "text|image|file|audio|video",
  "is_encrypted": "boolean"
}
```

**响应：**
```json
{
  "success": true,
  "data": {
    "id": "integer",
    "sender_id": "integer",
    "receiver_id": "integer",
    "content": "string",
    "message_type": "string",
    "timestamp": "string",
    "is_encrypted": "boolean"
  }
}
```

### 标记消息已读

**PUT** `/api/v1/messages/{message_id}/read`

标记指定消息为已读。

**请求头：**
```
Authorization: Bearer <token>
```

**响应：**
```json
{
  "success": true,
  "message": "消息已标记为已读"
}
```

### 删除消息

**DELETE** `/api/v1/messages/{message_id}`

删除指定消息。

**请求头：**
```
Authorization: Bearer <token>
```

**响应：**
```json
{
  "success": true,
  "message": "消息已删除"
}
```

## 文件上传

### 上传头像

**POST** `/api/v1/upload/avatar`

上传用户头像。

**请求头：**
```
Authorization: Bearer <token>
Content-Type: multipart/form-data
```

**请求体：**
```
file: <image-file>
```

**响应：**
```json
{
  "success": true,
  "data": {
    "avatar_url": "string"
  }
}
```

### 上传文件

**POST** `/api/v1/upload/file`

上传聊天文件。

**请求头：**
```
Authorization: Bearer <token>
Content-Type: multipart/form-data
```

**请求体：**
```
file: <file>
receiver_id: <integer>
```

**响应：**
```json
{
  "success": true,
  "data": {
    "file_url": "string",
    "file_name": "string",
    "file_size": "integer",
    "file_type": "string"
  }
}
```

## 加密接口

### 获取公钥

**GET** `/api/v1/encryption/public-key/{user_id}`

获取指定用户的公钥。

**请求头：**
```
Authorization: Bearer <token>
```

**响应：**
```json
{
  "success": true,
  "data": {
    "user_id": "integer",
    "public_key": "string"
  }
}
```

### 更新密钥对

**POST** `/api/v1/encryption/keys`

更新用户的密钥对。

**请求头：**
```
Authorization: Bearer <token>
```

**请求体：**
```json
{
  "public_key": "string",
  "private_key_encrypted": "string"
}
```

**响应：**
```json
{
  "success": true,
  "message": "密钥对已更新"
}
```

## WebSocket 接口

### 连接地址

**WebSocket URL**: `ws://localhost:8000/ws/{user_id}?token={jwt_token}`

### 消息格式

所有 WebSocket 消息都使用 JSON 格式：

```json
{
  "type": "message_type",
  "data": {},
  "timestamp": "2024-01-01T00:00:00Z"
}
```

### 消息类型

#### 1. 新消息通知

**类型**: `new_message`

```json
{
  "type": "new_message",
  "data": {
    "id": "integer",
    "sender_id": "integer",
    "sender_username": "string",
    "content": "string",
    "message_type": "text|image|file|audio|video",
    "is_encrypted": "boolean"
  },
  "timestamp": "string"
}
```

#### 2. 用户状态更新

**类型**: `user_status`

```json
{
  "type": "user_status",
  "data": {
    "user_id": "integer",
    "username": "string",
    "status": "online|offline|away"
  },
  "timestamp": "string"
}
```

#### 3. 好友请求通知

**类型**: `friend_request`

```json
{
  "type": "friend_request",
  "data": {
    "request_id": "integer",
    "from_user_id": "integer",
    "from_username": "string",
    "message": "string"
  },
  "timestamp": "string"
}
```

#### 4. 语音通话邀请

**类型**: `voice_call_invite`

```json
{
  "type": "voice_call_invite",
  "data": {
    "call_id": "string",
    "from_user_id": "integer",
    "from_username": "string"
  },
  "timestamp": "string"
}
```

#### 5. 视频通话邀请

**类型**: `video_call_invite`

```json
{
  "type": "video_call_invite",
  "data": {
    "call_id": "string",
    "from_user_id": "integer",
    "from_username": "string"
  },
  "timestamp": "string"
}
```

#### 6. 心跳检测

**类型**: `ping`

客户端发送：
```json
{
  "type": "ping"
}
```

服务器响应：
```json
{
  "type": "pong",
  "timestamp": "string"
}
```

## 错误处理

### HTTP 状态码

- `200`: 成功
- `201`: 创建成功
- `400`: 请求参数错误
- `401`: 未授权
- `403`: 禁止访问
- `404`: 资源不存在
- `409`: 资源冲突
- `422`: 请求参数验证失败
- `500`: 服务器内部错误

### 错误代码

| 错误代码 | 描述 |
|---------|------|
| `AUTH_001` | 无效的认证令牌 |
| `AUTH_002` | 令牌已过期 |
| `AUTH_003` | 用户名或密码错误 |
| `USER_001` | 用户不存在 |
| `USER_002` | 用户名已存在 |
| `USER_003` | 邮箱已存在 |
| `FRIEND_001` | 好友关系不存在 |
| `FRIEND_002` | 不能添加自己为好友 |
| `FRIEND_003` | 好友请求已存在 |
| `MESSAGE_001` | 消息不存在 |
| `MESSAGE_002` | 无权限访问消息 |
| `FILE_001` | 文件类型不支持 |
| `FILE_002` | 文件大小超出限制 |
| `ENCRYPT_001` | 加密密钥不存在 |
| `ENCRYPT_002` | 解密失败 |

## 示例代码

### JavaScript (Axios)

```javascript
// 配置 Axios
const api = axios.create({
  baseURL: 'http://localhost:8000/api/v1',
  headers: {
    'Content-Type': 'application/json'
  }
});

// 添加请求拦截器
api.interceptors.request.use(config => {
  const token = localStorage.getItem('access_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// 用户登录
async function login(username, password) {
  try {
    const response = await api.post('/auth/login', {
      username,
      password
    });
    
    const { access_token } = response.data.data;
    localStorage.setItem('access_token', access_token);
    
    return response.data;
  } catch (error) {
    console.error('登录失败:', error.response.data);
    throw error;
  }
}

// 发送消息
async function sendMessage(receiverId, content, messageType = 'text') {
  try {
    const response = await api.post('/messages', {
      receiver_id: receiverId,
      content,
      message_type: messageType
    });
    
    return response.data;
  } catch (error) {
    console.error('发送消息失败:', error.response.data);
    throw error;
  }
}

// WebSocket 连接
function connectWebSocket(userId, token) {
  const ws = new WebSocket(`ws://localhost:8000/ws/${userId}?token=${token}`);
  
  ws.onopen = () => {
    console.log('WebSocket 连接已建立');
  };
  
  ws.onmessage = (event) => {
    const message = JSON.parse(event.data);
    console.log('收到消息:', message);
    
    switch (message.type) {
      case 'new_message':
        handleNewMessage(message.data);
        break;
      case 'user_status':
        handleUserStatus(message.data);
        break;
      case 'friend_request':
        handleFriendRequest(message.data);
        break;
    }
  };
  
  ws.onclose = () => {
    console.log('WebSocket 连接已关闭');
  };
  
  ws.onerror = (error) => {
    console.error('WebSocket 错误:', error);
  };
  
  return ws;
}
```

### Python (requests)

```python
import requests
import json

class Chat8API:
    def __init__(self, base_url='http://localhost:8000/api/v1'):
        self.base_url = base_url
        self.session = requests.Session()
        self.token = None
    
    def set_token(self, token):
        self.token = token
        self.session.headers.update({
            'Authorization': f'Bearer {token}'
        })
    
    def login(self, username, password):
        response = self.session.post(f'{self.base_url}/auth/login', json={
            'username': username,
            'password': password
        })
        
        if response.status_code == 200:
            data = response.json()
            self.set_token(data['data']['access_token'])
            return data
        else:
            raise Exception(f'登录失败: {response.text}')
    
    def get_friends(self):
        response = self.session.get(f'{self.base_url}/friends')
        
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(f'获取好友列表失败: {response.text}')
    
    def send_message(self, receiver_id, content, message_type='text'):
        response = self.session.post(f'{self.base_url}/messages', json={
            'receiver_id': receiver_id,
            'content': content,
            'message_type': message_type
        })
        
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(f'发送消息失败: {response.text}')

# 使用示例
api = Chat8API()

# 登录
login_result = api.login('username', 'password')
print('登录成功:', login_result)

# 获取好友列表
friends = api.get_friends()
print('好友列表:', friends)

# 发送消息
message = api.send_message(1, 'Hello, World!')
print('消息已发送:', message)
```

---

更多详细信息请参考在线 API 文档：`http://localhost:8000/docs`