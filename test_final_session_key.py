#!/usr/bin/env python3
import requests
import json

API_BASE = "http://localhost:8000/api/v1"

def login_user(username, password):
    """用户登录"""
    data = {"username": username, "password": password}
    response = requests.post(f"{API_BASE}/auth/login", json=data)
    
    if response.status_code == 200:
        result = response.json()
        return result['data']['token']
    return None

def establish_session(token, target_user_id):
    """建立会话"""
    headers = {"Authorization": f"Bearer {token}"}
    data = {"target_user_id": target_user_id}
    
    response = requests.post(f"{API_BASE}/encryption/establish-session-manual", 
                           json=data, headers=headers)
    return response.status_code == 200

def get_session_key(token, other_user_id):
    """获取会话密钥"""
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{API_BASE}/encryption/session-key/{other_user_id}", 
                          headers=headers)
    
    if response.status_code == 200:
        return response.json()['data']['session_key']
    else:
        print(f"获取会话密钥失败: {response.status_code} - {response.text}")
        return None

def test_session_key_fix():
    """测试会话密钥修复"""
    print("=== 测试会话密钥修复 ===")
    
    # 使用已存在的用户37和38（之前测试成功的用户）
    import sys
    sys.path.append('/Users/tsuki/Desktop/chat8/backend')
    
    from app.db.database import SessionLocal
    from app.db.models import User
    
    db = SessionLocal()
    try:
        user37 = db.query(User).filter(User.id == 37).first()
        user38 = db.query(User).filter(User.id == 38).first()
        
        if not user37 or not user38:
            print("用户37或38不存在")
            return False
        
        print(f"用户37: {user37.username}")
        print(f"用户38: {user38.username}")
        
        # 登录两个用户
        token37 = login_user(user37.username, 'password123')
        token38 = login_user(user38.username, 'password123')
        
        if not token37 or not token38:
            print("登录失败")
            return False
        
        print("✅ 两个用户登录成功")
        
        # 建立会话
        if establish_session(token37, 38):
            print("✅ 会话建立成功")
        else:
            print("❌ 会话建立失败")
            return False
        
        # 测试双向获取会话密钥
        print("\n--- 测试双向获取会话密钥 ---")
        
        key37 = get_session_key(token37, 38)
        key38 = get_session_key(token38, 37)
        
        if key37 and key38:
            print(f"✅ 用户37获取密钥成功: {key37[:20]}...")
            print(f"✅ 用户38获取密钥成功: {key38[:20]}...")
            
            if key37 == key38:
                print("✅ 密钥一致，修复成功！")
                return True
            else:
                print("❌ 密钥不一致")
                return False
        else:
            print("❌ 获取会话密钥失败")
            return False
        
    finally:
        db.close()

if __name__ == "__main__":
    success = test_session_key_fix()
    if success:
        print("\n🎉 会话密钥功能修复验证成功！")
    else:
        print("\n❌ 会话密钥功能仍有问题")