#!/usr/bin/env python3
"""
数据库迁移脚本：添加会话密钥表
"""

import sqlite3
import os
from datetime import datetime

def migrate_database():
    """添加session_keys表到数据库"""
    
    # 数据库文件路径
    db_paths = [
        "/Users/tsuki/Desktop/chat8/backend/app/chat8.db",
        "/Users/tsuki/Desktop/chat8/backend/chat8.db",
        "/Users/tsuki/Desktop/chat8/chat8.db"
    ]
    
    # 创建session_keys表的SQL
    create_table_sql = """
    CREATE TABLE IF NOT EXISTS session_keys (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user1_id INTEGER NOT NULL,
        user2_id INTEGER NOT NULL,
        session_key_encrypted TEXT NOT NULL,
        session_key_encrypted_for_user2 TEXT,
        key_version INTEGER DEFAULT 1,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user1_id) REFERENCES users (id),
        FOREIGN KEY (user2_id) REFERENCES users (id)
    );
    """
    
    # 创建索引的SQL
    create_index_sql = """
    CREATE INDEX IF NOT EXISTS idx_session_keys_users 
    ON session_keys (user1_id, user2_id);
    """
    
    migrated_count = 0
    
    for db_path in db_paths:
        if os.path.exists(db_path):
            try:
                print(f"🔄 正在迁移数据库: {db_path}")
                
                # 连接数据库
                conn = sqlite3.connect(db_path)
                cursor = conn.cursor()
                
                # 检查表是否已存在
                cursor.execute("""
                    SELECT name FROM sqlite_master 
                    WHERE type='table' AND name='session_keys'
                """)
                
                if cursor.fetchone():
                    print(f"  ⚠️  表 session_keys 已存在，跳过创建")
                else:
                    # 创建表
                    cursor.execute(create_table_sql)
                    print(f"  ✅ 成功创建 session_keys 表")
                
                # 创建索引
                cursor.execute(create_index_sql)
                print(f"  ✅ 成功创建索引")
                
                # 提交更改
                conn.commit()
                conn.close()
                
                migrated_count += 1
                print(f"  ✅ 数据库迁移完成: {db_path}\n")
                
            except Exception as e:
                print(f"  ❌ 迁移失败: {db_path}")
                print(f"     错误: {str(e)}\n")
        else:
            print(f"  ⚠️  数据库文件不存在: {db_path}\n")
    
    print(f"🎉 迁移完成！成功迁移了 {migrated_count} 个数据库文件")
    return migrated_count > 0

def verify_migration():
    """验证迁移是否成功"""
    db_paths = [
        "/Users/tsuki/Desktop/chat8/backend/app/chat8.db",
        "/Users/tsuki/Desktop/chat8/backend/chat8.db",
        "/Users/tsuki/Desktop/chat8/chat8.db"
    ]
    
    print("\n🔍 验证迁移结果...")
    
    for db_path in db_paths:
        if os.path.exists(db_path):
            try:
                conn = sqlite3.connect(db_path)
                cursor = conn.cursor()
                
                # 检查表结构
                cursor.execute("PRAGMA table_info(session_keys)")
                columns = cursor.fetchall()
                
                if columns:
                    print(f"✅ {db_path}:")
                    print(f"   session_keys 表包含 {len(columns)} 个字段:")
                    for col in columns:
                        print(f"     - {col[1]} ({col[2]})")
                else:
                    print(f"❌ {db_path}: session_keys 表不存在")
                
                conn.close()
                
            except Exception as e:
                print(f"❌ 验证失败 {db_path}: {str(e)}")
        else:
            print(f"⚠️  数据库文件不存在: {db_path}")

if __name__ == "__main__":
    print("🚀 开始数据库迁移...")
    print("📝 添加 session_keys 表用于存储用户间的会话密钥\n")
    
    # 执行迁移
    success = migrate_database()
    
    if success:
        # 验证迁移
        verify_migration()
        print("\n🎉 数据库迁移成功完成！")
    else:
        print("\n❌ 数据库迁移失败！")
        exit(1)