#!/bin/bash

# Chat8 项目统一启动脚本
# 用于同时启动前端和后端服务

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

echo -e "${BLUE}=== Chat8 项目启动脚本 ===${NC}"
echo -e "${BLUE}项目根目录: $PROJECT_ROOT${NC}"
echo

# 检查依赖
check_dependencies() {
    echo -e "${YELLOW}检查依赖...${NC}"
    
    # 检查 Node.js
    if ! command -v node &> /dev/null; then
        echo -e "${RED}错误: Node.js 未安装${NC}"
        exit 1
    fi
    
    # 检查 Python
    if ! command -v python3 &> /dev/null; then
        echo -e "${RED}错误: Python3 未安装${NC}"
        exit 1
    fi
    
    # 检查 npm
    if ! command -v npm &> /dev/null; then
        echo -e "${RED}错误: npm 未安装${NC}"
        exit 1
    fi
    
    echo -e "${GREEN}依赖检查通过${NC}"
}

# 安装前端依赖
install_frontend_deps() {
    echo -e "${YELLOW}安装前端依赖...${NC}"
    cd "$FRONTEND_DIR"
    if [ ! -d "node_modules" ]; then
        npm install
    else
        echo -e "${GREEN}前端依赖已存在${NC}"
    fi
}

# 安装后端依赖
install_backend_deps() {
    echo -e "${YELLOW}安装后端依赖...${NC}"
    cd "$BACKEND_DIR"
    if [ ! -d "venv" ]; then
        echo -e "${YELLOW}创建Python虚拟环境...${NC}"
        python3 -m venv venv
    fi
    
    source venv/bin/activate
    pip install -r requirements.txt
}

# 初始化数据库
init_database() {
    echo -e "${YELLOW}初始化数据库...${NC}"
    cd "$BACKEND_DIR"
    source venv/bin/activate
    cd app
    python init_db.py
}

# 启动后端服务
start_backend() {
    echo -e "${YELLOW}启动后端服务...${NC}"
    cd "$BACKEND_DIR"
    source venv/bin/activate
    
    # 检查端口是否被占用
    if lsof -Pi :8000 -sTCP:LISTEN -t >/dev/null ; then
        echo -e "${YELLOW}端口 8000 已被占用，尝试终止现有进程...${NC}"
        pkill -f "uvicorn.*8000" || true
        sleep 2
    fi
    
    echo -e "${GREEN}后端服务启动中... (端口: 8000)${NC}"
    python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload &
    BACKEND_PID=$!
    echo "后端进程 PID: $BACKEND_PID"
}

# 启动前端服务
start_frontend() {
    echo -e "${YELLOW}启动前端服务...${NC}"
    cd "$FRONTEND_DIR"
    
    # 检查端口是否被占用
    if lsof -Pi :8080 -sTCP:LISTEN -t >/dev/null ; then
        echo -e "${YELLOW}端口 8080 已被占用，尝试使用端口 8081...${NC}"
        PORT=8081
    else
        PORT=8080
    fi
    
    echo -e "${GREEN}前端服务启动中... (端口: $PORT)${NC}"
    PORT=$PORT npm run dev &
    FRONTEND_PID=$!
    echo "前端进程 PID: $FRONTEND_PID"
}

# 等待服务启动
wait_for_services() {
    echo -e "${YELLOW}等待服务启动...${NC}"
    sleep 5
    
    # 检查后端是否启动成功
    if curl -s http://localhost:8000/api/ping > /dev/null; then
        echo -e "${GREEN}✓ 后端服务启动成功 (http://localhost:8000)${NC}"
    else
        echo -e "${RED}✗ 后端服务启动失败${NC}"
    fi
    
    # 检查前端是否启动成功
    if curl -s http://localhost:8080 > /dev/null || curl -s http://localhost:8081 > /dev/null; then
        echo -e "${GREEN}✓ 前端服务启动成功${NC}"
    else
        echo -e "${RED}✗ 前端服务启动失败${NC}"
    fi
}

# 显示服务信息
show_info() {
    echo
    echo -e "${BLUE}=== 服务信息 ===${NC}"
    echo -e "${GREEN}前端地址: http://localhost:8080 或 http://localhost:8081${NC}"
    echo -e "${GREEN}后端地址: http://localhost:8000${NC}"
    echo -e "${GREEN}API文档: http://localhost:8000/docs${NC}"
    echo
    echo -e "${YELLOW}按 Ctrl+C 停止所有服务${NC}"
}

# 清理函数
cleanup() {
    echo
    echo -e "${YELLOW}正在停止服务...${NC}"
    
    if [ ! -z "$BACKEND_PID" ]; then
        kill $BACKEND_PID 2>/dev/null || true
    fi
    
    if [ ! -z "$FRONTEND_PID" ]; then
        kill $FRONTEND_PID 2>/dev/null || true
    fi
    
    # 强制终止相关进程
    pkill -f "uvicorn.*8000" 2>/dev/null || true
    pkill -f "vite.*8080" 2>/dev/null || true
    pkill -f "vite.*8081" 2>/dev/null || true
    
    echo -e "${GREEN}服务已停止${NC}"
    exit 0
}

# 设置信号处理
trap cleanup SIGINT SIGTERM

# 主执行流程
main() {
    check_dependencies
    install_frontend_deps
    install_backend_deps
    init_database
    start_backend
    start_frontend
    wait_for_services
    show_info
    
    # 保持脚本运行
    while true; do
        sleep 1
    done
}

# 执行主函数
main