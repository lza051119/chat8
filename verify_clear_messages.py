#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
验证消息清空操作是否成功
"""

import os
import sqlite3
import sys
from pathlib import Path

# 添加backend/app到Python路径
backend_app_path = Path(__file__).parent / 'backend' / 'app'
sys.path.insert(0, str(backend_app_path))

from services.message_db_service import MessageDBService

def verify_messages_cleared():
    """验证所有用户数据库中的消息是否已清空"""
    messages_dir = Path(__file__).parent / 'backend' / 'app' / 'local_storage' / 'messages'
    
    if not messages_dir.exists():
        print(f"消息目录不存在: {messages_dir}")
        return
    
    # 查找所有用户数据库文件
    db_files = list(messages_dir.glob('user_*_messages.db'))
    
    if not db_files:
        print("未找到任何用户数据库文件")
        return
    
    print(f"检查 {len(db_files)} 个用户数据库文件")
    
    for db_file in db_files:
        # 从文件名提取用户ID
        filename = db_file.name
        try:
            user_id = int(filename.split('_')[1])
            
            # 直接查询数据库中的消息数量
            with MessageDBService.get_db_connection(user_id) as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT COUNT(*) FROM messages')
                count = cursor.fetchone()[0]
                
                if count == 0:
                    print(f"✓ 用户 {user_id}: 消息已清空 (0 条消息)")
                else:
                    print(f"✗ 用户 {user_id}: 仍有 {count} 条消息")
                    
        except (ValueError, IndexError) as e:
            print(f"✗ 无法解析文件名 {filename}: {e}")
            continue
        except Exception as e:
            print(f"✗ 检查用户 {user_id} 数据库时出错: {e}")
            continue

if __name__ == '__main__':
    print("验证消息清空操作...")
    verify_messages_cleared()
    print("验证完成")