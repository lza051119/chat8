#!/bin/bash

# Chat8 多端口启动脚本
# 同时在8080、8081、8082端口启动前端服务

echo "正在启动Chat8前端服务..."
echo "端口: 8080, 8081, 8082"
echo "后端API: http://localhost:8000"
echo "按 Ctrl+C 停止所有服务"
echo "========================"

# 创建日志目录
mkdir -p logs

# 启动8080端口服务
echo "启动端口 8080..."
PORT=8080 npm run dev > logs/port-8080.log 2>&1 &
PID_8080=$!
echo "端口 8080 启动完成 (PID: $PID_8080)"

# 等待一秒
sleep 1

# 启动8081端口服务
echo "启动端口 8081..."
PORT=8081 npm run dev > logs/port-8081.log 2>&1 &
PID_8081=$!
echo "端口 8081 启动完成 (PID: $PID_8081)"

# 等待一秒
sleep 1

# 启动8082端口服务
echo "启动端口 8082..."
PORT=8082 npm run dev > logs/port-8082.log 2>&1 &
PID_8082=$!
echo "端口 8082 启动完成 (PID: $PID_8082)"

echo "========================"
echo "所有服务已启动:"
echo "- http://localhost:8080 (PID: $PID_8080)"
echo "- http://localhost:8081 (PID: $PID_8081)"
echo "- http://localhost:8082 (PID: $PID_8082)"
echo "========================"
echo "日志文件:"
echo "- logs/port-8080.log"
echo "- logs/port-8081.log"
echo "- logs/port-8082.log"
echo "========================"

# 创建清理函数
cleanup() {
    echo "\n正在停止所有服务..."
    kill $PID_8080 $PID_8081 $PID_8082 2>/dev/null
    echo "所有服务已停止"
    exit 0
}

# 捕获中断信号
trap cleanup SIGINT SIGTERM

# 等待所有后台进程
wait