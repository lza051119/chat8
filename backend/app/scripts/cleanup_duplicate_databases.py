#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
清理重复的数据库文件脚本

这个脚本用于清理由于相对路径配置导致的多余数据库文件。
现在数据库配置已修改为绝对路径，只会在 backend/app/chat8.db 创建数据库。
"""

import os
import sys

def cleanup_duplicate_databases():
    """
    清理项目中的重复数据库文件
    """
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
    
    # 需要删除的重复数据库文件路径
    duplicate_db_files = [
        os.path.join(project_root, 'chat8.db'),  # 项目根目录
        os.path.join(project_root, 'backend', 'chat8.db'),  # backend目录
    ]
    
    print("=== 清理重复数据库文件 ===")
    
    for db_file in duplicate_db_files:
        if os.path.exists(db_file):
            try:
                os.remove(db_file)
                print(f"✅ 已删除: {db_file}")
            except Exception as e:
                print(f"❌ 删除失败 {db_file}: {e}")
        else:
            print(f"ℹ️  文件不存在: {db_file}")
    
    # 确认正确的数据库文件位置
    correct_db_path = os.path.join(project_root, 'backend', 'app', 'chat8.db')
    if os.path.exists(correct_db_path):
        print(f"✅ 正确的数据库文件存在: {correct_db_path}")
    else:
        print(f"⚠️  正确的数据库文件不存在: {correct_db_path}")
        print("   请运行 'python init_db.py' 来创建数据库")
    
    print("\n=== 清理完成 ===")
    print("现在所有数据库操作都将使用统一的数据库文件:")
    print(f"  {correct_db_path}")

if __name__ == "__main__":
    cleanup_duplicate_databases()