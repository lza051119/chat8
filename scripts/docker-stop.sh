#!/bin/bash

# Chat8 Docker 停止脚本
# 用于停止 Chat8 项目的 Docker 环境

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

# 停止服务
stop_services() {
    log_info "停止 Chat8 服务..."
    
    # 使用 docker-compose 或 docker compose
    if command -v docker-compose &> /dev/null; then
        DOCKER_COMPOSE="docker-compose"
    else
        DOCKER_COMPOSE="docker compose"
    fi
    
    # 停止并删除容器
    if [ "$1" = "--remove" ] || [ "$1" = "-r" ]; then
        log_info "停止并删除容器、网络和卷..."
        $DOCKER_COMPOSE down -v
    else
        log_info "停止容器..."
        $DOCKER_COMPOSE down
    fi
    
    log_success "服务已停止"
}

# 清理资源
clean_resources() {
    log_info "清理 Docker 资源..."
    
    # 删除未使用的镜像
    if [ "$1" = "--clean" ] || [ "$1" = "-c" ]; then
        log_info "删除未使用的镜像..."
        docker image prune -f
        
        log_info "删除未使用的容器..."
        docker container prune -f
        
        log_info "删除未使用的网络..."
        docker network prune -f
        
        log_info "删除未使用的卷..."
        docker volume prune -f
    fi
    
    log_success "资源清理完成"
}

# 显示帮助信息
show_help() {
    echo "Chat8 Docker 停止脚本"
    echo
    echo "用法: $0 [选项]"
    echo
    echo "选项:"
    echo "  -r, --remove    停止并删除容器、网络和卷"
    echo "  -c, --clean     清理未使用的 Docker 资源"
    echo "  -h, --help      显示此帮助信息"
    echo
    echo "示例:"
    echo "  $0              # 仅停止容器"
    echo "  $0 --remove     # 停止并删除所有资源"
    echo "  $0 --clean      # 停止容器并清理未使用的资源"
    echo
}

# 主函数
main() {
    echo "=== Chat8 Docker 停止脚本 ==="
    echo
    
    # 切换到项目根目录
    cd "$(dirname "$0")/.."
    
    case "$1" in
        -h|--help)
            show_help
            exit 0
            ;;
        -r|--remove)
            stop_services "--remove"
            ;;
        -c|--clean)
            stop_services
            clean_resources "--clean"
            ;;
        "")
            stop_services
            ;;
        *)
            log_error "未知选项: $1"
            show_help
            exit 1
            ;;
    esac
    
    log_success "操作完成！"
}

# 错误处理
trap 'log_error "脚本执行失败"' ERR

# 执行主函数
main "$@"