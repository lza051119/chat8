
# 1. 认证相关API(authAPI)
## 1.1 用户注册
- **方法**：POST  
- **URL**：`http://localhost:3000/api/auth/register`
- **Headers**：`Content-Type: application/json`
- **Body**（raw, JSON）

```json
{
	"username": "testuser",
	"email": "testuser@example.com",
	"password": "123456"
}
```
*response*
```json
{
	"success": false,
	"message": "用户名或邮箱已存在",
	"error": "400"
}
```


```json
{
	"username": "testuser5",
	"email": "testuser5@example.com",
	"password": "123456"
}
```
*response*
```json
{
	"success": true,
	"message": "注册成功",
	"data": {
		"user": {
			"id": "5",
			"username": "testuser5",
			"email": "testuser5@example.com",
			"avatar": null,
			"created_at": "2025-06-30T18:15:08.625670"
		},
		"token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ0ZXN0dXNlcjUiLCJleHAiOjE3NTEzMTA5MDh9.pwSQJonCjDJQCCxzZL5GWYI1wZCnUMkj2S9ReSPe_HA"
	}
}
```

## 1.2 用户登录
- **方法**：POST  
- **URL**：`http://localhost:3000/api/auth/login`
- **Headers**：`Content-Type: application/json`
- **Body**（raw, JSON）


```json
{
	"username": "testuser",
	"password": "123456"
}
```
*response*
```json
{
	"success": true,
	"message": "登录成功",
	"data": {
		"user": {
			"id": "1",
			"username": "testuser",
			"email": "testuser@example.com",
			"avatar": null,
			"created_at": "2025-06-30T17:55:17.281077"
		},
		"token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ0ZXN0dXNlciIsImV4cCI6MTc1MTMxNDY0M30.Sc1WncuQDdWeoIf-WT6WCup1ZjEsRibId5Cqn4YZy4E"
	}
}
```


```json
{
	"username": "testuser1",
	"password": "123456"
}
```
*response*
```json
{
	"success": false,
	"message": "用户名或密码错误",
	"error": "UNAUTHORIZED"
}
```

## 1.3 获取当前用户信息
- **方法**：GET  
- **URL**：`http://localhost:3000/api/auth/me`
- **Headers**：`Authorization: Bearer {token}`

示例：
`Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ0ZXN0dXNlciIsImV4cCI6MTc1MTMxNDY0M30.Sc1WncuQDdWeoIf-WT6WCup1ZjEsRibId5Cqn4YZy4E`

```json
{
	"username": "testuser",
	"password": "123456"
}
```
*response*
```json
{
	"id": "1",
	"username": "testuser",
	"email": "testuser@example.com",
	"avatar": null,
	"created_at": "2025-06-30T17:55:17.281077"
}
```

## 1.4 刷新Token
- **方法**：POST  
- **URL**：`http://localhost:3000/api/auth/refresh`
- **Headers**：`Authorization: Bearer {token}`

```json
{
	"success": true,
	"data": {
		"token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ0ZXN0dXNlciIsImV4cCI6MTc1MTMxNTcxN30.9Org5xSxYaiCok76AUgbD7x-6pq5XY8tHxFTEnMqPCk"
	}
}
```

## 1.5 退出登录
- **方法**：POST  
- **URL**：`http://localhost:3000/api/auth/logout`
- **Headers**：`Authorization: Bearer {token}`

*response*
```json
{
	"success": true,
	"message": "退出登录成功"
}
```

# 2. 联系人相关API（contactAPI）

## 2.1 获取联系人列表
- **方法**：GET  
- **URL**：`http://localhost:3000/api/contacts`
- **Headers**：`Authorization: Bearer {token}`

*response*
```json
{
	"success": true,
	"data": {
		"items": [],
		"pagination": {
			"page": 1,
			"limit": 50,
			"total": 0,
			"totalPages": 0
		}
	}
}
```

## 2.2 添加联系人
- **方法**：POST  
- **URL**：`http://localhost:3000/api/contacts`
- **Headers**：`Authorization: Bearer {token}`，`Content-Type: application/json`
- **Body**（raw, JSON）

```json
{
	"friendId": 2
}
```
*response*
```json
{
	"success": false,
	"message": "已经是好友",
	"error": "400"
}
```

```json
{
	"friendId": 3
}
```
*response*
```json
{
	"friend_id": 3,
	"id": 2,
	"user_id": 1,
	"created_at": "2025-06-30T20:10:57.464223"
}
```

## 2.3 删除联系人
- **方法**：DELETE  
- **URL**：`http://localhost:3000/api/contacts/{friend_id}`
- **Headers**：`Authorization: Bearer {token}`

*response*
```json
{
	"success": true,
	"message": "联系人删除成功"
}
```

## 2.4 搜索用户
- **方法**：GET  
- **URL**：`http://localhost:3000/api/users/search?q=test`
- **Headers**：`Authorization: Bearer {token}`

*response*
```json
{
	"success": true,
	"data": {
		"items": [
			{
				"id": "1",
				"username": "testuser",
				"email": "testuser@example.com",
				"avatarUrl": null
			},
			{
				"id": "2",
				"username": "testuser2",
				"email": "testuser2@example.com",
				"avatarUrl": null
			},
			{
				"id": "3",
				"username": "testuser3",
				"email": "testuser3@example.com",
				"avatarUrl": null
			},
			{
				"id": "4",
				"username": "testuser4",
				"email": "testuser4@example.com",
				"avatarUrl": null
			},
			{
				"id": "5",
				"username": "testuser5",
				"email": "testuser5@example.com",
				"avatarUrl": null
			}
		],
		"pagination": {
			"page": 1,
			"limit": 20,
			"total": 5,
			"totalPages": 1
		}
	}
}
```

# 3. 消息相关API（messageAPI）

## 3.1 发送消息
- **方法**：POST  
- **URL**：`http://localhost:3000/api/messages`
- **Headers**：`Authorization: Bearer {token}`，`Content-Type: application/json`
- **Body**（raw, JSON）

```json
{
	"to": 2,
	"content": "你好",
	"encrypted": true,
	"method": "Server"
}
  ```
*response*
```json
{
	"to": 2,
	"content": "你好",
	"encrypted": true,
	"method": "Server",
	"destroyAfter": null,
	"id": 1,
	"from": 1,
	"timestamp": "2025-06-30T20:18:22.857418"
}
```

## 3.2 获取消息历史
- **方法**：GET  
- **URL**：`http://localhost:3000/api/messages/history/{userId}?page=1&limit=20`
- **Headers**：`Authorization: Bearer {token}`

*response*
```json
{
    "success": true,
    "data": {
        "messages": [
            {
                "to_id": 2,
                "encrypted": true,
                "from_id": 1,
                "timestamp": "2025-06-30T20:18:22.857418",
                "content": "你好",
                "id": 1,
                "method": "Server",
                "destroy_after": null
            }
        ],
        "pagination": {
            "page": 1,
            "limit": 20,
            "total": 1,
            "totalPages": 1
        }
    }
}
```

## 3.3 删除消息
- **方法**：DELETE  
- **URL**：`http://localhost:3000/api/messages/{message_id}`
- **Headers**：`Authorization: Bearer {token}`

*response*
```json
{
    "success": true,
    "message": "消息删除成功"
}
```

# 4. 密钥管理API（keyAPI）

## 4.1 上传公钥
- **方法**：POST  
- **URL**：`http://localhost:3000/api/keys/public?fingerprint={}/`
- **Headers**：`Authorization: Bearer {token}`，`Content-Type: application/json`
- **Body**（raw, JSON）

公钥指纹例如：`SHA256:AA:BB:CC:DD:EE:FF`

```json
  {
    "publicKey": "-----BEGIN PUBLIC KEY-----\n...你的公钥内容...\n-----END PUBLIC KEY-----"
  }
```
*response*
```json
{
    "publicKey": "-----BEGIN PUBLIC KEY-----\n...你的公钥内容...\n-----END PUBLIC KEY-----",
    "id": 1,
    "userId": 1,
    "fingerprint": "SHA256:AA:BB:CC:DD:EE:FF",
    "updatedAt": "2025-07-01T04:55:42.211184"
}
```

## 4.2 获取单个用户公钥
- **方法**：GET  
- **URL**：`http://localhost:3000/api/keys/public/{user_id}`
- **Headers**：`Authorization: Bearer {token}`

*response*
```json
{
    "publicKey": "-----BEGIN PUBLIC KEY-----\n...你的公钥内容...\n-----END PUBLIC KEY-----",
    "id": 1,
    "userId": 1,
    "fingerprint": "SHA256:AA:BB:CC:DD:EE:FF",
    "updatedAt": "2025-07-01T04:55:42.211184"
}
```

## 4.3 获取所有联系人公钥
- **方法**：GET  
- **URL**：`http://localhost:3000/api/keys/public`
- **Headers**：`Authorization: Bearer {token}`

*response*
```json
[
    {
        "publicKey": "-----BEGIN PUBLIC KEY-----\n...你的公钥内容...\n-----END PUBLIC KEY-----",
        "id": 2,
        "userId": 2,
        "fingerprint": "SHA256:AA:BB:CC:DD:EE:FF",
        "updatedAt": "2025-07-01T05:54:40.451308"
    }
]
```

## 4.4 校验指纹（功能增强）
- **方法**：POST  
- **URL**：`http://localhost:3000/api/keys/verify-fingerprint`
- **Headers**：`Authorization: Bearer {token}`，`Content-Type: application/json`
- **Body**（raw, JSON）

```json
{
	"user_id": 2,
	"fingerprint": "SHA256:AA:BB:CC:DD:EE:FF"
}
```
*response*
```json
{
	"success": true,
	"message": "指纹校验通过"
}
```

# 5.WebRTC信令API（signalingAPI）

## 5.1 发送Offer

* **方法**：POST
* **URL**：`http://localhost:3000/api/signaling/offer?targetUserId={id}`
* **Headers**：`Authorization: Bearer {token}`，`Content-Type: application/json`
* **Body**（raw, JSON）

```json
{
	"targetUserId": 0,
	"offer": {
		"type": "offer",
		"sdp": "xxxx"
	}
}
```
*response*
```json
{
    "success": true,
    "message": "Offer发送成功"
}
```

## 5.2 发送Answer
* **方法**：POST
* **URL**：`http://localhost:3000/api/signaling/answer`
* **Headers**：`Authorization: Bearer {token}`，`Content-Type: application/json`
  
```json
{
	"targetUserId": 0,
	"offer": {
		"type": "answer",
		"sdp": "xxxx"
	}
}
```
*response*
```json
{  
	"success": true,
	"message": "Answer发送成功"
}
```

## 5.3 发送ICE Candidate
* **方法**：POST
* **URL**：`http://localhost:3000/api/signaling/ice-candidate`
* **Headers**：`Authorization: Bearer {token}`，`Content-Type: application/json`
  
```json
{
	"targetUserId": 2,
	"candidate": {
		"candidate": "xxxx",
		"sdpMLineIndex": 0,
		"sdpMid": "audio"
	}
}
```
 *reponse*
```json
{
	"success": true,
	"message": "ICE Candidate发送成功"
}
```

## 5.4 获取待处理信令
* **方法**：GET  
* **URL**：`http://localhost:3000/api/signaling/pending`
* **Headers**：`Authorization: Bearer {token}`

*reponse*
  ```json
{
"success": true,
"data": [
	{
		"id": "1",
		"type": "offer",
		"fromUserId": "2",
		"fromUsername": "testuser2",
		"data": {
			"type": "offer",
			"sdp": "xxxx"
		},
		"timestamp": "2024-01-01T00:00:00.000Z"
	}
]
}
  ```
 
# 6. 在线状态API（presenceAPI）

## 6.1 设置在线状态
- **方法**：POST 
- **URL**：`http://localhost:3000/api/presence/status`
- **Headers**：`Authorization: Bearer {token}`，`Content-Type: application/json`

```json
{
	"status": "online"
}
```

*reponse*
```json
{
	"success": true,
	"message": "状态更新成功"
}
```

## 6.2 获取联系人在线状态
- **方法**：GET  
- **URL**：`http://localhost:3000/api/presence/contacts`
- **Headers**：`Authorization: Bearer {token}`

*response*
```json
{
    "success": true,
    "data": [
        {
            "userId": "2",
            "username": "testuser2",
            "status": "offline",
            "lastSeen": "2025-06-30T18:04:16.827136"
        },
        {
            "userId": "3",
            "username": "testuser3",
            "status": "offline",
            "lastSeen": "2025-06-30T18:08:36.872046"
        }
    ]
}
```

## 6.3 心跳
- **方法**：POST  
- **URL**：`http://localhost:3000/api/presence/heartbeat`
- **Headers**：`Authorization: Bearer {token}`

*reponse*
```json
{
    "success": true,
    "data": {
        "nextHeartbeat": 30000
    }
}
```

# 7. WebSocket测试

## 7.1 连接WebSocket
- **URL**：`ws://localhost:3000/ws?token={token}`

```json
{
	"type": "private_message",
	"to_id": 1,
	"content": "你好"
}
```
*response*
```json
{
	"type": "message",
	"data": {
		"from": 1,
		"to": 1,
		"content": "\u4f60\u597d",
		"timestamp": null,
		"encrypted": true,
		"method": "Server",
		"destroy_after": null
	}
}
```

