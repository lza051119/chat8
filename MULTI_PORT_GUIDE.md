# Chat8 多端口启动指南

## 概述

Chat8 现在支持同时在多个端口启动前端服务，允许用户在 8080、8081、8082 端口同时访问应用。这对于开发、测试或多用户场景非常有用。

## 功能特性

- ✅ 支持 8080、8081、8082 三个端口同时运行
- ✅ 智能端口检测：自动检测端口占用情况，使用可用端口启动服务
- ✅ 后端 CORS 已配置支持所有三个端口
- ✅ 每个端口独立运行，互不干扰
- ✅ 统一的后端 API 服务 (localhost:8000)
- ✅ 自动备用端口：当目标端口被占用时，自动寻找可用的替代端口
- ✅ 跨平台支持 (Linux/macOS/Windows)

## 启动方式

### 方式一：使用 npm 脚本

```bash
# 启动单个端口
npm run dev:8080  # 启动 8080 端口
npm run dev:8081  # 启动 8081 端口
npm run dev:8082  # 启动 8082 端口

# 启动所有端口 (Linux/macOS)
npm run dev:multi
npm run dev:smart  # 智能检测可用端口并启动服务（推荐）
```

### 方式二：使用启动脚本

#### 智能启动脚本（推荐）
```bash
# 给脚本添加执行权限（首次使用）
chmod +x start-smart-ports.sh

# 智能检测可用端口并启动服务
./start-smart-ports.sh
```

#### 固定端口启动脚本

**Linux/macOS:**
```bash
# 给脚本执行权限
chmod +x start-multi-ports.sh

# 启动所有端口
./start-multi-ports.sh
```

**Windows:**
```cmd
# 双击运行或在命令行执行
start-multi-ports.bat
```

### 方式三：手动启动

```bash
# 终端1
PORT=8080 npm run dev

# 终端2
PORT=8081 npm run dev

# 终端3
PORT=8082 npm run dev
```

## 访问地址

启动成功后，可以通过以下地址访问：

- **端口 8080**: http://localhost:8080
- **端口 8081**: http://localhost:8081
- **端口 8082**: http://localhost:8082

## 日志管理

使用启动脚本时，每个端口的日志会保存在 `logs/` 目录下：

```
logs/
├── port-8080.log
├── port-8081.log
└── port-8082.log
```

## 停止服务

### 使用启动脚本启动的服务
- **Linux/macOS**: 在启动脚本的终端按 `Ctrl+C`
- **Windows**: 关闭所有 Chat8 相关的命令行窗口

### 手动启动的服务
- 在每个终端窗口按 `Ctrl+C`

## 技术实现

### 前端配置

**文件**: `vite.config.js`
```javascript
server: {
  host: '0.0.0.0',
  port: process.env.PORT || 8080, // 支持环境变量指定端口
  // ... 其他配置
}
```

### 后端 CORS 配置

**文件**: `backend/app/main.py`
```python
origins = [
    "http://localhost:8080",
    "http://127.0.0.1:8080",
    "http://localhost:8081",
    "http://127.0.0.1:8081",
    "http://localhost:8082",
    "http://127.0.0.1:8082",
]
```

## 使用场景

1. **开发测试**: 同时测试不同版本或配置
2. **多用户演示**: 不同端口模拟不同用户
3. **负载测试**: 并发访问测试
4. **功能对比**: 同时运行不同分支的代码

## 注意事项

1. 确保后端服务 (localhost:8000) 已启动
2. 每个端口会占用系统资源，根据需要启动
3. 所有端口共享同一个后端数据库
4. WebSocket 连接会自动路由到正确的后端服务

## 故障排除

### 端口被占用
```bash
# 查看端口占用情况
lsof -i :8080
lsof -i :8081
lsof -i :8082

# 杀死占用端口的进程
kill -9 <PID>
```

### 权限问题 (Linux/macOS)
```bash
# 确保脚本有执行权限
chmod +x start-multi-ports.sh
```

### 日志查看
```bash
# 实时查看日志
tail -f logs/port-8080.log
tail -f logs/port-8081.log
tail -f logs/port-8082.log
```