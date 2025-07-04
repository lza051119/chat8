#!/usr/bin/env python3
import requests
import json
import time

API_BASE = "http://localhost:8000/api/v1"

def register_and_login_user(username, email, password):
    """注册并登录用户"""
    # 注册
    register_data = {
        "username": username,
        "email": email,
        "password": password
    }
    
    register_response = requests.post(f"{API_BASE}/auth/register", json=register_data)
    if register_response.status_code != 200:
        print(f"注册失败: {register_response.text}")
        return None, None
    
    register_result = register_response.json()
    user_id = register_result['data']['user']['userId']
    
    # 登录
    login_data = {
        "username": username,
        "password": password
    }
    
    login_response = requests.post(f"{API_BASE}/auth/login", json=login_data)
    if login_response.status_code != 200:
        print(f"登录失败: {login_response.text}")
        return None, None
    
    login_result = login_response.json()
    token = login_result['data']['token']
    
    return user_id, token

def establish_session(token, target_user_id):
    """建立会话密钥"""
    headers = {"Authorization": f"Bearer {token}"}
    data = {"target_user_id": target_user_id}
    
    response = requests.post(f"{API_BASE}/encryption/establish-session-manual", 
                           json=data, headers=headers)
    
    print(f"建立会话响应状态: {response.status_code}")
    print(f"建立会话响应内容: {response.text}")
    
    return response.status_code == 200

def get_session_key(token, other_user_id):
    """获取会话密钥"""
    headers = {"Authorization": f"Bearer {token}"}
    
    response = requests.get(f"{API_BASE}/encryption/session-key/{other_user_id}", 
                          headers=headers)
    
    print(f"获取会话密钥响应状态: {response.status_code}")
    print(f"获取会话密钥响应内容: {response.text}")
    
    if response.status_code == 200:
        return response.json()['data']['session_key']
    return None

def main():
    print("=== 简单会话密钥测试 ===")
    
    # 生成唯一的用户名
    timestamp = int(time.time())
    user1_name = f"testuser1_{timestamp}"
    user2_name = f"testuser2_{timestamp}"
    
    # 注册并登录两个用户
    print("\n1. 注册并登录用户...")
    user1_id, token1 = register_and_login_user(
        user1_name, f"test1_{timestamp}@example.com", "password123"
    )
    user2_id, token2 = register_and_login_user(
        user2_name, f"test2_{timestamp}@example.com", "password123"
    )
    
    if not user1_id or not user2_id:
        print("❌ 用户注册或登录失败")
        return
    
    print(f"✅ 用户1 ID: {user1_id}, 用户2 ID: {user2_id}")
    
    # 为新用户生成密钥
    print("\n2. 为新用户生成密钥...")
    import sys
    sys.path.append('/Users/tsuki/Desktop/chat8/backend')
    from create_simple_keys import create_simple_keys
    
    create_simple_keys(int(user1_id))
    create_simple_keys(int(user2_id))
    print("✅ 密钥生成完成")
    
    # 建立会话密钥
    print("\n3. 建立会话密钥...")
    if establish_session(token1, int(user2_id)):
        print("✅ 会话密钥建立成功")
    else:
        print("❌ 会话密钥建立失败")
        return
    
    # 获取会话密钥
    print("\n4. 获取会话密钥...")
    session_key1 = get_session_key(token1, int(user2_id))
    session_key2 = get_session_key(token2, int(user1_id))
    
    if session_key1 and session_key2:
        print(f"✅ 用户1获取的会话密钥: {session_key1[:20]}...")
        print(f"✅ 用户2获取的会话密钥: {session_key2[:20]}...")
        
        if session_key1 == session_key2:
            print("✅ 会话密钥一致性验证通过")
        else:
            print("❌ 会话密钥不一致")
    else:
        print("❌ 获取会话密钥失败")

if __name__ == "__main__":
    main()