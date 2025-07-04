#!/usr/bin/env python3
import sys
import os
sys.path.append('/Users/tsuki/Desktop/chat8/backend')

from app.services.encryption_service import encryption_service

def fix_user_keys(user_id):
    """为指定用户生成密钥"""
    print(f"正在为用户 {user_id} 生成密钥...")
    result = encryption_service.setup_user_encryption(user_id)
    print(f"用户 {user_id} 密钥生成结果: {result}")
    return result

if __name__ == "__main__":
    # 为测试中的用户生成密钥
    user_ids = [31, 32]  # 根据测试日志中的用户ID
    
    for user_id in user_ids:
        try:
            fix_user_keys(user_id)
        except Exception as e:
            print(f"为用户 {user_id} 生成密钥时出错: {e}")
    
    # 检查密钥目录
    keys_dir = "/Users/tsuki/Desktop/大二下/chat8/backend/user_keys"
    if os.path.exists(keys_dir):
        print(f"\n密钥目录内容:")
        for file in os.listdir(keys_dir):
            print(f"  {file}")
    else:
        print(f"\n密钥目录不存在: {keys_dir}")