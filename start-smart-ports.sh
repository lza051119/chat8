#!/bin/bash

# Chat8 智能多端口启动脚本
# 自动检测可用端口并启动前端服务

echo "=== Chat8 智能多端口启动脚本 ==="
echo "正在检测可用端口..."

# 检查端口是否被占用的函数
check_port() {
    local port=$1
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; then
        return 1  # 端口被占用
    else
        return 0  # 端口可用
    fi
}

# 查找可用端口的函数
find_available_port() {
    local start_port=$1
    local port=$start_port
    
    while [ $port -le $((start_port + 20)) ]; do
        if check_port $port; then
            echo $port
            return 0
        fi
        port=$((port + 1))
    done
    
    echo "无法找到可用端口" >&2
    return 1
}

# 目标端口列表
target_ports=(8080 8081 8082)
available_ports=()
pids=()

# 检测可用端口
for target_port in "${target_ports[@]}"; do
    if check_port $target_port; then
        available_ports+=($target_port)
        echo "✓ 端口 $target_port 可用"
    else
        echo "✗ 端口 $target_port 被占用，寻找替代端口..."
        alt_port=$(find_available_port $((target_port + 1)))
        if [ $? -eq 0 ]; then
            available_ports+=($alt_port)
            echo "✓ 使用替代端口 $alt_port"
        else
            echo "✗ 无法为端口 $target_port 找到替代端口"
        fi
    fi
done

if [ ${#available_ports[@]} -eq 0 ]; then
    echo "错误：没有找到任何可用端口"
    exit 1
fi

echo ""
echo "将在以下端口启动前端服务：${available_ports[*]}"
echo ""

# 创建日志目录
mkdir -p logs

# 清理函数
cleanup() {
    echo ""
    echo "正在停止所有前端服务..."
    for pid in "${pids[@]}"; do
        if kill -0 $pid 2>/dev/null; then
            kill $pid
            echo "已停止进程 $pid"
        fi
    done
    echo "所有服务已停止"
    exit 0
}

# 设置信号处理
trap cleanup SIGINT SIGTERM

# 启动服务
for port in "${available_ports[@]}"; do
    echo "启动前端服务在端口 $port..."
    PORT=$port npm run dev -- --host --port $port > "logs/frontend-$port.log" 2>&1 &
    pid=$!
    pids+=($pid)
    echo "前端服务已启动在端口 $port (PID: $pid)"
    sleep 2
done

echo ""
echo "=== 所有服务启动完成 ==="
echo "访问地址："
for port in "${available_ports[@]}"; do
    echo "  - http://localhost:$port"
done
echo ""
echo "日志文件位置："
for port in "${available_ports[@]}"; do
    echo "  - logs/frontend-$port.log"
done
echo ""
echo "按 Ctrl+C 停止所有服务"
echo ""

# 等待所有进程
wait