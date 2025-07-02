#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据迁移脚本：将JSON文件存储的消息迁移到SQLite数据库

使用方法:
1. 迁移所有用户: python migrate_to_database.py --all
2. 迁移指定用户: python migrate_to_database.py --user-id 18
3. 查看帮助: python migrate_to_database.py --help
"""

import os
import sys
import argparse
import json
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from services.message_db_service import MessageDBService

def get_json_files_directory():
    """获取JSON文件存储目录"""
    # 从脚本所在目录向上找到app目录，然后定位到local_storage/messages
    script_dir = Path(__file__).parent
    app_dir = script_dir.parent
    return os.path.join(app_dir, 'local_storage', 'messages')

def find_user_json_files():
    """查找所有用户的JSON消息文件"""
    json_dir = get_json_files_directory()
    if not os.path.exists(json_dir):
        print(f"JSON文件目录不存在: {json_dir}")
        return []
    
    user_files = []
    for filename in os.listdir(json_dir):
        if filename.startswith('user_') and filename.endswith('_messages.json'):
            try:
                # 提取用户ID
                user_id_str = filename.replace('user_', '').replace('_messages.json', '')
                user_id = int(user_id_str)
                file_path = os.path.join(json_dir, filename)
                user_files.append((user_id, file_path))
            except ValueError:
                print(f"无法解析用户ID: {filename}")
                continue
    
    return user_files

def migrate_user_data(user_id, json_file_path, backup=True):
    """迁移单个用户的数据"""
    print(f"\n开始迁移用户 {user_id} 的数据...")
    
    try:
        # 检查JSON文件是否存在
        if not os.path.exists(json_file_path):
            print(f"JSON文件不存在: {json_file_path}")
            return False
        
        # 读取JSON数据
        with open(json_file_path, 'r', encoding='utf-8') as f:
            json_messages = json.load(f)
        
        print(f"找到 {len(json_messages)} 条消息")
        
        if not json_messages:
            print("没有消息需要迁移")
            return True
        
        # 初始化数据库
        MessageDBService.init_user_database(user_id)
        
        # 迁移每条消息
        success_count = 0
        failed_count = 0
        
        for i, msg in enumerate(json_messages, 1):
            try:
                if MessageDBService.add_message(user_id, msg):
                    success_count += 1
                else:
                    failed_count += 1
                    print(f"  消息 {i} 迁移失败")
                
                # 显示进度
                if i % 10 == 0 or i == len(json_messages):
                    print(f"  进度: {i}/{len(json_messages)} ({i/len(json_messages)*100:.1f}%)")
                    
            except Exception as e:
                failed_count += 1
                print(f"  消息 {i} 迁移异常: {e}")
        
        print(f"迁移完成: 成功 {success_count} 条，失败 {failed_count} 条")
        
        # 备份原JSON文件
        if backup and success_count > 0:
            backup_path = json_file_path + '.backup'
            os.rename(json_file_path, backup_path)
            print(f"原JSON文件已备份到: {backup_path}")
        
        # 验证迁移结果
        db_status = MessageDBService.get_database_status(user_id)
        print(f"数据库状态: {db_status['message_count']} 条消息")
        
        return success_count > 0
        
    except Exception as e:
        print(f"迁移用户 {user_id} 数据时发生错误: {e}")
        return False

def migrate_all_users(backup=True):
    """迁移所有用户的数据"""
    user_files = find_user_json_files()
    
    if not user_files:
        print("没有找到需要迁移的JSON文件")
        return
    
    print(f"找到 {len(user_files)} 个用户的JSON文件需要迁移")
    
    success_users = []
    failed_users = []
    
    for user_id, json_file_path in user_files:
        if migrate_user_data(user_id, json_file_path, backup):
            success_users.append(user_id)
        else:
            failed_users.append(user_id)
    
    print(f"\n=== 迁移总结 ===")
    print(f"成功迁移用户: {success_users}")
    if failed_users:
        print(f"迁移失败用户: {failed_users}")
    print(f"总计: {len(success_users)}/{len(user_files)} 个用户迁移成功")

def check_migration_status():
    """检查迁移状态"""
    print("=== 迁移状态检查 ===")
    
    user_files = find_user_json_files()
    print(f"剩余JSON文件: {len(user_files)}")
    
    # 检查数据库文件
    db_dir = get_json_files_directory()
    db_files = [f for f in os.listdir(db_dir) if f.endswith('.db')]
    print(f"数据库文件: {len(db_files)}")
    
    for db_file in db_files:
        try:
            user_id_str = db_file.replace('user_', '').replace('_messages.db', '')
            user_id = int(user_id_str)
            status = MessageDBService.get_database_status(user_id)
            print(f"  用户 {user_id}: {status['message_count']} 条消息")
        except:
            print(f"  无法解析数据库文件: {db_file}")

def main():
    parser = argparse.ArgumentParser(description='消息数据迁移工具')
    parser.add_argument('--all', action='store_true', help='迁移所有用户的数据')
    parser.add_argument('--user-id', type=int, help='迁移指定用户的数据')
    parser.add_argument('--no-backup', action='store_true', help='不备份原JSON文件')
    parser.add_argument('--status', action='store_true', help='检查迁移状态')
    
    args = parser.parse_args()
    
    if args.status:
        check_migration_status()
        return
    
    backup = not args.no_backup
    
    if args.all:
        migrate_all_users(backup)
    elif args.user_id:
        json_dir = get_json_files_directory()
        json_file_path = os.path.join(json_dir, f'user_{args.user_id}_messages.json')
        migrate_user_data(args.user_id, json_file_path, backup)
    else:
        parser.print_help()
        print("\n请指定 --all 或 --user-id 参数")

if __name__ == '__main__':
    main()