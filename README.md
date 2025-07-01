# Chat8 - 安全即时通信应用

一个基于Vue 3前端和FastAPI后端的全栈安全即时通信应用，提供端到端加密的聊天功能。

## 🚀 特性

- 🔐 端到端加密通信
- 💬 实时聊天功能
- 👥 联系人管理
- 📞 语音通话支持（WebRTC）
- 🎨 现代化UI设计
- 📱 响应式设计
- 🔄 WebSocket实时通信
- 🗄️ SQLite数据库存储

## 🛠️ 技术栈

### 前端
- **前端框架**: Vue 3
- **构建工具**: Vite
- **路由管理**: Vue Router 4
- **状态管理**: 自定义 hybrid-store
- **加密**: CryptoJS
- **HTTP客户端**: Axios

### 后端
- **后端框架**: FastAPI
- **数据库**: SQLite
- **WebSocket**: FastAPI WebSocket
- **认证**: JWT Token
- **加密**: RSA公钥加密

## 📁 项目结构

```
├── src/                    # 前端源码
│   ├── api/               # 后端API请求封装
│   ├── components/        # UI组件
│   ├── views/             # 页面视图
│   ├── store/             # 状态管理
│   ├── router/            # 路由配置
│   └── services/          # 服务层
├── backend/               # 后端源码
│   ├── app/
│   │   ├── api/          # API路由
│   │   ├── core/         # 核心配置
│   │   ├── db/           # 数据库模型
│   │   ├── schemas/      # Pydantic模式
│   │   ├── services/     # 业务逻辑
│   │   ├── websocket/    # WebSocket处理
│   │   └── main.py       # 应用入口
│   └── requirements.txt   # Python依赖
└── Postman_test_result.md # API测试结果
```

## 🚀 快速开始

### 前端开发

```bash
# 安装依赖
npm install

# 开发环境运行
npm run dev

# 构建生产版本
npm run build
```

### 后端开发

```bash
# 进入后端目录
cd backend

# 安装Python依赖
pip install -r requirements.txt

# 初始化数据库
cd app
python init_db.py

# 启动后端服务
python main.py
```

## 🔧 后端API状态

**已初步完成所有后端API，但完成测试的仅有** *认证相关API (authAPI)、联系人相关API (contactAPI)、消息相关API (messageAPI)*，**剩余部分会继续开展测试，测试结果保存至`Postman_test_result.md`**

### 功能增强

##### 1. 联系人和消息接口支持分页
* `/api/contacts` 支持 `page` 和 `limit` 分页参数
* `/api/messages/history/{userId}` 也支持分页

##### 2. 密钥指纹校验接口
* 增加了 `/api/keys/verify-fingerprint`，用于校验公钥指纹

##### 3. WebSocket事件类型丰富
- 打字通知（`typing_start/typing_stop`）
- 截图提醒（`screenshot_alert`）
- WebRTC信令细分（`webrtc_offer/webrtc_answer/webrtc_ice_candidate`）

##### 4. 错误处理健全
- FastAPI全局异常处理，详细的参数校验错误返回

##### 5. 参数灵活性增强
- `/api/keys/public` 和 `/api/presence/contacts` 支持多种参数模式

## 📝 开发说明

- 前端使用Vue 3 Composition API
- 后端遵循FastAPI最佳实践
- 支持端到端加密通信
- WebSocket实时消息推送
- 完整的用户认证和授权系统
