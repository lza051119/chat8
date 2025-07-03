#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
清空所有用户数据库中的消息
"""

import os
import sqlite3
import sys
from pathlib import Path

# 添加backend/app到Python路径
backend_app_path = Path(__file__).parent / 'backend' / 'app'
sys.path.insert(0, str(backend_app_path))

from services.message_db_service import MessageDBService

def clear_all_user_messages():
    """清空所有用户数据库中的消息"""
    messages_dir = Path(__file__).parent / 'backend' / 'app' / 'local_storage' / 'messages'
    
    if not messages_dir.exists():
        print(f"消息目录不存在: {messages_dir}")
        return
    
    # 查找所有用户数据库文件
    db_files = list(messages_dir.glob('user_*_messages.db'))
    
    if not db_files:
        print("未找到任何用户数据库文件")
        return
    
    print(f"找到 {len(db_files)} 个用户数据库文件")
    
    success_count = 0
    for db_file in db_files:
        # 从文件名提取用户ID
        filename = db_file.name
        try:
            user_id = int(filename.split('_')[1])
            print(f"正在清空用户 {user_id} 的消息...")
            
            if MessageDBService.clear_all_messages(user_id):
                print(f"✓ 用户 {user_id} 的消息已清空")
                success_count += 1
            else:
                print(f"✗ 清空用户 {user_id} 的消息失败")
                
        except (ValueError, IndexError) as e:
            print(f"✗ 无法解析文件名 {filename}: {e}")
            continue
    
    print(f"\n清空完成: {success_count}/{len(db_files)} 个数据库处理成功")

if __name__ == '__main__':
    print("开始清空所有用户数据库中的消息...")
    clear_all_user_messages()
    print("操作完成")