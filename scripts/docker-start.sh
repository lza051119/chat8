#!/bin/bash

# Chat8 Docker 启动脚本
# 用于快速启动整个 Chat8 项目的 Docker 环境

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 日志函数
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 检查 Docker 和 Docker Compose
check_docker() {
    log_info "检查 Docker 环境..."
    
    if ! command -v docker &> /dev/null; then
        log_error "Docker 未安装，请先安装 Docker"
        exit 1
    fi
    
    if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
        log_error "Docker Compose 未安装，请先安装 Docker Compose"
        exit 1
    fi
    
    if ! docker info &> /dev/null; then
        log_error "Docker 服务未启动，请启动 Docker 服务"
        exit 1
    fi
    
    log_success "Docker 环境检查通过"
}

# 创建必要的目录
create_directories() {
    log_info "创建必要的目录..."
    
    mkdir -p data/database
    mkdir -p data/uploads
    mkdir -p data/logs
    mkdir -p data/local_storage
    mkdir -p deployment/ssl
    
    log_success "目录创建完成"
}

# 检查环境变量文件
check_env_files() {
    log_info "检查环境变量文件..."
    
    if [ ! -f ".env" ]; then
        if [ -f ".env.example" ]; then
            log_warning ".env 文件不存在，从 .env.example 复制"
            cp .env.example .env
            log_warning "请编辑 .env 文件配置您的环境变量"
        else
            log_warning ".env 和 .env.example 文件都不存在"
        fi
    fi
    
    if [ ! -f "backend/.env" ]; then
        if [ -f "backend/.env.example" ]; then
            log_warning "backend/.env 文件不存在，从 backend/.env.example 复制"
            cp backend/.env.example backend/.env
            log_warning "请编辑 backend/.env 文件配置您的后端环境变量"
        fi
    fi
}

# 构建和启动服务
start_services() {
    log_info "构建和启动 Chat8 服务..."
    
    # 使用 docker-compose 或 docker compose
    if command -v docker-compose &> /dev/null; then
        DOCKER_COMPOSE="docker-compose"
    else
        DOCKER_COMPOSE="docker compose"
    fi
    
    # 构建镜像
    log_info "构建 Docker 镜像..."
    $DOCKER_COMPOSE build
    
    # 启动服务
    log_info "启动服务..."
    $DOCKER_COMPOSE up -d
    
    # 等待服务启动
    log_info "等待服务启动..."
    sleep 10
    
    # 检查服务状态
    log_info "检查服务状态..."
    $DOCKER_COMPOSE ps
}

# 显示访问信息
show_access_info() {
    log_success "Chat8 服务启动成功！"
    echo
    echo "访问信息："
    echo "  前端应用: http://localhost:8080"
    echo "  后端 API: http://localhost:8000"
    echo "  API 文档: http://localhost:8000/docs"
    echo "  Nginx 代理: http://localhost (如果启用)"
    echo
    echo "管理命令："
    echo "  查看日志: docker-compose logs -f"
    echo "  停止服务: docker-compose down"
    echo "  重启服务: docker-compose restart"
    echo "  查看状态: docker-compose ps"
    echo
}

# 主函数
main() {
    echo "=== Chat8 Docker 启动脚本 ==="
    echo
    
    # 切换到项目根目录
    cd "$(dirname "$0")/.."
    
    check_docker
    create_directories
    check_env_files
    start_services
    show_access_info
    
    log_success "启动完成！"
}

# 错误处理
trap 'log_error "脚本执行失败"' ERR

# 执行主函数
main "$@"