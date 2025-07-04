# Chat8 - 安全即时通信应用

一个基于Vue 3前端和FastAPI后端的全栈安全即时通信应用，采用混合架构设计，支持P2P直连和服务器转发两种传输方式，提供端到端加密的聊天功能。

## ✨ 核心特性

### 🔐 安全特性
- **端到端加密**: 使用RSA公钥加密和AES对称加密
- **密钥管理**: 自动密钥生成、交换和验证
- **隐写术支持**: 图片隐写功能，隐藏敏感信息
- **安全认证**: JWT Token认证机制

### 🌐 混合架构
- **P2P直连**: 在线用户间自动建立点对点连接
- **服务器转发**: 离线或P2P失败时自动切换到服务器转发
- **智能切换**: 根据网络状况自动选择最优传输方式
- **连接统计**: 实时显示P2P连接数量和传输效率

### 💬 通信功能
- **实时聊天**: WebSocket实时消息推送
- **语音通话**: WebRTC语音通话支持
- **视频通话**: WebRTC视频通话功能
- **文件传输**: 支持图片和文件发送
- **消息状态**: 已读/未读状态跟踪

### 👥 用户管理
- **联系人管理**: 添加、删除、搜索联系人
- **好友申请**: 好友请求发送和处理
- **用户状态**: 在线/离线状态显示
- **用户资料**: 头像上传和个人信息管理

### 🎨 用户界面
- **现代化设计**: 美观的彩色花体字标题和渐变背景
- **响应式布局**: 适配不同屏幕尺寸
- **实时统计**: 连接和消息传输统计面板
- **状态指示**: 连接状态和传输方式实时显示

## 🛠️ 技术栈

### 前端技术
- **框架**: Vue 3 (Composition API)
- **构建工具**: Vite 6.0
- **路由**: Vue Router 4
- **状态管理**: Vuex 4 + 自定义 hybrid-store
- **HTTP客户端**: Axios
- **加密库**: CryptoJS
- **本地存储**: Dexie (IndexedDB)
- **UI组件**: 自定义组件库

### 后端技术
- **框架**: FastAPI 0.115
- **ASGI服务器**: Uvicorn 0.35
- **数据库**: SQLite + SQLAlchemy 2.0
- **WebSocket**: FastAPI WebSocket + Socket.IO
- **认证**: JWT + PassLib
- **加密**: Cryptography + PyJWT
- **文件处理**: Pillow
- **邮件服务**: FastAPI-Mail

### 开发工具
- **包管理**: npm (前端) + pip (后端)
- **代码规范**: ESLint + Prettier
- **版本控制**: Git
- **API测试**: Postman

## 📁 项目结构

```
chat8/
├── README.md                    # 项目说明文档
├── .env.example                 # 环境变量示例
├── .gitignore                   # Git忽略文件
├── PROJECT_STRUCTURE.md         # 项目重构说明
├── frontend/                    # 前端代码
│   ├── src/                    # 前端源码
│   │   ├── api/                # API请求封装
│   │   │   ├── hybrid-api.js   # 混合架构API
│   │   │   └── index.js        # 基础API配置
│   │   ├── components/         # Vue组件
│   │   │   ├── hybridchatwindow.vue # 混合聊天窗口
│   │   │   ├── hybridcontactlist.vue # 联系人列表
│   │   │   ├── VideoCall.vue   # 视频通话
│   │   │   └── ...
│   │   ├── views/              # 页面视图
│   │   │   ├── hybridchatmain.vue # 主聊天界面
│   │   │   ├── login.vue       # 登录页面
│   │   │   └── ...
│   │   ├── services/           # 服务层
│   │   ├── store/              # 状态管理
│   │   ├── utils/              # 工具函数
│   │   ├── client_db/          # 客户端数据库
│   │   └── router/             # 路由配置
│   ├── public/                 # 静态资源
│   ├── package.json            # 前端依赖配置
│   ├── vite.config.js          # Vite构建配置
│   └── jsconfig.json           # JavaScript配置
├── backend/                     # 后端代码
│   ├── app/                    # 应用代码
│   │   ├── api/v1/endpoints/   # API端点
│   │   │   ├── auth.py         # 认证API
│   │   │   ├── messages.py     # 消息API
│   │   │   ├── friends.py      # 好友API
│   │   │   └── ...
│   │   ├── core/               # 核心配置
│   │   ├── db/                 # 数据库模型
│   │   ├── services/           # 业务逻辑
│   │   ├── websocket/          # WebSocket处理
│   │   └── main.py             # 应用入口
│   ├── requirements.txt        # Python依赖
│   └── .env.example            # 后端环境变量示例
├── data/                        # 数据目录
│   ├── database/               # 数据库文件
│   │   ├── chat8.db           # 主数据库
│   │   └── *.backup           # 数据库备份
│   ├── uploads/                # 上传文件
│   │   ├── static/            # 静态文件
│   │   ├── avatars/           # 用户头像
│   │   ├── images/            # 图片文件
│   │   └── files/             # 其他文件
│   ├── local_storage/          # 本地存储
│   │   └── messages/          # 消息数据库
│   └── logs/                   # 日志文件
├── scripts/                     # 项目脚本
│   ├── start.sh               # 统一启动脚本
│   ├── build.sh               # 构建脚本
│   ├── start-multi-ports.sh   # 多端口启动
│   └── start-smart-ports.sh   # 智能端口启动
├── docs/                        # 项目文档
└── deployment/                  # 部署配置
    ├── nginx/                  # Nginx配置
    ├── ssl/                    # SSL证书
    └── systemd/                # 系统服务配置
```

## 🚀 快速开始

### 环境要求
- **Node.js**: 18.0+ (推荐 LTS 版本)
- **Python**: 3.8+ (推荐 3.11+)
- **npm**: 8.0+
- **pip**: 21.0+
- **Docker**: 20.0+ (可选，用于容器化部署)
- **Docker Compose**: 2.0+ (可选)
- **Git**: 2.0+

### 🚀 一键开发环境设置（推荐）

使用开发环境设置脚本，自动配置整个开发环境：

```bash
# 克隆项目
git clone <repository-url>
cd chat8

# 设置开发环境
./scripts/setup-dev.sh

# 启动开发服务器
./scripts/start.sh
```

### 🐳 Docker 一键部署（推荐）

使用 Docker 进行快速部署，无需手动配置环境：

```bash
# 启动 Docker 环境
./scripts/docker-start.sh

# 停止 Docker 环境
./scripts/docker-stop.sh

# 查看服务状态
./scripts/docker-status.sh
```

启动脚本会自动：
- 检查依赖环境
- 安装前后端依赖
- 初始化数据库
- 启动前后端服务
- 显示访问地址

### 手动启动

#### 1. 前端设置
```bash
cd frontend

# 安装前端依赖
npm install

# 开发环境运行
npm run dev          # 默认端口8080
npm run dev:8081     # 端口8081
npm run dev:8082     # 端口8082

# 构建生产版本
npm run build
```

#### 2. 后端设置
```bash
cd backend

# 创建虚拟环境
python3 -m venv venv
source venv/bin/activate

# 安装Python依赖
pip install -r requirements.txt

# 初始化数据库
cd app
python init_db.py
cd ..

# 启动后端服务
python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

#### 3. 访问应用
- 前端: http://localhost:8080
- 后端API: http://localhost:8000
- API文档: http://localhost:8000/docs

## 📚 文档

- [部署指南](docs/DEPLOYMENT.md) - 详细的部署说明
- [API 文档](docs/API.md) - REST API 和 WebSocket 接口文档
- [项目结构](PROJECT_STRUCTURE.md) - 项目架构和目录说明

## 🛠️ 可用脚本

| 脚本 | 描述 |
|------|------|
| `scripts/setup-dev.sh` | 一键设置开发环境 |
| `scripts/start.sh` | 启动开发服务器 |
| `scripts/build.sh` | 生产环境构建 |
| `scripts/docker-start.sh` | 启动 Docker 环境 |
| `scripts/docker-stop.sh` | 停止 Docker 环境 |

## ⚙️ 配置说明

### 环境变量

项目使用环境变量进行配置，主要配置文件：

- `.env` - 主配置文件
- `backend/.env` - 后端专用配置

复制示例配置文件：
```bash
cp .env.example .env
cp backend/.env.example backend/.env
```

创建 `.env` 文件在后端目录：
```env
# 数据库配置
DATABASE_URL=sqlite:///./chat8.db

# JWT配置
SECRET_KEY=your-secret-key
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# 邮件配置 (可选)
MAIL_USERNAME=your-email@example.com
MAIL_PASSWORD=your-password
MAIL_FROM=your-email@example.com
MAIL_PORT=587
MAIL_SERVER=smtp.example.com
```

### 端口配置
- 前端默认端口: 8080
- 后端默认端口: 8000
- WebSocket 连接: 8000/ws
- Nginx 代理: 80/443 (生产环境)
- 支持多端口同时运行
- 自动端口冲突检测和切换

### 数据库

项目使用 SQLite 数据库，数据库文件位于 `data/database/chat8.db`。

首次运行时会自动创建数据库表结构。

## 📱 功能使用

### 用户注册和登录
1. 访问应用首页
2. 点击"注册"创建新账户
3. 使用用户名和密码登录

### 添加联系人
1. 在聊天界面点击添加联系人按钮
2. 输入对方用户名发送好友申请
3. 等待对方接受申请

### 开始聊天
1. 在联系人列表选择联系人
2. 在聊天窗口输入消息
3. 系统自动选择P2P或服务器转发
4. 查看连接统计了解传输方式

### 语音/视频通话
1. 在聊天界面点击通话按钮
2. 选择语音或视频通话
3. 等待对方接听

### 文件传输
1. 点击聊天输入框的附件按钮
2. 选择要发送的文件
3. 文件将通过当前连接方式传输

## 🔒 安全机制

### 加密流程
1. **密钥生成**: 用户注册时自动生成RSA密钥对
2. **密钥交换**: 添加好友时交换公钥
3. **消息加密**: 使用AES加密消息内容
4. **密钥加密**: 使用RSA加密AES密钥
5. **传输安全**: 所有数据传输均加密

### 隐私保护
- 消息端到端加密，服务器无法解密
- 本地数据库加密存储
- 密钥本地生成和管理
- 支持消息自毁功能

## 🧪 开发和测试

### API测试
- 所有后端API已通过完整测试
- 使用Postman进行API测试
- 支持自动化测试脚本

### 开发模式
```bash
# 前端热重载开发
npm run dev

# 后端热重载开发
uvicorn main:app --reload

# 同时启动前后端
./start-smart-ports.sh
```

### 调试功能
- 浏览器开发者工具
- Vue DevTools支持
- 后端日志输出
- WebSocket连接监控

## 📊 性能特性

### 混合架构优势
- **低延迟**: P2P直连减少服务器中转延迟
- **高可靠**: 服务器转发保证消息必达
- **负载均衡**: 减轻服务器压力
- **智能切换**: 根据网络状况自动优化

### 优化措施
- 消息分页加载
- 图片懒加载
- 连接池管理
- 内存缓存优化

## 🤝 贡献指南

### 开发规范
1. 遵循Vue 3 Composition API最佳实践
2. 使用TypeScript类型注解
3. 遵循ESLint代码规范
4. 编写单元测试
5. 提交前运行测试

### 提交流程
1. Fork项目
2. 创建功能分支
3. 提交代码变更
4. 创建Pull Request
5. 代码审查和合并

## 📄 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

## 🆘 支持和反馈

如果您在使用过程中遇到问题或有改进建议，请：

1. 查看文档和FAQ
2. 搜索已有的Issues
3. 创建新的Issue描述问题
4. 联系开发团队

---

**Whisper** - 让安全通信变得简单而优雅 🚀
