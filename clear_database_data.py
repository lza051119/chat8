#!/usr/bin/env python3
"""
清空数据库数据但保留表结构的脚本
"""

import sqlite3
import os
from datetime import datetime

def clear_database_data():
    """清空所有表的数据但保留表结构"""
    
    # 数据库文件路径
    db_path = "/Users/tsuki/Desktop/chat8/backend/app/chat8.db"
    
    if not os.path.exists(db_path):
        print(f"错误：数据库文件不存在 {db_path}")
        return False
    
    try:
        # 连接数据库
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 获取所有表名
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name NOT LIKE 'sqlite_%'
            ORDER BY name
        """)
        
        tables = cursor.fetchall()
        print(f"\n📊 发现 {len(tables)} 个表需要清空数据：")
        
        # 禁用外键约束
        cursor.execute("PRAGMA foreign_keys = OFF")
        
        # 清空每个表的数据
        for table in tables:
            table_name = table[0]
            try:
                # 获取表中的记录数
                cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
                count = cursor.fetchone()[0]
                
                if count > 0:
                    # 清空表数据
                    cursor.execute(f"DELETE FROM {table_name}")
                    print(f"✅ 已清空表 {table_name} ({count} 条记录)")
                else:
                    print(f"ℹ️  表 {table_name} 已经是空的")
                    
            except Exception as e:
                print(f"❌ 清空表 {table_name} 失败: {str(e)}")
        
        # 重置自增ID
        cursor.execute("DELETE FROM sqlite_sequence")
        print("🔄 已重置所有自增ID")
        
        # 重新启用外键约束
        cursor.execute("PRAGMA foreign_keys = ON")
        
        # 提交更改
        conn.commit()
        print("\n✅ 数据库数据清空完成！表结构已保留。")
        
        # 验证清空结果
        print("\n📋 验证清空结果：")
        for table in tables:
            table_name = table[0]
            cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            count = cursor.fetchone()[0]
            print(f"  - {table_name}: {count} 条记录")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ 清空数据库失败: {str(e)}")
        return False

def backup_database():
    """备份数据库"""
    db_path = "/Users/tsuki/Desktop/chat8/backend/app/chat8.db"
    backup_path = f"/Users/tsuki/Desktop/chat8/backend/app/chat8_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
    
    try:
        import shutil
        shutil.copy2(db_path, backup_path)
        print(f"📦 数据库已备份到: {backup_path}")
        return backup_path
    except Exception as e:
        print(f"❌ 备份失败: {str(e)}")
        return None

if __name__ == "__main__":
    print("🚀 开始清空数据库数据...")
    print("⚠️  注意：此操作将删除所有数据但保留表结构")
    
    # 询问用户确认
    confirm = input("\n是否要继续？(y/N): ")
    if confirm.lower() != 'y':
        print("❌ 操作已取消")
        exit()
    
    # 询问是否备份
    backup_confirm = input("是否先备份数据库？(Y/n): ")
    if backup_confirm.lower() != 'n':
        backup_path = backup_database()
        if not backup_path:
            print("❌ 备份失败，操作已取消")
            exit()
    
    # 执行清空操作
    success = clear_database_data()
    
    if success:
        print("\n🎉 数据库清空完成！")
        print("💡 提示：表结构已保留，可以重新注册用户进行测试")
    else:
        print("\n❌ 数据库清空失败！")
        exit(1)