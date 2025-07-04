#!/usr/bin/env python3
import sys
import json
import base64
sys.path.append('/Users/tsuki/Desktop/chat8/backend')

from app.db.database import SessionLocal
from app.db.models import SessionKey, User
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.asymmetric import padding

def debug_session_decryption(session_id):
    """调试会话密钥解密过程"""
    print(f"\n=== 调试会话 {session_id} 的解密过程 ===")
    
    db = SessionLocal()
    try:
        # 获取会话记录
        session_record = db.query(SessionKey).filter(SessionKey.id == session_id).first()
        if not session_record:
            print(f"会话 {session_id} 不存在")
            return
        
        print(f"会话用户: {session_record.user1_id} <-> {session_record.user2_id}")
        
        # 获取用户信息
        user1 = db.query(User).filter(User.id == session_record.user1_id).first()
        user2 = db.query(User).filter(User.id == session_record.user2_id).first()
        
        # 测试用户1的解密
        print(f"\n--- 测试用户 {session_record.user1_id} 的解密 ---")
        test_user_decryption(session_record.user1_id, session_record, user1.public_key)
        
        # 测试用户2的解密
        print(f"\n--- 测试用户 {session_record.user2_id} 的解密 ---")
        test_user_decryption(session_record.user2_id, session_record, user2.public_key)
        
    finally:
        db.close()

def test_user_decryption(user_id, session_record, db_public_key):
    """测试特定用户的解密过程"""
    try:
        # 读取用户的私钥文件
        keys_file = f"/Users/tsuki/Desktop/大二下/chat8/backend/user_keys/user_{user_id}_keys.json"
        with open(keys_file, 'r') as f:
            keys_data = json.load(f)
        
        file_private_key = keys_data.get('identity_private_key')
        file_public_key = keys_data.get('identity_public_key')
        
        print(f"数据库公钥存在: {bool(db_public_key)}")
        print(f"文件私钥存在: {bool(file_private_key)}")
        print(f"文件公钥存在: {bool(file_public_key)}")
        
        # 检查公钥是否匹配
        if db_public_key and file_public_key:
            keys_match = db_public_key.strip() == file_public_key.strip()
            print(f"数据库和文件公钥匹配: {keys_match}")
            if not keys_match:
                print("❌ 公钥不匹配，这会导致解密失败")
                return
        
        # 尝试解密
        if file_private_key:
            private_key_obj = serialization.load_pem_private_key(file_private_key.encode(), password=None)
            
            # 确定使用哪个加密的会话密钥
            if session_record.user1_id == user_id:
                encrypted_session_key = base64.b64decode(session_record.session_key_encrypted)
                print(f"使用 session_key_encrypted (用户1的密钥)")
            else:
                encrypted_session_key = base64.b64decode(session_record.session_key_encrypted_for_user2)
                print(f"使用 session_key_encrypted_for_user2 (用户2的密钥)")
            
            print(f"加密密钥长度: {len(encrypted_session_key)} bytes")
            
            # 尝试解密
            try:
                session_key = private_key_obj.decrypt(
                    encrypted_session_key,
                    padding.OAEP(
                        mgf=padding.MGF1(algorithm=hashes.SHA256()),
                        algorithm=hashes.SHA256(),
                        label=None
                    )
                )
                
                session_key_b64 = base64.b64encode(session_key).decode()
                print(f"✅ 解密成功: {session_key_b64}")
                
            except Exception as decrypt_error:
                print(f"❌ 解密失败: {decrypt_error}")
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")

def find_latest_session():
    """找到最新的会话记录"""
    db = SessionLocal()
    try:
        latest_session = db.query(SessionKey).order_by(SessionKey.id.desc()).first()
        if latest_session:
            return latest_session.id
        return None
    finally:
        db.close()

if __name__ == "__main__":
    # 找到最新的会话并调试
    latest_session_id = find_latest_session()
    if latest_session_id:
        print(f"调试最新会话: {latest_session_id}")
        debug_session_decryption(latest_session_id)
    else:
        print("没有找到会话记录")