#!/usr/bin/env python3
import requests
import json

API_BASE = "http://localhost:8000/api/v1"

def login_user(username, password):
    """用户登录"""
    data = {
        "username": username,
        "password": password
    }
    
    response = requests.post(f"{API_BASE}/auth/login", json=data)
    print(f"登录 {username} - 状态: {response.status_code}")
    
    if response.status_code == 200:
        result = response.json()
        print(f"登录响应: {result}")
        # 尝试不同的token字段名
        token = result.get('access_token') or result.get('token') or result.get('data', {}).get('token')
        return token
    else:
        print(f"登录失败: {response.text}")
        return None

def get_session_key_http(token, other_user_id):
    """通过HTTP API获取会话密钥"""
    headers = {"Authorization": f"Bearer {token}"}
    
    response = requests.get(f"{API_BASE}/encryption/session-key/{other_user_id}", 
                          headers=headers)
    
    print(f"HTTP获取会话密钥 - 状态: {response.status_code}")
    print(f"响应内容: {response.text}")
    
    if response.status_code == 200:
        return response.json()['data']['session_key']
    return None

def test_http_session_keys():
    """测试HTTP API的会话密钥获取"""
    print("=== 测试HTTP API会话密钥获取 ===")
    
    # 假设用户37和38已经存在并且有会话
    # 首先需要获取他们的登录token
    
    # 这里我们需要知道用户37和38的用户名和密码
    # 从之前的测试来看，可能是testuser1_xxx和testuser2_xxx格式
    
    # 让我们先检查数据库中的用户信息
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
            return
        
        print(f"用户37: {user37.username}")
        print(f"用户38: {user38.username}")
        
        # 尝试登录（密码通常是'password123'）
        token37 = login_user(user37.username, 'password123')
        token38 = login_user(user38.username, 'password123')
        
        if not token37 or not token38:
            print("登录失败")
            return
        
        print("\n--- 用户37通过HTTP获取与用户38的会话密钥 ---")
        key37 = get_session_key_http(token37, 38)
        
        print("\n--- 用户38通过HTTP获取与用户37的会话密钥 ---")
        key38 = get_session_key_http(token38, 37)
        
        if key37 and key38:
            print(f"\n--- 密钥比较 ---")
            print(f"用户37获取的密钥: {key37}")
            print(f"用户38获取的密钥: {key38}")
            print(f"密钥一致: {key37 == key38}")
        
    finally:
        db.close()

if __name__ == "__main__":
    test_http_session_keys()