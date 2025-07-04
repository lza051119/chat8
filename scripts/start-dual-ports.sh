#!/bin/bash

# Chat8 双端口启动脚本
# 同时启动后端服务和两个前端端口

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
LOGS_DIR="$PROJECT_ROOT/logs"

echo -e "${BLUE}=== Chat8 双端口启动脚本 ===${NC}"
echo "正在启动Chat8服务..."
echo "前端端口: 8080, 8081"
echo "后端端口: 8000"
echo "按 Ctrl+C 停止所有服务"
echo "========================"

# 创建日志目录
mkdir -p "$LOGS_DIR"

# 检查必要目录是否存在
if [ ! -d "$BACKEND_DIR" ]; then
    echo -e "${RED}错误: 后端目录不存在: $BACKEND_DIR${NC}"
    exit 1
fi

if [ ! -d "$FRONTEND_DIR" ]; then
    echo -e "${RED}错误: 前端目录不存在: $FRONTEND_DIR${NC}"
    exit 1
fi

# 检查虚拟环境
if [ ! -f "$BACKEND_DIR/venv/bin/activate" ]; then
    echo -e "${RED}错误: Python虚拟环境不存在，请先运行 setup-dev.sh${NC}"
    exit 1
fi

# 清理可能存在的进程
echo -e "${YELLOW}清理现有进程...${NC}"
pkill -f "uvicorn.*8000" 2>/dev/null || true
pkill -f "vite.*8080" 2>/dev/null || true
pkill -f "vite.*8081" 2>/dev/null || true
sleep 2

# 启动后端服务
echo -e "${YELLOW}启动后端服务...${NC}"
cd "$BACKEND_DIR"
source venv/bin/activate

echo -e "${GREEN}后端服务启动中... (端口: 8000)${NC}"
python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload > "$LOGS_DIR/backend.log" 2>&1 &
BACKEND_PID=$!
echo "后端进程 PID: $BACKEND_PID"

# 等待后端启动
echo -e "${YELLOW}等待后端服务启动...${NC}"
sleep 5

# 检查后端是否启动成功
BACKEND_READY=false
for i in {1..10}; do
    if curl -s http://localhost:8000/api/ping > /dev/null 2>&1; then
        echo -e "${GREEN}✓ 后端服务启动成功${NC}"
        BACKEND_READY=true
        break
    fi
    echo "等待后端启动... ($i/10)"
    sleep 1
done

if [ "$BACKEND_READY" = false ]; then
    echo -e "${RED}✗ 后端服务启动失败，请检查日志: $LOGS_DIR/backend.log${NC}"
    kill $BACKEND_PID 2>/dev/null || true
    exit 1
fi

# 切换到前端目录
cd "$FRONTEND_DIR"

# 检查package.json是否存在
if [ ! -f "package.json" ]; then
    echo -e "${RED}错误: package.json 不存在，请先安装前端依赖${NC}"
    kill $BACKEND_PID 2>/dev/null || true
    exit 1
fi

# 启动8080端口服务
echo -e "${YELLOW}启动前端端口 8080...${NC}"
PORT=8080 npm run dev > "$LOGS_DIR/port-8080.log" 2>&1 &
PID_8080=$!
echo "前端8080进程 PID: $PID_8080"

# 等待2秒
sleep 2

# 启动8081端口服务
echo -e "${YELLOW}启动前端端口 8081...${NC}"
PORT=8081 npm run dev > "$LOGS_DIR/port-8081.log" 2>&1 &
PID_8081=$!
echo "前端8081进程 PID: $PID_8081"

# 等待前端服务启动
echo -e "${YELLOW}等待前端服务启动...${NC}"
sleep 5

# 检查前端服务状态
FRONTEND_8080_READY=false
FRONTEND_8081_READY=false

for i in {1..10}; do
    if curl -s http://localhost:8080 > /dev/null 2>&1; then
        FRONTEND_8080_READY=true
    fi
    if curl -s http://localhost:8081 > /dev/null 2>&1; then
        FRONTEND_8081_READY=true
    fi
    
    if [ "$FRONTEND_8080_READY" = true ] && [ "$FRONTEND_8081_READY" = true ]; then
        break
    fi
    
    echo "等待前端服务启动... ($i/10)"
    sleep 1
done

echo "========================"
echo -e "${GREEN}服务启动状态:${NC}"

if [ "$BACKEND_READY" = true ]; then
    echo -e "${GREEN}✓ 后端服务: http://localhost:8000 (PID: $BACKEND_PID)${NC}"
else
    echo -e "${RED}✗ 后端服务启动失败${NC}"
fi

if [ "$FRONTEND_8080_READY" = true ]; then
    echo -e "${GREEN}✓ 前端8080: http://localhost:8080 (PID: $PID_8080)${NC}"
else
    echo -e "${YELLOW}⚠ 前端8080: 启动中... (PID: $PID_8080)${NC}"
fi

if [ "$FRONTEND_8081_READY" = true ]; then
    echo -e "${GREEN}✓ 前端8081: http://localhost:8081 (PID: $PID_8081)${NC}"
else
    echo -e "${YELLOW}⚠ 前端8081: 启动中... (PID: $PID_8081)${NC}"
fi

echo -e "${GREEN}✓ API文档: http://localhost:8000/docs${NC}"
echo "========================"
echo "日志文件:"
echo "- $LOGS_DIR/backend.log"
echo "- $LOGS_DIR/port-8080.log"
echo "- $LOGS_DIR/port-8081.log"
echo "========================"
echo -e "${BLUE}提示: 前端服务可能需要额外时间完成启动${NC}"
echo -e "${BLUE}如果前端无法访问，请等待1-2分钟或查看日志文件${NC}"
echo "========================"

# 创建清理函数
cleanup() {
    echo -e "\n${YELLOW}正在停止所有服务...${NC}"
    
    # 优雅停止进程
    if [ ! -z "$BACKEND_PID" ]; then
        kill $BACKEND_PID 2>/dev/null || true
    fi
    if [ ! -z "$PID_8080" ]; then
        kill $PID_8080 2>/dev/null || true
    fi
    if [ ! -z "$PID_8081" ]; then
        kill $PID_8081 2>/dev/null || true
    fi
    
    sleep 2
    
    # 强制终止相关进程
    pkill -f "uvicorn.*8000" 2>/dev/null || true
    pkill -f "vite.*8080" 2>/dev/null || true
    pkill -f "vite.*8081" 2>/dev/null || true
    
    echo -e "${GREEN}所有服务已停止${NC}"
    exit 0
}

# 捕获中断信号
trap cleanup SIGINT SIGTERM

# 等待所有后台进程
wait