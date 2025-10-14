# Chat8 Client

这是Chat8应用的客户端代码，提供端到端加密的聊天界面。

## 功能特性

- 现代化的Vue.js界面
- 端到端加密通信
- 实时消息传输
- 文件分享功能
- 视频通话支持
- 本地消息存储
- Signal协议加密

## 新功能：本地文件系统存储

最新版本的 Chat8 客户端支持将聊天数据存储在本地文件系统中，而不是浏览器的 IndexedDB 中。这有以下优势：

1. **持久性存储**：数据存储在用户数据目录，即使清除浏览器缓存也不会丢失
2. **更好的隐私**：数据不受浏览器管理，更加安全
3. **跨会话访问**：即使在不同的浏览器会话中，也能访问相同的数据

数据存储路径：`%APPDATA%\chat8-client\chat8-data\user_{userId}\`（Windows）或 `~/Library/Application Support/chat8-client/chat8-data/user_{userId}/`（macOS）

## 环境要求

- Node.js 16+
- npm 或 yarn

## 安装和运行

### 1. 安装依赖

```bash
cd frontend
npm install
```

### 2. 配置服务器地址

编辑 `frontend/src/config/config.js` 文件，设置服务器地址：

```javascript
export const API_BASE_URL = 'http://your-server-ip:8000'
export const WS_BASE_URL = 'ws://your-server-ip:8000'
```

### 3. 构建Signal库

```bash
cd libsignal
cargo build --release
```

### 4. 启动开发服务器

```bash
cd frontend
npm run dev
```

客户端将在 `http://localhost:5173` 启动。

## 生产环境部署

### 1. 构建生产版本

```bash
cd frontend
npm run build
```

### 2. 使用Nginx部署

```nginx
server {
    listen 80;
    server_name your-domain.com;
    
    location / {
        root /path/to/chat8-client/frontend/dist;
        try_files $uri $uri/ /index.html;
    }
    
    # 代理API请求到服务器
    location /api/ {
        proxy_pass http://your-server-ip:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }
    
    # 代理WebSocket连接
    location /ws {
        proxy_pass http://your-server-ip:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### 3. Docker部署

```bash
cd frontend
docker build -t chat8-client .
docker run -p 80:80 chat8-client
```

## 配置说明

### 服务器连接

在 `frontend/src/config/config.js` 中配置：

```javascript
// 开发环境
export const API_BASE_URL = 'http://localhost:8000'
export const WS_BASE_URL = 'ws://localhost:8000'

// 生产环境
export const API_BASE_URL = 'https://your-server.com'
export const WS_BASE_URL = 'wss://your-server.com'
```

### 加密设置

客户端使用Signal协议进行端到端加密，无需额外配置。

## 安全特性

### 端到端加密

- 使用Signal协议
- 消息在客户端加密，服务器无法解密
- 支持前向安全性
- 自动密钥轮换

### 本地存储

- 消息本地加密存储
- 密钥安全管理
- 自动清理过期数据

## 开发说明

### 项目结构

```
frontend/
├── src/
│   ├── components/     # Vue组件
│   ├── views/         # 页面视图
│   ├── services/      # API服务
│   ├── store/         # 状态管理
│   ├── utils/         # 工具函数
│   ├── client_db/     # 本地数据库
│   └── config/        # 配置文件
├── public/            # 静态资源
└── dist/             # 构建输出
```

### 主要依赖

- Vue.js 3 - 前端框架
- Vite - 构建工具
- Pinia - 状态管理
- Vue Router - 路由管理
- Axios - HTTP客户端
- Socket.io - WebSocket通信

## 故障排除

### 常见问题

1. **无法连接服务器**：检查服务器地址配置
2. **加密失败**：确保libsignal库正确编译
3. **消息发送失败**：检查WebSocket连接状态
4. **文件上传失败**：检查文件大小限制

### 调试模式

在开发环境中，可以在浏览器控制台查看详细日志：

```javascript
// 启用调试模式
localStorage.setItem('debug', 'true')
```

## 性能优化

- 启用代码分割
- 使用CDN加速
- 压缩静态资源
- 启用浏览器缓存
- 优化图片资源