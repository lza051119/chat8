# Chat8 部署指南

本文档提供了 Chat8 项目的详细部署指南，包括开发环境、生产环境和 Docker 部署等多种方式。

## 目录

- [快速开始](#快速开始)
- [开发环境部署](#开发环境部署)
- [生产环境部署](#生产环境部署)
- [Docker 部署](#docker-部署)
- [Nginx 配置](#nginx-配置)
- [SSL 证书配置](#ssl-证书配置)
- [环境变量配置](#环境变量配置)
- [故障排除](#故障排除)

## 快速开始

### 一键开发环境设置

```bash
# 克隆项目
git clone <repository-url>
cd chat8

# 运行开发环境设置脚本
./scripts/setup-dev.sh

# 启动开发服务器
./scripts/start.sh
```

### 一键 Docker 部署

```bash
# 启动 Docker 环境
./scripts/docker-start.sh

# 停止 Docker 环境
./scripts/docker-stop.sh
```

## 开发环境部署

### 系统要求

- **Node.js**: 18.0+ (推荐 LTS 版本)
- **Python**: 3.8+ (推荐 3.11+)
- **npm**: 8.0+
- **pip**: 21.0+

### 手动设置步骤

#### 1. 环境准备

```bash
# 创建项目目录结构
mkdir -p data/{database,uploads,logs,local_storage}
mkdir -p deployment/ssl

# 复制环境变量文件
cp .env.example .env
cp backend/.env.example backend/.env
```

#### 2. 前端设置

```bash
cd frontend

# 安装依赖
npm install

# 启动开发服务器
npm run dev
```

#### 3. 后端设置

```bash
cd backend

# 创建虚拟环境（推荐）
python3 -m venv venv
source venv/bin/activate  # Linux/macOS
# 或 venv\Scripts\activate  # Windows

# 安装依赖
pip install -r requirements.txt

# 初始化数据库
python app/init_db.py

# 启动开发服务器
python -m uvicorn app.main:app --reload
```

#### 4. 访问应用

- 前端应用: http://localhost:8080
- 后端 API: http://localhost:8000
- API 文档: http://localhost:8000/docs

## 生产环境部署

### 系统要求

- **操作系统**: Ubuntu 20.04+ / CentOS 8+ / RHEL 8+
- **内存**: 2GB+ (推荐 4GB+)
- **存储**: 10GB+ 可用空间
- **网络**: 公网 IP 或域名

### 部署步骤

#### 1. 服务器准备

```bash
# 更新系统
sudo apt update && sudo apt upgrade -y

# 安装必要软件
sudo apt install -y nginx python3 python3-pip nodejs npm git

# 安装 PM2（进程管理器）
sudo npm install -g pm2
```

#### 2. 项目部署

```bash
# 克隆项目到服务器
git clone <repository-url> /var/www/chat8
cd /var/www/chat8

# 运行生产构建脚本
./scripts/build.sh

# 设置权限
sudo chown -R www-data:www-data /var/www/chat8
sudo chmod -R 755 /var/www/chat8
```

#### 3. 配置环境变量

```bash
# 编辑生产环境配置
sudo nano .env
sudo nano backend/.env

# 设置生产环境变量
export NODE_ENV=production
export PYTHON_ENV=production
```

#### 4. 启动服务

```bash
# 启动后端服务
cd backend
pm2 start "python -m uvicorn app.main:app --host 0.0.0.0 --port 8000" --name chat8-backend

# 启动前端服务（如果需要）
cd ../frontend
pm2 serve dist 8080 --name chat8-frontend

# 保存 PM2 配置
pm2 save
pm2 startup
```

#### 5. 配置 Nginx

```bash
# 复制 Nginx 配置
sudo cp deployment/nginx/nginx.conf /etc/nginx/sites-available/chat8
sudo ln -s /etc/nginx/sites-available/chat8 /etc/nginx/sites-enabled/

# 测试配置
sudo nginx -t

# 重启 Nginx
sudo systemctl restart nginx
```

## Docker 部署

### 系统要求

- **Docker**: 20.0+
- **Docker Compose**: 2.0+

### 部署步骤

#### 1. 安装 Docker

```bash
# Ubuntu/Debian
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER

# 安装 Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
```

#### 2. 配置环境

```bash
# 复制环境变量文件
cp .env.example .env
cp backend/.env.example backend/.env

# 编辑配置文件
nano .env
nano backend/.env
```

#### 3. 启动服务

```bash
# 使用脚本启动
./scripts/docker-start.sh

# 或手动启动
docker-compose up -d
```

#### 4. 管理服务

```bash
# 查看服务状态
docker-compose ps

# 查看日志
docker-compose logs -f

# 停止服务
./scripts/docker-stop.sh

# 重启服务
docker-compose restart
```

## Nginx 配置

### 基本配置

项目提供了两个 Nginx 配置文件：

1. `frontend/nginx.conf` - 前端容器内的 Nginx 配置
2. `deployment/nginx/nginx.conf` - 反向代理配置

### 自定义域名

编辑 `deployment/nginx/nginx.conf`：

```nginx
server {
    listen 443 ssl http2;
    server_name your-domain.com;  # 替换为您的域名
    
    # SSL 配置
    ssl_certificate /etc/nginx/ssl/your-domain.crt;
    ssl_certificate_key /etc/nginx/ssl/your-domain.key;
    
    # 其他配置...
}
```

## SSL 证书配置

### 使用 Let's Encrypt

```bash
# 安装 Certbot
sudo apt install certbot python3-certbot-nginx

# 获取证书
sudo certbot --nginx -d your-domain.com

# 自动续期
sudo crontab -e
# 添加以下行：
# 0 12 * * * /usr/bin/certbot renew --quiet
```

### 使用自签名证书（开发环境）

```bash
# 创建自签名证书
sudo mkdir -p /etc/nginx/ssl
sudo openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
    -keyout /etc/nginx/ssl/chat8.key \
    -out /etc/nginx/ssl/chat8.crt
```

## 环境变量配置

### 主要环境变量

#### 根目录 `.env`

```bash
# 应用配置
APP_NAME=Chat8
APP_VERSION=1.0.0
ENVIRONMENT=production

# 服务器配置
FRONTEND_PORT=8080
BACKEND_PORT=8000
NGINX_PORT=80
NGINX_SSL_PORT=443

# 域名配置
DOMAIN=your-domain.com
```

#### 后端 `backend/.env`

```bash
# 数据库配置
DATABASE_URL=sqlite:///./data/database/chat8.db

# 安全配置
SECRET_KEY=your-super-secret-key-change-this
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# CORS 配置
ALLOWED_ORIGINS=https://your-domain.com,http://localhost:8080

# 文件上传配置
UPLOADS_DIR=./data/uploads
MAX_FILE_SIZE=10485760
```

## 故障排除

### 常见问题

#### 1. 端口冲突

```bash
# 检查端口占用
sudo netstat -tlnp | grep :8000
sudo netstat -tlnp | grep :8080

# 杀死占用进程
sudo kill -9 <PID>
```

#### 2. 权限问题

```bash
# 设置正确权限
sudo chown -R $USER:$USER /path/to/chat8
sudo chmod -R 755 /path/to/chat8
```

#### 3. 数据库问题

```bash
# 重新初始化数据库
cd backend
python app/init_db.py
```

#### 4. Docker 问题

```bash
# 清理 Docker 资源
docker system prune -a

# 重新构建镜像
docker-compose build --no-cache
```

### 日志查看

```bash
# 应用日志
tail -f data/logs/app.log

# Nginx 日志
sudo tail -f /var/log/nginx/access.log
sudo tail -f /var/log/nginx/error.log

# Docker 日志
docker-compose logs -f

# PM2 日志
pm2 logs
```

### 性能监控

```bash
# 系统资源监控
htop
df -h
free -h

# PM2 监控
pm2 monit

# Docker 资源监控
docker stats
```

## 备份和恢复

### 数据备份

```bash
# 备份数据库
cp data/database/chat8.db data/database/chat8.db.backup.$(date +%Y%m%d_%H%M%S)

# 备份上传文件
tar -czf uploads_backup_$(date +%Y%m%d_%H%M%S).tar.gz data/uploads/

# 备份配置文件
tar -czf config_backup_$(date +%Y%m%d_%H%M%S).tar.gz .env backend/.env
```

### 自动备份脚本

```bash
# 创建备份脚本
cat > scripts/backup.sh << 'EOF'
#!/bin/bash
BACKUP_DIR="/var/backups/chat8"
DATE=$(date +%Y%m%d_%H%M%S)

mkdir -p $BACKUP_DIR

# 备份数据库
cp data/database/chat8.db $BACKUP_DIR/chat8_$DATE.db

# 备份上传文件
tar -czf $BACKUP_DIR/uploads_$DATE.tar.gz data/uploads/

# 清理旧备份（保留7天）
find $BACKUP_DIR -name "*.db" -mtime +7 -delete
find $BACKUP_DIR -name "*.tar.gz" -mtime +7 -delete
EOF

chmod +x scripts/backup.sh

# 添加到 crontab
echo "0 2 * * * /var/www/chat8/scripts/backup.sh" | sudo crontab -
```

## 更新和维护

### 应用更新

```bash
# 拉取最新代码
git pull origin main

# 更新依赖
cd frontend && npm install
cd ../backend && pip install -r requirements.txt

# 重新构建
./scripts/build.sh

# 重启服务
pm2 restart all
# 或
docker-compose restart
```

### 系统维护

```bash
# 清理日志
sudo logrotate -f /etc/logrotate.conf

# 清理临时文件
sudo apt autoremove
sudo apt autoclean

# 更新系统
sudo apt update && sudo apt upgrade
```

---

如需更多帮助，请查看项目文档或提交 Issue。