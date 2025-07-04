#!/bin/bash

# Chat8 数据库完全清空脚本

echo "=== Chat8 数据库清空脚本 ==="
echo "⚠️  警告：此操作将删除所有数据库文件和数据！"
echo "========================"

# 项目根目录
PROJECT_ROOT="/Users/tsuki/Desktop/chat8"

# 停止所有可能运行的服务
echo "正在停止服务..."
pkill -f "uvicorn.*8000" 2>/dev/null || true
pkill -f "vite.*8080" 2>/dev/null || true
pkill -f "vite.*8081" 2>/dev/null || true
sleep 2

echo "开始清空数据库..."

# 1. 删除主数据库文件
echo "1. 清理主数据库文件..."
MAIN_DB_FILES=(
    "$PROJECT_ROOT/data/database/chat8.db"
    "$PROJECT_ROOT/data/database/chat8.db.backup_20250704_064621"
    "$PROJECT_ROOT/backend/app/chat8.db"
)

for db_file in "${MAIN_DB_FILES[@]}"; do
    if [ -f "$db_file" ]; then
        rm -f "$db_file"
        echo "   ✓ 已删除: $db_file"
    else
        echo "   - 不存在: $db_file"
    fi
done

# 2. 删除所有用户消息数据库
echo "2. 清理用户消息数据库..."
MESSAGE_DB_DIR="$PROJECT_ROOT/backend/app/local_storage/messages"

if [ -d "$MESSAGE_DB_DIR" ]; then
    USER_DB_COUNT=$(find "$MESSAGE_DB_DIR" -name "user_*_messages.db" | wc -l)
    echo "   发现 $USER_DB_COUNT 个用户数据库文件"
    
    find "$MESSAGE_DB_DIR" -name "user_*_messages.db" -delete
    echo "   ✓ 已删除所有用户消息数据库"
else
    echo "   - 消息数据库目录不存在"
fi

# 3. 清理上传的文件
echo "3. 清理上传文件..."
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
        # 保留目录结构，只删除文件
        find "$upload_dir" -type f -delete 2>/dev/null || true
        find "$upload_dir" -type d -empty -delete 2>/dev/null || true
        echo "   ✓ 已清理: $upload_dir"
    else
        echo "   - 不存在: $upload_dir"
    fi
done

# 4. 清理本地存储的消息文件
echo "4. 清理本地存储消息文件..."
LOCAL_STORAGE_DIRS=(
    "$PROJECT_ROOT/data/local_storage/messages"
    "$PROJECT_ROOT/backend/local_storage/messages"
)

for storage_dir in "${LOCAL_STORAGE_DIRS[@]}"; do
    if [ -d "$storage_dir" ]; then
        find "$storage_dir" -type f -delete 2>/dev/null || true
        echo "   ✓ 已清理: $storage_dir"
    else
        echo "   - 不存在: $storage_dir"
    fi
done

# 5. 清理日志文件
echo "5. 清理日志文件..."
LOG_DIRS=(
    "$PROJECT_ROOT/logs"
    "$PROJECT_ROOT/data/logs"
)

for log_dir in "${LOG_DIRS[@]}"; do
    if [ -d "$log_dir" ]; then
        find "$log_dir" -name "*.log" -delete 2>/dev/null || true
        echo "   ✓ 已清理: $log_dir"
    else
        echo "   - 不存在: $log_dir"
    fi
done

# 6. 清理缓存文件
echo "6. 清理Python缓存..."
find "$PROJECT_ROOT/backend" -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
find "$PROJECT_ROOT/backend" -name "*.pyc" -delete 2>/dev/null || true
echo "   ✓ 已清理Python缓存文件"

echo "========================"
echo "✅ 数据库清空完成！"
echo "========================"
echo "已清理的内容："
echo "- 主数据库文件 (chat8.db)"
echo "- 所有用户消息数据库"
echo "- 上传的文件 (头像、背景、图片等)"
echo "- 本地存储的消息文件"
echo "- 日志文件"
echo "- Python缓存文件"
echo "========================"
echo "注意：下次启动服务时会自动重新创建数据库表结构"