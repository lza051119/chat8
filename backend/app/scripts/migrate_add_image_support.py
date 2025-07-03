#!/usr/bin/env python3
"""
数据库迁移脚本：添加图片消息支持
为Message表添加新字段：message_type, file_path, file_name, hidding_message
"""

import sqlite3
import os
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def migrate_database(db_path):
    """
    执行数据库迁移
    """
    print(f"开始迁移数据库: {db_path}")
    
    # 检查数据库文件是否存在
    if not os.path.exists(db_path):
        print(f"错误: 数据库文件不存在: {db_path}")
        return False
    
    try:
        # 连接数据库
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 检查是否已经迁移过
        cursor.execute("PRAGMA table_info(messages)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'message_type' in columns:
            print("数据库已经迁移过，跳过迁移")
            conn.close()
            return True
        
        print("开始添加新字段...")
        
        # 添加新字段
        migrations = [
            "ALTER TABLE messages ADD COLUMN message_type TEXT DEFAULT 'text'",
            "ALTER TABLE messages ADD COLUMN file_path TEXT",
            "ALTER TABLE messages ADD COLUMN file_name TEXT", 
            "ALTER TABLE messages ADD COLUMN hidding_message TEXT"
        ]
        
        for migration in migrations:
            try:
                cursor.execute(migration)
                print(f"✓ 执行成功: {migration}")
            except sqlite3.Error as e:
                print(f"✗ 执行失败: {migration}")
                print(f"  错误: {e}")
                conn.rollback()
                conn.close()
                return False
        
        # 提交更改
        conn.commit()
        print("✓ 所有迁移已成功提交")
        
        # 验证迁移结果
        cursor.execute("PRAGMA table_info(messages)")
        new_columns = [column[1] for column in cursor.fetchall()]
        print(f"迁移后的字段: {new_columns}")
        
        conn.close()
        print("✓ 数据库迁移完成")
        return True
        
    except Exception as e:
        print(f"✗ 迁移失败: {e}")
        return False

def main():
    """
    主函数
    """
    print("Chat8 数据库迁移工具 - 添加图片消息支持")
    print("=" * 50)
    
    # 数据库文件路径
    db_paths = [
        project_root / "chat8.db",  # 主数据库
        project_root / "app" / "chat8.db"  # 应用目录下的数据库
    ]
    
    success_count = 0
    total_count = 0
    
    for db_path in db_paths:
        if os.path.exists(db_path):
            total_count += 1
            print(f"\n处理数据库: {db_path}")
            if migrate_database(db_path):
                success_count += 1
            else:
                print(f"✗ 迁移失败: {db_path}")
        else:
            print(f"跳过不存在的数据库: {db_path}")
    
    print("\n" + "=" * 50)
    print(f"迁移完成: {success_count}/{total_count} 个数据库迁移成功")
    
    if success_count == total_count and total_count > 0:
        print("✓ 所有数据库迁移成功！")
        return True
    elif total_count == 0:
        print("⚠ 未找到任何数据库文件")
        return False
    else:
        print("✗ 部分数据库迁移失败")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)