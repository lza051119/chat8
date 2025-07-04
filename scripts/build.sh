#!/bin/bash

# Chat8 项目构建脚本
# 用于构建生产环境版本

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 项目根目录
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
FRONTEND_DIR="$PROJECT_ROOT/frontend"
BACKEND_DIR="$PROJECT_ROOT/backend"
BUILD_DIR="$PROJECT_ROOT/build"

echo -e "${BLUE}=== Chat8 项目构建脚本 ===${NC}"
echo -e "${BLUE}项目根目录: $PROJECT_ROOT${NC}"
echo

# 清理构建目录
clean_build() {
    echo -e "${YELLOW}清理构建目录...${NC}"
    rm -rf "$BUILD_DIR"
    mkdir -p "$BUILD_DIR"
}

# 构建前端
build_frontend() {
    echo -e "${YELLOW}构建前端...${NC}"
    cd "$FRONTEND_DIR"
    
    # 安装依赖
    if [ ! -d "node_modules" ]; then
        echo -e "${YELLOW}安装前端依赖...${NC}"
        npm install
    fi
    
    # 构建
    npm run build
    
    # 复制构建结果
    cp -r dist/* "$BUILD_DIR/"
    
    echo -e "${GREEN}前端构建完成${NC}"
}

# 准备后端
prepare_backend() {
    echo -e "${YELLOW}准备后端文件...${NC}"
    
    # 创建后端目录
    mkdir -p "$BUILD_DIR/backend"
    
    # 复制后端代码
    cp -r "$BACKEND_DIR/app" "$BUILD_DIR/backend/"
    cp "$BACKEND_DIR/requirements.txt" "$BUILD_DIR/backend/"
    cp "$BACKEND_DIR/.env.example" "$BUILD_DIR/backend/"
    
    # 创建启动脚本
    cat > "$BUILD_DIR/backend/start.sh" << 'EOF'
#!/bin/bash

# 后端启动脚本
set -e

echo "启动 Chat8 后端服务..."

# 检查虚拟环境
if [ ! -d "venv" ]; then
    echo "创建Python虚拟环境..."
    python3 -m venv venv
fi

# 激活虚拟环境
source venv/bin/activate

# 安装依赖
echo "安装依赖..."
pip install -r requirements.txt

# 初始化数据库
echo "初始化数据库..."
cd app
python init_db.py
cd ..

# 启动服务
echo "启动服务..."
python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000
EOF
    
    chmod +x "$BUILD_DIR/backend/start.sh"
    
    echo -e "${GREEN}后端准备完成${NC}"
}

# 创建部署文档
create_deploy_docs() {
    echo -e "${YELLOW}创建部署文档...${NC}"
    
    cat > "$BUILD_DIR/README.md" << 'EOF'
# Chat8 生产环境部署

## 系统要求

- Node.js 16+
- Python 3.8+
- Nginx (推荐)

## 部署步骤

### 1. 后端部署

```bash
cd backend

# 复制环境变量配置
cp .env.example .env

# 编辑环境变量
vim .env

# 启动后端服务
./start.sh
```

### 2. 前端部署

前端已构建为静态文件，可以直接使用 Nginx 或其他 Web 服务器托管。

#### Nginx 配置示例

```nginx
server {
    listen 80;
    server_name your-domain.com;
    
    # 前端静态文件
    location / {
        root /path/to/chat8/build;
        try_files $uri $uri/ /index.html;
    }
    
    # 后端 API 代理
    location /api {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
    
    # WebSocket 代理
    location /ws {
        proxy_pass http://localhost:8000;
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

### 3. 环境变量配置

重要的环境变量：

- `SECRET_KEY`: 生产环境密钥（必须修改）
- `DATABASE_URL`: 数据库连接字符串
- `ALLOWED_ORIGINS`: 允许的前端域名
- `MAIL_*`: 邮件服务配置（如需要）

### 4. 安全建议

- 使用 HTTPS
- 配置防火墙
- 定期备份数据库
- 监控日志文件
- 使用强密码和密钥

### 5. 维护

- 日志文件位置: `../data/logs/`
- 数据库文件位置: `../data/database/`
- 上传文件位置: `../data/uploads/`

EOF
    
    echo -e "${GREEN}部署文档创建完成${NC}"
}

# 创建版本信息
create_version_info() {
    echo -e "${YELLOW}创建版本信息...${NC}"
    
    cat > "$BUILD_DIR/version.json" << EOF
{
    "name": "Chat8",
    "version": "1.0.0",
    "build_time": "$(date -u +"%Y-%m-%dT%H:%M:%SZ")",
    "git_commit": "$(git rev-parse HEAD 2>/dev/null || echo 'unknown')",
    "git_branch": "$(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo 'unknown')",
    "build_environment": "production"
}
EOF
    
    echo -e "${GREEN}版本信息创建完成${NC}"
}

# 显示构建结果
show_build_info() {
    echo
    echo -e "${BLUE}=== 构建完成 ===${NC}"
    echo -e "${GREEN}构建目录: $BUILD_DIR${NC}"
    echo -e "${GREEN}构建大小: $(du -sh "$BUILD_DIR" | cut -f1)${NC}"
    echo
    echo -e "${YELLOW}部署说明:${NC}"
    echo -e "${YELLOW}1. 将构建目录复制到服务器${NC}"
    echo -e "${YELLOW}2. 配置环境变量${NC}"
    echo -e "${YELLOW}3. 启动后端服务${NC}"
    echo -e "${YELLOW}4. 配置 Web 服务器${NC}"
    echo
    echo -e "${GREEN}详细说明请查看: $BUILD_DIR/README.md${NC}"
}

# 主执行流程
main() {
    clean_build
    build_frontend
    prepare_backend
    create_deploy_docs
    create_version_info
    show_build_info
}

# 执行主函数
main