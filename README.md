# Secure Chat Vue

一个基于Vue 3的安全即时通信前端应用，提供端到端加密的聊天功能

## 🚀 特性

- 🔐 端到端加密通信
- 💬 实时聊天功能
- 👥 联系人管理
- 📞 语音通话支持
- 🎨 现代化UI设计
- 📱 响应式设计

## 🛠️ 技术栈

- **前端框架**: Vue 3
- **构建工具**: Vite
- **路由管理**: Vue Router 4
- **状态管理**: 自定义 hybrid-store
- **加密**: CryptoJS
- **HTTP客户端**: Axios

## 📁 项目结构

```
src/
├── api/           # 后端API请求封装
│   ├── hybrid-api.js
│   └── index.js
├── components/    # UI组件
│   ├── CallOverlay.vue
│   ├── ChatWindow.vue
│   ├── ContactList.vue
│   ├── HybridChatWindow.vue
│   ├── HybridContactList.vue
│   ├── HybridMessageInput.vue
│   ├── LoginRegister.vue
│   ├── MessageInput.vue
│   └── SecurityPanel.vue
├── views/         # 页面视图
│   ├── HybridChatMain.vue
│   ├── Login.vue
│   ├── Register.vue
│   └── Settings.vue
├── store/         # 状态管理
│   ├── hybrid-store.js
│   └── index.js
├── router/        # 路由配置
│   └── index.js
├── services/      # 服务层
│   └── HybridMessaging.js
├── App.vue        # 根组件
└── main.js        # 应用入口
```

## 🚀 快速开始

### 安装依赖

```bash
npm install
```

### 开发环境运行

```bash
npm run dev
```

### 构建生产版本

```bash
npm run build
```

### 预览生产版本

```bash
npm run preview
```

## 🔧 配置

1. 确保后端API服务正在运行
2. 在 `src/api/` 目录中配置API端点
3. 根据需要调整加密配置

## 📝 开发说明

- 所有需要后端API集成的地方已在代码中注释
- 使用Vue 3 Composition API
- 支持TypeScript（可选）
- 遵循Vue.js官方风格指南


