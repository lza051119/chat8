#!/bin/bash

# Chat8 多端口启动脚本
# 启动后端服务和多个前端服务（8080、8081、8082端口）

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 项目根目录
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.."; pwd)"
FRONTEND_DIR="$PROJECT_ROOT/frontend"
BACKEND_DIR="$PROJECT_ROOT/backend"

echo -e "${BLUE}正在启动Chat8服务...${NC}"
echo -e "${YELLOW}前端端口: 8080, 8081, 8082${NC}"
echo -e "${YELLOW}后端API: http://localhost:8000${NC}"
echo -e "${YELLOW}按 Ctrl+C 停止所有服务${NC}"
echo "========================"

# 检查必要目录
if [ ! -d "$FRONTEND_DIR" ]; then
    echo -e "${RED}错误: 前端目录不存在: $FRONTEND_DIR${NC}"
    exit 1
fi

if [ ! -d "$BACKEND_DIR" ]; then
    echo -e "${RED}错误: 后端目录不存在: $BACKEND_DIR${NC}"
    exit 1
fi

# 创建日志目录
mkdir -p "$PROJECT_ROOT/logs"

# 清理可能存在的旧进程
echo -e "${YELLOW}清理可能存在的旧进程...${NC}"
pkill -f "uvicorn.*8000" 2>/dev/null || true
pkill -f "vite.*8080" 2>/dev/null || true
pkill -f "vite.*8081" 2>/dev/null || true
pkill -f "vite.*8082" 2>/dev/null || true
sleep 2

# 清空并初始化数据库
echo -e "${YELLOW}清空并初始化数据库...${NC}"
echo -e "${YELLOW}正在清理数据库文件...${NC}"

# 删除主数据库文件
MAIN_DB_FILES=(
    "$PROJECT_ROOT/data/database/chat8.db"
    "$PROJECT_ROOT/backend/app/chat8.db"
)

for db_file in "${MAIN_DB_FILES[@]}"; do
    if [ -f "$db_file" ]; then
        rm -f "$db_file"
        echo -e "${GREEN}   ✓ 已删除: $db_file${NC}"
    fi
done

# 删除用户消息数据库
MESSAGE_DB_DIR="$PROJECT_ROOT/backend/app/local_storage/messages"
if [ -d "$MESSAGE_DB_DIR" ]; then
    find "$MESSAGE_DB_DIR" -name "user_*_messages.db" -delete 2>/dev/null || true
    echo -e "${GREEN}   ✓ 已清理用户消息数据库${NC}"
fi

# 清理上传文件
UPLOAD_DIRS=(
    "$PROJECT_ROOT/data/uploads/avatars"
    "$PROJECT_ROOT/data/uploads/backgrounds"
    "$PROJECT_ROOT/data/uploads/files"
    "$PROJECT_ROOT/data/uploads/images"
    "$PROJECT_ROOT/backend/app/static/backgrounds"
    "$PROJECT_ROOT/backend/app/static/files"
    "$PROJECT_ROOT/backend/app/static/images"
)

for upload_dir in "${UPLOAD_DIRS[@]}"; do
    if [ -d "$upload_dir" ]; then
        find "$upload_dir" -type f -delete 2>/dev/null || true
    fi
done

# 清理本地存储消息文件
LOCAL_STORAGE_DIRS=(
    "$PROJECT_ROOT/data/local_storage/messages"
    "$PROJECT_ROOT/backend/local_storage/messages"
)

for storage_dir in "${LOCAL_STORAGE_DIRS[@]}"; do
    if [ -d "$storage_dir" ]; then
        find "$storage_dir" -type f -delete 2>/dev/null || true
    fi
done

echo -e "${GREEN}数据库清理完成！${NC}"

# 初始化数据库表结构
echo -e "${YELLOW}初始化数据库表结构...${NC}"
cd "$BACKEND_DIR/app"
python3 init_db.py
if [ $? -eq 0 ]; then
    echo -e "${GREEN}数据库表结构初始化完成！${NC}"
else
    echo -e "${RED}数据库初始化失败！${NC}"
    exit 1
fi

# 启动后端服务
echo -e "${GREEN}启动后端服务 (端口 8000)...${NC}"
cd "$BACKEND_DIR"
python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload > "$PROJECT_ROOT/logs/backend.log" 2>&1 &
BACKEND_PID=$!
echo -e "${GREEN}后端服务启动完成 (PID: $BACKEND_PID)${NC}"

# 等待后端服务启动
echo -e "${YELLOW}等待后端服务启动...${NC}"
sleep 3

# 检查后端服务是否启动成功
for i in {1..10}; do
    if curl -s http://localhost:8000/health >/dev/null 2>&1; then
        echo -e "${GREEN}后端服务启动成功！${NC}"
        break
    elif [ $i -eq 10 ]; then
        echo -e "${RED}后端服务启动失败，请检查日志: logs/backend.log${NC}"
        kill $BACKEND_PID 2>/dev/null
        exit 1
    else
        echo -e "${YELLOW}等待后端服务启动... ($i/10)${NC}"
        sleep 1
    fi
done

# 切换到前端目录
cd "$FRONTEND_DIR"

# 启动8080端口服务
echo -e "${GREEN}启动前端服务 (端口 8080)...${NC}"
PORT=8080 npm run dev > "$PROJECT_ROOT/logs/port-8080.log" 2>&1 &
PID_8080=$!
echo -e "${GREEN}端口 8080 启动完成 (PID: $PID_8080)${NC}"

# 等待一秒
sleep 2

# 启动8081端口服务
echo -e "${GREEN}启动前端服务 (端口 8081)...${NC}"
PORT=8081 npm run dev > "$PROJECT_ROOT/logs/port-8081.log" 2>&1 &
PID_8081=$!
echo -e "${GREEN}端口 8081 启动完成 (PID: $PID_8081)${NC}"

# 等待一秒
sleep 2

# 启动8082端口服务
echo -e "${GREEN}启动前端服务 (端口 8082)...${NC}"
PORT=8082 npm run dev > "$PROJECT_ROOT/logs/port-8082.log" 2>&1 &
PID_8082=$!
echo -e "${GREEN}端口 8082 启动完成 (PID: $PID_8082)${NC}"

# 等待前端服务启动
sleep 3

echo "========================"
echo -e "${GREEN}所有服务已启动:${NC}"
echo -e "${BLUE}- 前端服务1: http://localhost:8080 (PID: $PID_8080)${NC}"
echo -e "${BLUE}- 前端服务2: http://localhost:8081 (PID: $PID_8081)${NC}"
echo -e "${BLUE}- 前端服务3: http://localhost:8082 (PID: $PID_8082)${NC}"
echo -e "${BLUE}- 后端API: http://localhost:8000 (PID: $BACKEND_PID)${NC}"
echo -e "${BLUE}- API文档: http://localhost:8000/docs${NC}"
echo "========================"
echo -e "${YELLOW}日志文件:${NC}"
echo -e "${YELLOW}- logs/backend.log${NC}"
echo -e "${YELLOW}- logs/port-8080.log${NC}"
echo -e "${YELLOW}- logs/port-8081.log${NC}"
echo -e "${YELLOW}- logs/port-8082.log${NC}"
echo "========================"
echo -e "${GREEN}所有服务运行正常！按 Ctrl+C 停止服务${NC}"

# 创建清理函数
cleanup() {
    echo -e "\n${YELLOW}正在停止所有服务...${NC}"
    # 优雅停止
    kill $BACKEND_PID $PID_8080 $PID_8081 $PID_8082 2>/dev/null
    sleep 2
    # 强制停止
    kill -9 $BACKEND_PID $PID_8080 $PID_8081 $PID_8082 2>/dev/null
    # 清理可能残留的进程
    pkill -f "uvicorn.*8000" 2>/dev/null || true
    pkill -f "vite.*808" 2>/dev/null || true
    echo -e "${GREEN}所有服务已停止${NC}"
    exit 0
}

# 捕获中断信号
trap cleanup SIGINT SIGTERM

# 等待所有后台进程
wait