# Chat8 Server

这是Chat8应用的服务器端代码，可以独立部署在服务器上。

## 功能特性

- RESTful API接口
- WebSocket实时通信
- 用户认证和管理
- 消息路由和临时存储
- 文件上传和管理
- 纯中转服务，不处理加密内容

## 环境要求

- Python 3.8+
- SQLite 数据库

## 安装和运行

### 1. 安装依赖

```bash
cd backend
pip install -r requirements.txt
```

### 2. 配置环境变量

复制 `.env.example` 为 `.env` 并配置相关参数：

```bash
cp .env.example .env
```

### 3. 初始化数据库

```bash
python -m app.init_db
```

### 4. 启动服务器

```bash
python -m app.main
```

服务器将在 `http://localhost:8000` 启动。

## API文档

启动服务器后，可以访问以下地址查看API文档：

- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## Docker部署

```bash
docker build -t chat8-server .
docker run -p 8000:8000 chat8-server
```

## 配置说明

### 跨域设置

如果客户端部署在不同的域名或端口，需要在 `app/core/config.py` 中配置CORS设置。

### 数据库

默认使用SQLite数据库，生产环境建议使用PostgreSQL或MySQL。

## 安全注意事项

- 服务器不存储或处理明文消息内容
- 所有消息内容都是客户端加密的
- 定期备份数据库
- 使用HTTPS部署
- 配置适当的防火墙规则

## 监控和日志

服务器日志位于 `logs/` 目录下，包含：

- 访问日志
- 错误日志
- WebSocket连接日志

## 故障排除

### 常见问题

1. **端口被占用**：修改 `app/main.py` 中的端口配置
2. **数据库连接失败**：检查数据库文件权限
3. **CORS错误**：检查跨域配置

### 性能优化

- 使用反向代理（如Nginx）
- 配置数据库连接池
- 启用gzip压缩
- 使用CDN加速静态资源