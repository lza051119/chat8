#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检查数据库表结构的脚本
"""

import sqlite3
import os
import sys
import pathlib

# 添加父目录到路径，以便导入服务
sys.path.append(str(pathlib.Path(__file__).parent.parent))

from services.message_db_service import MessageDBService

def check_database_structure(user_id: int):
    """
    检查指定用户数据库的表结构
    """
    db_path = MessageDBService.get_user_db_path(user_id)
    
    if not os.path.exists(db_path):
        print(f"❌ 用户 {user_id} 的数据库文件不存在: {db_path}")
        return False
    
    print(f"📦 检查用户 {user_id} 的数据库结构...")
    print(f"📁 数据库路径: {db_path}")
    
    try:
        with MessageDBService.get_db_connection(user_id) as conn:
            cursor = conn.cursor()
            
            # 检查表是否存在
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='messages'")
            table_exists = cursor.fetchone()
            
            if not table_exists:
                print("❌ messages 表不存在")
                return False
            
            print("✅ messages 表存在")
            
            # 检查表结构
            cursor.execute("PRAGMA table_info(messages)")
            columns = cursor.fetchall()
            
            print("\n📋 当前表结构:")
            for col in columns:
                print(f"  - {col[1]} ({col[2]}) {'NOT NULL' if col[3] else 'NULL'} {'DEFAULT ' + str(col[4]) if col[4] else ''}")
            
            # 检查必需字段
            column_names = [col[1] for col in columns]
            required_fields = [
                'message_id', 'from_user', 'to_user', 'content', 'timestamp',
                'received_time', 'method', 'encrypted', 'message_type', 
                'file_path', 'file_name', 'is_burn_after_read', 'readable_duration',
                'is_read', 'read_time', 'is_deleted', 'created_at', 'updated_at'
            ]
            
            missing_fields = [field for field in required_fields if field not in column_names]
            
            if missing_fields:
                print(f"\n❌ 缺少字段: {missing_fields}")
            else:
                print("\n✅ 所有必需字段都存在")
            
            # 检查数据
            cursor.execute("SELECT COUNT(*) FROM messages")
            total_messages = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM messages WHERE is_deleted = FALSE")
            active_messages = cursor.fetchone()[0]
            
            print(f"\n📊 数据统计:")
            print(f"  - 总消息数: {total_messages}")
            print(f"  - 活跃消息数: {active_messages}")
            
            # 显示最近几条消息的基本信息
            cursor.execute("SELECT message_id, from_user, to_user, content, message_type FROM messages WHERE is_deleted = FALSE ORDER BY timestamp DESC LIMIT 5")
            recent_messages = cursor.fetchall()
            
            if recent_messages:
                print(f"\n📝 最近 {len(recent_messages)} 条消息:")
                for msg in recent_messages:
                    content_preview = msg[3][:30] + "..." if len(msg[3]) > 30 else msg[3]
                    print(f"  - ID: {msg[0]}, From: {msg[1]}, To: {msg[2]}, Type: {msg[4] or 'text'}, Content: {content_preview}")
            else:
                print("\n📝 没有找到消息")
            
            return len(missing_fields) == 0
            
    except Exception as e:
        print(f"❌ 检查数据库结构失败: {e}")
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
    print("=== Chat8 数据库结构检查 ===")
    
    # 查找所有用户数据库
    user_ids = find_all_user_databases()
    
    if not user_ids:
        print("❌ 未找到任何用户数据库文件")
        return
    
    print(f"📁 找到 {len(user_ids)} 个用户数据库: {user_ids}")
    
    for user_id in user_ids:
        print("\n" + "=" * 60)
        success = check_database_structure(user_id)
        if not success:
            print(f"⚠️ 用户 {user_id} 的数据库结构有问题")
        else:
            print(f"✅ 用户 {user_id} 的数据库结构正常")
    
    print("\n" + "=" * 60)
    print("🎉 数据库结构检查完成！")

if __name__ == "__main__":
    main()