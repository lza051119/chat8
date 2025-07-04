#!/usr/bin/env python3
import sys
import json
sys.path.append('/Users/tsuki/Desktop/chat8/backend')

from app.db.database import SessionLocal
from app.db.models import User

def check_user_keys(user_id):
    """检查用户的数据库公钥和文件密钥是否匹配"""
    print(f"\n=== 检查用户 {user_id} 的密钥 ===")
    
    # 从数据库获取公钥
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            print(f"用户 {user_id} 不存在于数据库中")
            return
        
        db_public_key = user.public_key
        print(f"数据库公钥存在: {bool(db_public_key)}")
        if db_public_key:
            print(f"数据库公钥前50字符: {db_public_key[:50]}...")
    finally:
        db.close()
    
    # 从文件获取密钥
    keys_file = f"/Users/tsuki/Desktop/大二下/chat8/backend/user_keys/user_{user_id}_keys.json"
    try:
        with open(keys_file, 'r') as f:
            keys_data = json.load(f)
        
        file_public_key = keys_data.get('identity_public_key')
        file_private_key = keys_data.get('identity_private_key')
        
        print(f"文件公钥存在: {bool(file_public_key)}")
        print(f"文件私钥存在: {bool(file_private_key)}")
        
        if file_public_key:
            print(f"文件公钥前50字符: {file_public_key[:50]}...")
        
        # 检查公钥是否一致
        if db_public_key and file_public_key:
            if db_public_key.strip() == file_public_key.strip():
                print("✅ 数据库和文件中的公钥一致")
            else:
                print("❌ 数据库和文件中的公钥不一致")
                print("这可能导致解密失败")
        
    except Exception as e:
        print(f"读取密钥文件失败: {e}")

def test_key_pair_validity(user_id):
    """测试密钥对的有效性"""
    print(f"\n=== 测试用户 {user_id} 密钥对有效性 ===")
    
    try:
        from cryptography.hazmat.primitives import serialization, hashes
        from cryptography.hazmat.primitives.asymmetric import padding
        import base64
        
        # 读取密钥文件
        keys_file = f"/Users/tsuki/Desktop/大二下/chat8/backend/user_keys/user_{user_id}_keys.json"
        with open(keys_file, 'r') as f:
            keys_data = json.load(f)
        
        private_key_pem = keys_data.get('identity_private_key')
        public_key_pem = keys_data.get('identity_public_key')
        
        if not private_key_pem or not public_key_pem:
            print("❌ 密钥不完整")
            return
        
        # 加载密钥
        private_key = serialization.load_pem_private_key(private_key_pem.encode(), password=None)
        public_key = serialization.load_pem_public_key(public_key_pem.encode())
        
        # 测试加密解密
        test_message = b"Hello, World!"
        
        # 用公钥加密
        encrypted = public_key.encrypt(
            test_message,
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None
            )
        )
        
        # 用私钥解密
        decrypted = private_key.decrypt(
            encrypted,
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None
            )
        )
        
        if decrypted == test_message:
            print("✅ 密钥对有效，加密解密测试通过")
        else:
            print("❌ 密钥对无效，解密结果不匹配")
            
    except Exception as e:
        print(f"❌ 密钥对测试失败: {e}")

if __name__ == "__main__":
    # 检查最近的用户
    user_ids = [37, 38]
    
    for user_id in user_ids:
        check_user_keys(user_id)
        test_key_pair_validity(user_id)