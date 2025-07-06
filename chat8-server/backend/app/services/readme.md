# 用户状态管理服务 (User States Update Service)

## 概述

`user_states_update.py` 提供了完整的用户在线状态管理功能，包括用户登录/退出状态处理、心跳监控和好友状态通知。

## 主要功能

### 1. 用户登录处理
- 用户WebSocket连接建立时自动触发
- 更新数据库中用户状态为 `online`
- 获取并发送用户的在线好友列表
- 向所有在线好友广播用户上线消息

### 2. 用户退出处理
- 用户WebSocket连接断开时自动触发
- 更新数据库中用户状态为 `offline`
- 向所有在线好友广播用户离线消息

### 3. 心跳监控
- 每60秒自动检查所有在线用户的心跳状态
- 超时时间为120秒
- 自动处理心跳超时的用户，设置为离线状态

## API 端点

### 心跳相关
- `POST /api/user-status/heartbeat` - 发送心跳信号
- `POST /api/user-status/check-timeouts` - 手动触发心跳超时检查

### 状态查询
- `GET /api/user-status/me` - 获取当前用户状态
- `GET /api/user-status/{user_id}` - 获取指定用户状态
- `GET /api/user-status/stats` - 获取服务统计信息

### 管理功能
- `POST /api/user-status/force-logout/{user_id}` - 强制用户离线

## WebSocket 消息格式

### 好友状态通知
```json
{
  "type": "friends_status",
  "data": {
    "online_friends": [
      {
        "user_id": 123,
        "username": "friend1",
        "status": "online",
        "last_seen": "2024-01-01T12:00:00Z"
      }
    ]
  }
}
```

### 用户状态变化通知
```json
{
  "type": "user_status_change",
  "data": {
    "user_id": 123,
    "username": "user1",
    "status": "online", // 或 "offline"
    "timestamp": "2024-01-01T12:00:00Z"
  }
}
```

### 心跳消息
```json
// 客户端发送
{
  "type": "heartbeat",
  "timestamp": 1704110400000
}

// 服务器响应
{
  "type": "heartbeat_response",
  "timestamp": 1704110400000
}
```

## 使用示例

### 初始化服务
```python
from services.user_states_update import initialize_user_states_service
from websocket.manager import ConnectionManager

connection_manager = ConnectionManager()
user_states_service = initialize_user_states_service(connection_manager)
await user_states_service.start_heartbeat_monitor()
```

### 处理用户登录
```python
from services.user_states_update import get_user_states_service

user_states_service = get_user_states_service()
result = await user_states_service.user_login(user_id)
if result["success"]:
    print(f"用户 {user_id} 登录成功")
    print(f"在线好友: {result['online_friends']}")
```

### 处理用户退出
```python
user_states_service = get_user_states_service()
result = await user_states_service.user_logout(user_id)
if result["success"]:
    print(f"用户 {user_id} 已离线，通知了 {result['notified_friends']} 个好友")
```

### 更新心跳
```python
user_states_service = get_user_states_service()
result = await user_states_service.update_user_heartbeat(user_id)
```

## 配置参数

- `heartbeat_interval`: 心跳检测间隔，默认60秒
- `heartbeat_timeout`: 心跳超时时间，默认120秒

## 日志记录

服务会记录以下类型的日志：
- `[状态更新]`: 用户状态变化相关日志
- `[心跳监控]`: 心跳监控相关日志
- `[心跳检测]`: 心跳超时检测相关日志
- `[消息发送]`: WebSocket消息发送相关日志

## 数据库字段

服务依赖 `User` 表的以下字段：
- `id`: 用户ID
- `username`: 用户名
- `status`: 用户状态 ('online'/'offline')
- `last_seen`: 最后在线时间

## 注意事项

1. 服务需要在应用启动时初始化
2. 心跳监控会在后台持续运行
3. WebSocket连接断开时会自动处理用户离线状态
4. 服务是线程安全的，可以在多个WebSocket连接中并发使用
5. 建议在生产环境中调整心跳间隔和超时时间以适应网络条件