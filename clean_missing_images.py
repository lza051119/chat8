#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
清理本地数据库中文件不存在的图片记录
"""

import sqlite3
import os
import glob
from pathlib import Path

def clean_missing_images():
    """清理本地数据库中文件不存在的图片记录"""
    
    # 本地数据库目录
    db_dir = Path("backend/app/local_storage/messages")
    
    # 静态图片目录
    static_images_dir = Path("backend/app/static/images")
    
    if not db_dir.exists():
        print(f"数据库目录不存在: {db_dir}")
        return
    
    if not static_images_dir.exists():
        print(f"静态图片目录不存在: {static_images_dir}")
        return
    
    # 查找所有用户数据库文件
    db_files = list(db_dir.glob("user_*_messages.db"))
    
    total_deleted = 0
    
    for db_file in db_files:
        print(f"\n检查数据库: {db_file.name}")
        
        try:
            conn = sqlite3.connect(str(db_file))
            cursor = conn.cursor()
            
            # 查询所有有文件路径的图片消息
            cursor.execute("""
                SELECT id, file_path, content 
                FROM messages 
                WHERE message_type = 'image' 
                AND file_path IS NOT NULL 
                AND file_path != ''
            """)
            
            records = cursor.fetchall()
            deleted_count = 0
            
            for record_id, file_path, content in records:
                # 构建完整的文件路径
                full_path = static_images_dir / file_path
                
                # 检查文件是否存在
                if not full_path.exists():
                    print(f"  删除记录 ID {record_id}: {file_path} (文件不存在)")
                    
                    # 删除数据库记录
                    cursor.execute("DELETE FROM messages WHERE id = ?", (record_id,))
                    deleted_count += 1
                else:
                    print(f"  保留记录 ID {record_id}: {file_path} (文件存在)")
            
            # 提交更改
            conn.commit()
            conn.close()
            
            print(f"  从 {db_file.name} 删除了 {deleted_count} 条记录")
            total_deleted += deleted_count
            
        except Exception as e:
            print(f"  处理 {db_file.name} 时出错: {e}")
    
    print(f"\n总共删除了 {total_deleted} 条无效图片记录")
    
    # 显示当前存在的图片文件
    print("\n当前存在的图片文件:")
    for user_dir in static_images_dir.iterdir():
        if user_dir.is_dir():
            image_files = list(user_dir.glob("*.png")) + list(user_dir.glob("*.jpg")) + list(user_dir.glob("*.jpeg"))
            if image_files:
                print(f"  用户 {user_dir.name}: {len(image_files)} 个文件")
                for img_file in image_files[:5]:  # 只显示前5个
                    print(f"    - {img_file.name}")
                if len(image_files) > 5:
                    print(f"    ... 还有 {len(image_files) - 5} 个文件")

if __name__ == "__main__":
    clean_missing_images()