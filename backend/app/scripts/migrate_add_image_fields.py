#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据库迁移脚本：为现有数据库添加图片消息字段
添加字段：message_type, file_path, file_name
"""

import sqlite3
import os
import sys
import pathlib

# 添加父目录到路径，以便导入服务
sys.path.append(str(pathlib.Path(__file__).parent.parent))

from services.message_db_service import MessageDBService

def migrate_user_database(user_id: int):
    """
    为指定用户的数据库添加图片消息字段
    """
    db_path = MessageDBService.get_user_db_path(user_id)
    
    if not os.path.exists(db_path):
        print(f"❌ 用户 {user_id} 的数据库文件不存在: {db_path}")
        return False
    
    print(f"📦 开始迁移用户 {user_id} 的数据库...")
    
    try:
        with MessageDBService.get_db_connection(user_id) as conn:
            cursor = conn.cursor()
            
            # 检查表结构
            cursor.execute("PRAGMA table_info(messages)")
            columns = [column[1] for column in cursor.fetchall()]
            print(f"📋 当前字段: {columns}")
            
            # 添加 message_type 字段
            if 'message_type' not in columns:
                print("➕ 添加 message_type 字段...")
                cursor.execute('ALTER TABLE messages ADD COLUMN message_type TEXT DEFAULT "text"')
                print("✅ message_type 字段添加成功")
            else:
                print("✅ message_type 字段已存在")
            
            # 添加 file_path 字段
            if 'file_path' not in columns:
                print("➕ 添加 file_path 字段...")
                cursor.execute('ALTER TABLE messages ADD COLUMN file_path TEXT DEFAULT NULL')
                print("✅ file_path 字段添加成功")
            else:
                print("✅ file_path 字段已存在")
            
            # 添加 file_name 字段
            if 'file_name' not in columns:
                print("➕ 添加 file_name 字段...")
                cursor.execute('ALTER TABLE messages ADD COLUMN file_name TEXT DEFAULT NULL')
                print("✅ file_name 字段添加成功")
            else:
                print("✅ file_name 字段已存在")
            
            conn.commit()
            
            # 验证字段添加
            cursor.execute("PRAGMA table_info(messages)")
            new_columns = [column[1] for column in cursor.fetchall()]
            print(f"📋 更新后字段: {new_columns}")
            
            print(f"🎉 用户 {user_id} 数据库迁移完成")
            return True
            
    except Exception as e:
        print(f"❌ 迁移用户 {user_id} 数据库失败: {e}")
        return False

def find_all_user_databases():
    """
    查找所有用户数据库文件
    """
    db_dir = os.path.dirname(MessageDBService.get_user_db_path(1))
    if not os.path.exists(db_dir):
        print(f"❌ 数据库目录不存在: {db_dir}")
        return []
    
    db_files = [f for f in os.listdir(db_dir) if f.endswith('_messages.db')]
    user_ids = []
    
    for db_file in db_files:
        try:
            # 从文件名提取用户ID: user_18_messages.db -> 18
            user_id_str = db_file.replace('user_', '').replace('_messages.db', '')
            user_id = int(user_id_str)
            user_ids.append(user_id)
        except ValueError:
            print(f"⚠️ 无法解析用户ID: {db_file}")
    
    return sorted(user_ids)

def main():
    """
    主函数
    """
    print("=== Chat8 数据库迁移：添加图片消息字段 ===")
    
    # 查找所有用户数据库
    user_ids = find_all_user_databases()
    
    if not user_ids:
        print("❌ 未找到任何用户数据库文件")
        return
    
    print(f"📁 找到 {len(user_ids)} 个用户数据库: {user_ids}")
    
    success_count = 0
    
    for user_id in user_ids:
        if migrate_user_database(user_id):
            success_count += 1
        print("-" * 50)
    
    print(f"\n🎉 迁移完成！成功: {success_count}/{len(user_ids)}")
    
    if success_count == len(user_ids):
        print("✅ 所有数据库迁移成功！")
    else:
        print(f"⚠️ {len(user_ids) - success_count} 个数据库迁移失败")

if __name__ == "__main__":
    main()