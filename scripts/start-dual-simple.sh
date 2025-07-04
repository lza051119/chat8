#!/bin/bash

# Chat8 简化双端口启动脚本

echo "=== Chat8 双端口启动 ==="
echo "正在启动后端和双前端服务..."
echo "========================"

# 创建日志目录
mkdir -p /Users/tsuki/Desktop/chat8/logs

# 启动后端服务
echo "启动后端服务..."
cd /Users/tsuki/Desktop/chat8/backend
source venv/bin/activate

# 终止可能存在的进程
pkill -f "uvicorn.*8000" 2>/dev/null || true
sleep 1

python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload > /Users/tsuki/Desktop/chat8/logs/backend.log 2>&1 &
BACKEND_PID=$!
echo "后端进程 PID: $BACKEND_PID"

# 等待后端启动
sleep 3

# 启动前端服务
cd /Users/tsuki/Desktop/chat8/frontend

echo "启动前端端口 8080..."
PORT=8080 npm run dev > /Users/tsuki/Desktop/chat8/logs/port-8080.log 2>&1 &
PID_8080=$!
echo "前端8080 PID: $PID_8080"

sleep 2

echo "启动前端端口 8081..."
PORT=8081 npm run dev > /Users/tsuki/Desktop/chat8/logs/port-8081.log 2>&1 &
PID_8081=$!
echo "前端8081 PID: $PID_8081"

# 等待服务启动
sleep 3

# 检查服务状态
echo "========================"
if curl -s http://localhost:8000/api/ping > /dev/null; then
    echo "✓ 后端服务正常 (http://localhost:8000)"
else
    echo "✗ 后端服务异常"
fi

echo "========================"
echo "服务已启动:"
echo "- 前端: http://localhost:8080"
echo "- 前端: http://localhost:8081"
echo "- 后端: http://localhost:8000"
echo "- API文档: http://localhost:8000/docs"
echo "========================"
echo "按 Ctrl+C 停止所有服务"

# 清理函数
cleanup() {
    echo "\n正在停止服务..."
    kill $BACKEND_PID $PID_8080 $PID_8081 2>/dev/null
    pkill -f "uvicorn.*8000" 2>/dev/null || true
    pkill -f "vite.*8080" 2>/dev/null || true
    pkill -f "vite.*8081" 2>/dev/null || true
    echo "服务已停止"
    exit 0
}

trap cleanup SIGINT SIGTERM
wait