# Chat8 全栈 API 接口文档

本文档详细列出了 Chat8 项目前端和后端之间的所有API接口，旨在为开发和维护提供清晰的参考。

---

## 目录
1.  [认证 (Authentication)](#1-认证-authentication)
2.  [联系人与好友 (Contacts & Friends)](#2-联系人与好友-contacts--friends)
3.  [消息 (Messages)](#3-消息-messages)
4.  [文件上传 (File Uploads)](#4-文件上传-file-uploads)
5.  [用户状态与心跳 (User Status & Heartbeat)](#5-用户状态与心跳-user-status--heartbeat)
6.  [WebRTC 信令 (WebRTC Signaling)](#6-webrtc-信令-webrtc-signaling)
7.  [用户头像 (Avatar)](#7-用户头像-avatar)
8.  [用户个人资料 (User Profile)](#8-用户个人资料-user-profile)
9.  [安全 (Security)](#9-安全-security)

---

## 1. 认证 (Authentication)

### 1.1 用户登录
- **Description**: 使用用户名和密码验证用户身份，成功后返回Token和用户信息。
- **Method**: `POST`
- **Path**: `/api/v1/auth/login`
- **Request Body**:
  ```json
  {
    "username": "string",
    "password": "string"
  }
  ```
- **Response**:
  ```json
  {
    "success": true,
    "message": "Login successful",
    "data": {
      "token": "string (jwt)",
      "user": {
        "userId": "integer",
        "username": "string",
        "email": "string",
        "avatar": "string | null",
        "createdAt": "string (datetime)"
      }
    }
  }
  ```

### 1.2 用户注册
- **Description**: 创建一个新用户。
- **Method**: `POST`
- **Path**: `/api/v1/auth/register`
- **Request Body**:
  ```json
  {
    "username": "string",
    "email": "string",
    "password": "string"
  }
  ```
- **Response**:
  ```json
  {
    "success": true,
    "message": "注册成功",
    "data": { ... }
  }
  ```

### 1.3 获取当前用户信息
- **Description**: 获取当前已登录用户的信息（需要Token认证）。
- **Method**: `GET`
- **Path**: `/api/v1/auth/me`
- **Response**: `UserOut` schema (同登录返回的user对象)。

### 1.4 用户登出
- **Description**: (名义上的接口) 前端实现登出主要是通过清除本地Token。
- **Method**: `POST`
- **Path**: `/api/v1/auth/logout`

### 1.5 密码重置
- **Description**: 密码重置流程，包括发送验证码、验证、重设密码。
- **Method**: `POST`
- **Paths**:
  - `/api/v1/auth/forgot-password` (Body: `{ "email": "string" }`)
  - `/api/v1/auth/verify-reset-code` (Body: `{ "email": "string", "code": "string" }`)
  - `/api/v1/auth/reset-password` (Body: `{ "email": "string", "code": "string", "new_password": "string" }`)

---

## 2. 联系人与好友 (Contacts & Friends)

### 2.1 获取联系人列表
- **Description**: 获取当前用户的所有好友列表。
- **Method**: `GET`
- **Path**: `/api/v1/contacts`

### 2.2 搜索用户
- **Description**: 根据用户名或邮箱搜索用户。
- **Method**: `GET`
- **Path**: `/api/v1/users/search?q={query}`

### 2.3 发送好友请求
- **Description**: 向另一个用户发送好友请求。
- **Method**: `POST`
- **Path**: `/api/v1/contacts/request`
- **Request Body**:
  ```json
  {
    "to_user_id": "integer",
    "message": "string | null"
  }
  ```

### 2.4 获取好友请求列表
- **Description**: 获取收到或发送的好友请求。
- **Method**: `GET`
- **Path**: `/api/v1/requests?request_type={type}` (type: 'received' or 'sent')

### 2.5 处理好友请求
- **Description**: 同意或拒绝一个好友请求。
- **Method**: `POST`
- **Path**: `/api/v1/requests/handle`
- **Request Body**:
  ```json
  {
    "request_id": "integer",
    "action": "string" // 'accept' or 'reject'
  }
  ```

### 2.6 删除联系人
- **Description**: 从好友列表中删除一个用户。
- **Method**: `DELETE`
- **Path**: `/api/v1/contacts/{userId}`

---

## 3. 消息 (Messages)

### 3.1 发送消息
- **Description**: 向指定用户发送一条消息。
- **Method**: `POST`
- **Path**: `/api/v1/messages`
- **Request Body**:
  ```json
  {
    "to_user_id": "integer",
    "content": "string",
    "encrypted": "boolean"
  }
  ```

### 3.2 获取消息历史
- **Description**: 获取与指定用户的聊天记录。
- **Method**: `GET`
- **Path**: `/api/v1/messages/history/{userId}`

---

## 4. 文件上传 (File Uploads)

### 4.1 上传图片
- **Description**: 上传图片文件，用于聊天中发送。
- **Method**: `POST`
- **Path**: `/api/v1/upload/image`
- **Request Body**: `FormData` (包含文件)

### 4.2 上传普通文件
- **Description**: 上传非图片类文件。
- **Method**: `POST`
- **Path**: `/api/v1/upload/file`
- **Request Body**: `FormData` (包含文件)

---

## 5. 用户状态与心跳 (User Status & Heartbeat)

### 5.1 发送心跳
- **Description**: 客户端定时调用，以告知服务器自己仍在线。
- **Method**: `POST`
- **Path**: `/api/v1/user-status/heartbeat`
- **Request Body**:
  ```json
  {
    "timestamp": "string (datetime)"
  }
  ```

### 5.2 获取指定用户状态
- **Description**: 查询某个用户的在线状态。
- **Method**: `GET`
- **Path**: `/api/v1/user-status/{userId}`

---

## 6. WebRTC 信令 (WebRTC Signaling)

### 6.1 发送信令
- **Description**: 在P2P连接建立过程中，交换WebRTC信令消息。
- **Method**: `POST`
- **Paths**:
  - `/api/v1/signaling/offer` (Body: `{ "targetUserId": "integer", "offer": "..." }`)
  - `/api/v1/signaling/answer` (Body: `{ "targetUserId": "integer", "answer": "..." }`)
  - `/api/v1/signaling/ice-candidate` (Body: `{ "targetUserId": "integer", "candidate": "..." }`)

---

## 7. 用户头像 (Avatar)

### 7.1 上传头像
- **Description**: 为当前用户上传新的头像。
- **Method**: `POST`
- **Path**: `/api/v1/avatar/upload`
- **Request Body**: `FormData` (包含文件)

### 7.2 删除头像
- **Description**: 删除当前用户的头像。
- **Method**: `DELETE`
- **Path**: `/api/v1/avatar`

---

## 8. 用户个人资料 (User Profile)

### 8.1 获取个人资料
- **Description**: 获取当前用户或指定用户的详细个人资料。
- **Method**: `GET`
- **Paths**:
  - `/api/v1/profile` (获取自己的)
  - `/api/v1/profile/{userId}` (获取他人的)

### 8.2 创建/更新个人资料
- **Description**: 创建或更新当前用户的个人资料。
- **Method**: `POST` (创建), `PUT` (更新)
- **Path**: `/api/v1/profile`
- **Request Body**: `UserProfileCreate` / `UserProfileUpdate` schema。

---

## 9. 安全 (Security)

### 9.1 获取安全事件
- **Description**: 获取与当前用户相关的安全事件日志。
- **Method**: `GET`
- **Path**: `/api/v1/security/events` 