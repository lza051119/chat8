#!/usr/bin/env python3
import sys
import os
import json
import base64
sys.path.append('/Users/tsuki/Desktop/chat8/backend')

from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.asymmetric import rsa
from app.db.database import SessionLocal
from app.db.models import User

def create_simple_keys(user_id):
    """为用户创建简单的RSA密钥对"""
    try:
        # 生成RSA密钥对
        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048,
        )
        public_key = private_key.public_key()
        
        # 序列化密钥
        private_pem = private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()
        ).decode('utf-8')
        
        public_pem = public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        ).decode('utf-8')
        
        # 创建密钥目录
        keys_dir = "/Users/tsuki/Desktop/大二下/chat8/backend/user_keys"
        os.makedirs(keys_dir, exist_ok=True)
        
        # 保存密钥文件
        keys_data = {
            'identity_private_key': private_pem,
            'identity_public_key': public_pem,
            'registration_id': user_id,
            'prekey_bundle': {
                'identity_key': public_pem,
                'registration_id': user_id
            }
        }
        
        keys_file = os.path.join(keys_dir, f"user_{user_id}_keys.json")
        with open(keys_file, 'w') as f:
            json.dump(keys_data, f, indent=2)
        
        # 更新数据库中的公钥
        db = SessionLocal()
        try:
            user = db.query(User).filter(User.id == user_id).first()
            if user:
                user.public_key = public_pem
                db.commit()
                print(f"用户 {user_id} 密钥生成成功，已更新数据库")
            else:
                print(f"用户 {user_id} 不存在于数据库中")
        finally:
            db.close()
        
        return True
        
    except Exception as e:
        print(f"为用户 {user_id} 生成密钥时出错: {e}")
        return False

if __name__ == "__main__":
    # 为测试中的用户生成密钥
    if len(sys.argv) > 1:
        # 从命令行参数获取用户ID
        user_ids = [int(arg) for arg in sys.argv[1:] if arg.isdigit()]
    else:
        # 默认用户ID
        user_ids = [31, 32]
    
    for user_id in user_ids:
        create_simple_keys(user_id)
    
    # 检查密钥目录
    keys_dir = "/Users/tsuki/Desktop/大二下/chat8/backend/user_keys"
    if os.path.exists(keys_dir):
        print(f"\n密钥目录内容:")
        for file in os.listdir(keys_dir):
            file_path = os.path.join(keys_dir, file)
            if os.path.isfile(file_path):
                size = os.path.getsize(file_path)
                print(f"  {file} ({size} bytes)")
    else:
        print(f"\n密钥目录不存在: {keys_dir}")