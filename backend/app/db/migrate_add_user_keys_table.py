#!/usr/bin/env python3
"""
数据库迁移脚本：添加UserKeys表
用于存储用户的公钥、私钥和Signal协议相关密钥
"""

import sqlite3
import os
from datetime import datetime

def migrate_add_user_keys_table():
    """添加UserKeys表到数据库"""
    
    # 数据库文件路径
    db_path = "/Users/tsuki/Desktop/大二下/chat8/backend/app/chat8.db"
    
    if not os.path.exists(db_path):
        print(f"错误：数据库文件不存在 {db_path}")
        return False
    
    try:
        # 连接数据库
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 检查UserKeys表是否已存在
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='user_keys'
        """)
        
        if cursor.fetchone():
            print("UserKeys表已存在，跳过创建")
            conn.close()
            return True
        
        # 创建UserKeys表
        create_table_sql = """
        CREATE TABLE user_keys (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            public_key TEXT NOT NULL,
            private_key_encrypted TEXT NOT NULL,
            identity_key TEXT,
            signed_prekey TEXT,
            onetime_prekeys TEXT,
            key_version INTEGER DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
        )
        """
        
        cursor.execute(create_table_sql)
        
        # 创建索引
        cursor.execute("""
            CREATE INDEX idx_user_keys_user_id ON user_keys(user_id)
        """)
        
        cursor.execute("""
            CREATE UNIQUE INDEX idx_user_keys_user_version ON user_keys(user_id, key_version)
        """)
        
        # 提交更改
        conn.commit()
        
        print("✅ UserKeys表创建成功")
        print("✅ 相关索引创建成功")
        
        # 验证表结构
        cursor.execute("PRAGMA table_info(user_keys)")
        columns = cursor.fetchall()
        print("\n📋 UserKeys表结构：")
        for col in columns:
            print(f"  - {col[1]} ({col[2]})")
        
        conn.close()
        return True
        
    except sqlite3.Error as e:
        print(f"❌ 数据库操作失败: {e}")
        if 'conn' in locals():
            conn.rollback()
            conn.close()
        return False
    except Exception as e:
        print(f"❌ 迁移失败: {e}")
        if 'conn' in locals():
            conn.close()
        return False

def check_database_structure():
    """检查数据库结构"""
    db_path = "/Users/tsuki/Desktop/大二下/chat8/backend/app/chat8.db"
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 获取所有表
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name NOT LIKE 'sqlite_%'
            ORDER BY name
        """)
        
        tables = cursor.fetchall()
        print("\n📊 数据库中的表：")
        for table in tables:
            table_name = table[0]
            print(f"\n🔹 {table_name}")
            
            # 获取表结构
            cursor.execute(f"PRAGMA table_info({table_name})")
            columns = cursor.fetchall()
            for col in columns:
                print(f"    {col[1]} ({col[2]})")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ 检查数据库结构失败: {e}")

if __name__ == "__main__":
    print("🚀 开始数据库迁移：添加UserKeys表")
    print(f"⏰ 迁移时间: {datetime.now()}")
    
    # 执行迁移
    success = migrate_add_user_keys_table()
    
    if success:
        print("\n✅ 迁移完成！")
        # 检查数据库结构
        check_database_structure()
    else:
        print("\n❌ 迁移失败！")
        exit(1)