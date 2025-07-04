#!/bin/bash

# Chat8 开发环境设置脚本
# 用于快速设置 Chat8 项目的开发环境

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

# 检查系统要求
check_requirements() {
    log_info "检查系统要求..."
    
    # 检查 Node.js
    if ! command -v node &> /dev/null; then
        log_error "Node.js 未安装，请先安装 Node.js (推荐版本 18+)"
        exit 1
    fi
    
    NODE_VERSION=$(node --version | cut -d'v' -f2 | cut -d'.' -f1)
    if [ "$NODE_VERSION" -lt 16 ]; then
        log_warning "Node.js 版本过低 (当前: $(node --version))，推荐使用 18+"
    fi
    
    # 检查 npm
    if ! command -v npm &> /dev/null; then
        log_error "npm 未安装，请先安装 npm"
        exit 1
    fi
    
    # 检查 Python
    if ! command -v python3 &> /dev/null; then
        log_error "Python3 未安装，请先安装 Python3 (推荐版本 3.8+)"
        exit 1
    fi
    
    PYTHON_VERSION=$(python3 --version | cut -d' ' -f2 | cut -d'.' -f1,2)
    if [ "$(echo "$PYTHON_VERSION < 3.8" | bc -l 2>/dev/null || echo 1)" -eq 1 ]; then
        log_warning "Python 版本可能过低 (当前: $(python3 --version))，推荐使用 3.8+"
    fi
    
    # 检查 pip
    if ! command -v pip3 &> /dev/null; then
        log_error "pip3 未安装，请先安装 pip3"
        exit 1
    fi
    
    log_success "系统要求检查通过"
}

# 创建目录结构
create_directories() {
    log_info "创建项目目录结构..."
    
    mkdir -p data/database
    mkdir -p data/uploads
    mkdir -p data/logs
    mkdir -p data/local_storage
    mkdir -p deployment/ssl
    mkdir -p docs
    
    log_success "目录结构创建完成"
}

# 设置环境变量文件
setup_env_files() {
    log_info "设置环境变量文件..."
    
    # 根目录 .env 文件
    if [ ! -f ".env" ]; then
        if [ -f ".env.example" ]; then
            cp .env.example .env
            log_success "已创建 .env 文件"
        else
            log_warning ".env.example 文件不存在，跳过根目录 .env 创建"
        fi
    else
        log_info ".env 文件已存在"
    fi
    
    # 后端 .env 文件
    if [ ! -f "backend/.env" ]; then
        if [ -f "backend/.env.example" ]; then
            cp backend/.env.example backend/.env
            log_success "已创建 backend/.env 文件"
        else
            log_warning "backend/.env.example 文件不存在，跳过后端 .env 创建"
        fi
    else
        log_info "backend/.env 文件已存在"
    fi
}

# 安装前端依赖
install_frontend_deps() {
    log_info "安装前端依赖..."
    
    cd frontend
    
    if [ -f "package-lock.json" ]; then
        npm ci
    else
        npm install
    fi
    
    cd ..
    log_success "前端依赖安装完成"
}

# 安装后端依赖
install_backend_deps() {
    log_info "安装后端依赖..."
    
    cd backend
    
    # 创建虚拟环境（可选）
    if [ "$1" = "--venv" ]; then
        if [ ! -d "venv" ]; then
            log_info "创建 Python 虚拟环境..."
            python3 -m venv venv
        fi
        
        log_info "激活虚拟环境..."
        source venv/bin/activate
    fi
    
    # 安装依赖
    pip3 install -r requirements.txt
    
    cd ..
    log_success "后端依赖安装完成"
}

# 初始化数据库
init_database() {
    log_info "初始化数据库..."
    
    cd backend
    
    if [ -f "app/init_db.py" ]; then
        python3 app/init_db.py
        log_success "数据库初始化完成"
    else
        log_warning "数据库初始化脚本不存在，跳过数据库初始化"
    fi
    
    cd ..
}

# 显示完成信息
show_completion_info() {
    log_success "Chat8 开发环境设置完成！"
    echo
    echo "下一步操作："
    echo "  1. 编辑 .env 和 backend/.env 文件配置您的环境变量"
    echo "  2. 启动开发服务器："
    echo "     - 使用统一脚本: ./scripts/start.sh"
    echo "     - 或分别启动:"
    echo "       前端: cd frontend && npm run dev"
    echo "       后端: cd backend && python3 -m uvicorn app.main:app --reload"
    echo "  3. 访问应用: http://localhost:8080"
    echo
    echo "其他有用的脚本："
    echo "  - Docker 启动: ./scripts/docker-start.sh"
    echo "  - 生产构建: ./scripts/build.sh"
    echo "  - 项目文档: 查看 README.md 和 PROJECT_STRUCTURE.md"
    echo
}

# 显示帮助信息
show_help() {
    echo "Chat8 开发环境设置脚本"
    echo
    echo "用法: $0 [选项]"
    echo
    echo "选项:"
    echo "  --venv          为后端创建和使用 Python 虚拟环境"
    echo "  --skip-deps     跳过依赖安装"
    echo "  --skip-db       跳过数据库初始化"
    echo "  -h, --help      显示此帮助信息"
    echo
    echo "示例:"
    echo "  $0              # 标准设置"
    echo "  $0 --venv       # 使用虚拟环境设置"
    echo "  $0 --skip-deps  # 跳过依赖安装"
    echo
}

# 主函数
main() {
    echo "=== Chat8 开发环境设置脚本 ==="
    echo
    
    # 切换到项目根目录
    cd "$(dirname "$0")/.."
    
    # 解析参数
    USE_VENV=false
    SKIP_DEPS=false
    SKIP_DB=false
    
    while [[ $# -gt 0 ]]; do
        case $1 in
            --venv)
                USE_VENV=true
                shift
                ;;
            --skip-deps)
                SKIP_DEPS=true
                shift
                ;;
            --skip-db)
                SKIP_DB=true
                shift
                ;;
            -h|--help)
                show_help
                exit 0
                ;;
            *)
                log_error "未知选项: $1"
                show_help
                exit 1
                ;;
        esac
    done
    
    check_requirements
    create_directories
    setup_env_files
    
    if [ "$SKIP_DEPS" = false ]; then
        install_frontend_deps
        if [ "$USE_VENV" = true ]; then
            install_backend_deps --venv
        else
            install_backend_deps
        fi
    fi
    
    if [ "$SKIP_DB" = false ]; then
        init_database
    fi
    
    show_completion_info
    
    log_success "设置完成！"
}

# 错误处理
trap 'log_error "脚本执行失败"' ERR

# 执行主函数
main "$@"