#!/usr/bin/env python3
"""
数据库迁移脚本：删除UserKeys表中的identity_key、signed_prekey和onetime_prekeys字段
"""

import sqlite3
import os
from datetime import datetime

def migrate_user_keys_table():
    """迁移UserKeys表结构"""
    
    # 数据库文件路径
    db_paths = [
        "/Users/tsuki/Desktop/chat8/backend/app/chat8.db",
        "/Users/tsuki/Desktop/chat8/chat8.db",
        "/Users/tsuki/Desktop/chat8/backend/chat8.db"
    ]
    
    for db_path in db_paths:
        if os.path.exists(db_path):
            print(f"正在迁移数据库: {db_path}")
            migrate_single_database(db_path)
        else:
            print(f"数据库文件不存在: {db_path}")

def migrate_single_database(db_path):
    """迁移单个数据库文件"""
    
    try:
        # 备份原数据库
        backup_path = f"{db_path}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        import shutil
        shutil.copy2(db_path, backup_path)
        print(f"✅ 已创建备份: {backup_path}")
        
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 检查user_keys表是否存在
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='user_keys'
        """)
        
        if not cursor.fetchone():
            print("⚠️  user_keys表不存在，跳过迁移")
            conn.close()
            return
        
        # 检查需要删除的字段是否存在
        cursor.execute("PRAGMA table_info(user_keys)")
        columns = cursor.fetchall()
        column_names = [col[1] for col in columns]
        
        fields_to_remove = ['identity_key', 'signed_prekey', 'onetime_prekeys']
        existing_fields = [field for field in fields_to_remove if field in column_names]
        
        if not existing_fields:
            print("✅ 表结构已经是最新的，无需迁移")
            conn.close()
            return
        
        print(f"需要删除的字段: {existing_fields}")
        
        # 获取现有数据
        cursor.execute("""
            SELECT id, user_id, public_key, private_key_encrypted, 
                   key_version, created_at, updated_at
            FROM user_keys
        """)
        
        existing_data = cursor.fetchall()
        print(f"找到 {len(existing_data)} 条现有记录")
        
        # 创建新表
        cursor.execute("""
            CREATE TABLE user_keys_new (
                id INTEGER PRIMARY KEY,
                user_id INTEGER UNIQUE NOT NULL,
                public_key TEXT NOT NULL,
                private_key_encrypted TEXT NOT NULL,
                key_version INTEGER DEFAULT 1,
                created_at DATETIME,
                updated_at DATETIME,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        """)
        
        # 迁移数据
        if existing_data:
            cursor.executemany("""
                INSERT INTO user_keys_new 
                (id, user_id, public_key, private_key_encrypted, 
                 key_version, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, existing_data)
            
            print(f"✅ 已迁移 {len(existing_data)} 条记录")
        
        # 删除旧表
        cursor.execute("DROP TABLE user_keys")
        
        # 重命名新表
        cursor.execute("ALTER TABLE user_keys_new RENAME TO user_keys")
        
        # 提交更改
        conn.commit()
        print("✅ 数据库迁移完成")
        
        # 验证迁移结果
        cursor.execute("PRAGMA table_info(user_keys)")
        new_columns = cursor.fetchall()
        new_column_names = [col[1] for col in new_columns]
        
        print(f"新表结构字段: {new_column_names}")
        
        # 验证数据完整性
        cursor.execute("SELECT COUNT(*) FROM user_keys")
        count = cursor.fetchone()[0]
        print(f"迁移后记录数: {count}")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ 迁移失败: {str(e)}")
        if 'conn' in locals():
            conn.rollback()
            conn.close()
        raise

if __name__ == "__main__":
    print("🔄 开始数据库迁移...")
    print("⚠️  此操作将删除identity_key、signed_prekey和onetime_prekeys字段")
    
    confirm = input("是否继续？(Y/n): ")
    if confirm.lower() == 'n':
        print("❌ 迁移已取消")
        exit()
    
    try:
        migrate_user_keys_table()
        print("\n🎉 数据库迁移完成！")
        print("💡 提示：")
        print("  - 已删除identity_key、signed_prekey和onetime_prekeys字段")
        print("  - 保留了public_key和private_key_encrypted字段")
        print("  - 原数据库已备份")
    except Exception as e:
        print(f"\n❌ 迁移失败: {str(e)}")
        exit(1)