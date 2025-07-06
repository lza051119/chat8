# Chat8 Server Configuration

## 环境配置

### .env 文件配置

在 `backend/.env` 文件中配置以下参数：

```env
# 数据库配置
DATABASE_URL=sqlite:///./chat8.db

# JWT配置
SECRET_KEY=your-secret-key-here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# 服务器配置
HOST=0.0.0.0
PORT=8000
DEBUG=false

# CORS配置
ALLOWED_ORIGINS=["http://localhost:5173", "http://localhost:3000"]

# 文件上传配置
MAX_FILE_SIZE=10485760  # 10MB
UPLOAD_DIR=./static/uploads

# WebSocket配置
WS_HEARTBEAT_INTERVAL=30
WS_TIMEOUT=60
```

## 生产环境配置

### 1. 数据库配置

#### PostgreSQL
```env
DATABASE_URL=postgresql://username:password@localhost:5432/chat8
```

#### MySQL
```env
DATABASE_URL=mysql://username:password@localhost:3306/chat8
```

### 2. 安全配置

```env
# 生成强密钥
SECRET_KEY=$(openssl rand -hex 32)

# 禁用调试模式
DEBUG=false

# 配置允许的域名
ALLOWED_ORIGINS=["https://your-client-domain.com"]
```

### 3. 性能配置

```env
# 数据库连接池
DB_POOL_SIZE=20
DB_MAX_OVERFLOW=30

# 工作进程数
WORKERS=4

# 请求限制
RATE_LIMIT=100/minute
```

## Nginx反向代理配置

```nginx
server {
    listen 80;
    server_name your-server-domain.com;
    
    # 重定向到HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name your-server-domain.com;
    
    # SSL证书配置
    ssl_certificate /path/to/certificate.crt;
    ssl_certificate_key /path/to/private.key;
    
    # SSL安全配置
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512:ECDHE-RSA-AES256-GCM-SHA384:DHE-RSA-AES256-GCM-SHA384;
    ssl_prefer_server_ciphers off;
    
    # 代理到FastAPI应用
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
    
    # WebSocket代理
    location /ws {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
    
    # 静态文件
    location /static/ {
        alias /path/to/chat8-server/backend/static/;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
}
```

## Docker配置

### Dockerfile优化

```dockerfile
FROM python:3.11-slim

# 设置工作目录
WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# 复制依赖文件
COPY backend/requirements.txt .

# 安装Python依赖
RUN pip install --no-cache-dir -r requirements.txt

# 复制应用代码
COPY backend/ .

# 创建非root用户
RUN useradd --create-home --shell /bin/bash app \
    && chown -R app:app /app
USER app

# 暴露端口
EXPOSE 8000

# 启动命令
CMD ["python", "-m", "app.main"]
```

### docker-compose.yml

```yaml
version: '3.8'

services:
  chat8-server:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://postgres:password@db:5432/chat8
      - SECRET_KEY=${SECRET_KEY}
    depends_on:
      - db
    volumes:
      - ./uploads:/app/static/uploads
    restart: unless-stopped

  db:
    image: postgres:15
    environment:
      - POSTGRES_DB=chat8
      - POSTGRES_USER=postgres
      - POSTGRES_PASSWORD=password
    volumes:
      - postgres_data:/var/lib/postgresql/data
    restart: unless-stopped

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./ssl:/etc/nginx/ssl
    depends_on:
      - chat8-server
    restart: unless-stopped

volumes:
  postgres_data:
```

## 监控和日志

### 日志配置

```python
# logging_config.py
import logging
from logging.handlers import RotatingFileHandler

def setup_logging():
    # 创建日志格式
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # 文件处理器
    file_handler = RotatingFileHandler(
        'logs/chat8.log', maxBytes=10485760, backupCount=5
    )
    file_handler.setFormatter(formatter)
    file_handler.setLevel(logging.INFO)
    
    # 控制台处理器
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    console_handler.setLevel(logging.INFO)
    
    # 配置根日志器
    logging.basicConfig(
        level=logging.INFO,
        handlers=[file_handler, console_handler]
    )
```

### 健康检查

```python
# health_check.py
from fastapi import APIRouter

router = APIRouter()

@router.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat()
    }
```

## 备份策略

### 数据库备份

```bash
#!/bin/bash
# backup.sh

DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/backups"
DB_NAME="chat8"

# PostgreSQL备份
pg_dump $DB_NAME > $BACKUP_DIR/chat8_$DATE.sql

# 压缩备份文件
gzip $BACKUP_DIR/chat8_$DATE.sql

# 删除7天前的备份
find $BACKUP_DIR -name "chat8_*.sql.gz" -mtime +7 -delete
```

### 文件备份

```bash
#!/bin/bash
# backup_files.sh

DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/backups"
UPLOAD_DIR="/app/static/uploads"

# 备份上传文件
tar -czf $BACKUP_DIR/uploads_$DATE.tar.gz $UPLOAD_DIR

# 删除30天前的文件备份
find $BACKUP_DIR -name "uploads_*.tar.gz" -mtime +30 -delete
```