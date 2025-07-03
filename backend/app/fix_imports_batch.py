#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
批量修复导入语句中的\1错误
"""

import os
import re

def fix_imports_in_file(file_path):
    """修复单个文件中的导入语句"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 定义替换规则
        replacements = {
            r'from \\1 import SessionLocal': 'from db.database import SessionLocal',
            r'from \\1 import models': 'from db import models',
            r'from \\1 import User': 'from db.models import User',
            r'from \\1 import SecurityEvent': 'from db.models import SecurityEvent',
            r'from \\1 import SignalingMessage': 'from db.models import SignalingMessage',
            r'from \\1 import Friend, FriendCreate, FriendRequestCreate, FriendRequestResponse, FriendRequestOut': 'from schemas.friend import Friend, FriendCreate, FriendRequestCreate, FriendRequestResponse, FriendRequestOut',
            r'from \\1 import friend_service': 'from services import friend_service',
            r'from \\1 import get_current_user': 'from core.security import get_current_user',
            r'from \\1 import UserOut': 'from schemas.user import UserOut',
            r'from \\1 import User as UserModel': 'from db.models import User as UserModel',
            r'from \\1 import MessageCreate': 'from schemas.message import MessageCreate',
            r'from \\1 import MessageDBService': 'from services.message_db_service import MessageDBService',
            r'from \\1 import UserCreate, UserLogin, UserOut, ResponseModel': 'from schemas.user import UserCreate, UserLogin, UserOut, ResponseModel',
            r'from \\1 import register_user, authenticate_user, search_users': 'from services.user_service import register_user, authenticate_user, search_users',
            r'from \\1 import create_access_token': 'from core.security import create_access_token',
            r'from \\1 import security_event_service': 'from services import security_event_service',
            r'from \\1 import Message, MessageCreate': 'from schemas.message import Message, MessageCreate',
            r'from \\1 import message_service': 'from services import message_service',
            r'from \\1 import hash_password, verify_password': 'from core.security import hash_password, verify_password',
            r'from \\1 import TokenData': 'from schemas.user import TokenData',
            r'from \\1 import embed, extract': 'from services.steganography import embed, extract',
            r'from \\1 import decode_access_token': 'from core.security import decode_access_token',
            r'from \\1 import get_user_states_service': 'from services.user_states_update import get_user_states_service',
            r'from \\1 import ConnectionManager': 'from websocket.manager import ConnectionManager',
            r'from \\1 import get_db': 'from db.database import get_db',
            r'from \\1 import signaling_service': 'from services import signaling_service',
            r'from \\1 import OfferRequest, AnswerRequest': 'from schemas.signaling import OfferRequest, AnswerRequest',
            r'from \\1 import Key, KeyCreate': 'from schemas.key import Key, KeyCreate',
            r'from \\1 import key_service': 'from services import key_service'
        }
        
        # 应用替换
        modified = False
        for pattern, replacement in replacements.items():
            if re.search(pattern, content):
                content = re.sub(pattern, replacement, content)
                modified = True
        
        # 如果有修改，写回文件
        if modified:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"已修复: {file_path}")
            return True
        else:
            print(f"无需修复: {file_path}")
            return False
            
    except Exception as e:
        print(f"处理文件 {file_path} 时出错: {e}")
        return False

def find_python_files(directory):
    """查找目录下的所有Python文件"""
    python_files = []
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith('.py'):
                python_files.append(os.path.join(root, file))
    return python_files

def main():
    # 获取当前脚本所在目录
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    # 查找所有Python文件
    python_files = find_python_files(script_dir)
    
    print(f"找到 {len(python_files)} 个Python文件")
    
    fixed_count = 0
    for file_path in python_files:
        if fix_imports_in_file(file_path):
            fixed_count += 1
    
    print(f"\n修复完成！共修复了 {fixed_count} 个文件")

if __name__ == "__main__":
    main()