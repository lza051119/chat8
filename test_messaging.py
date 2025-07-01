#!/usr/bin/env python3
"""
测试消息功能的脚本
用于验证用户注册、登录、添加好友和发送消息的完整流程
"""

import requests
import json
import time

BASE_URL = "http://localhost:8000/api"

def register_user(username, email, password):
    """注册用户"""
    url = f"{BASE_URL}/auth/register"
    data = {
        "username": username,
        "email": email,
        "password": password
    }
    response = requests.post(url, json=data)
    return response.json()

def login_user(username, password):
    """用户登录"""
    url = f"{BASE_URL}/auth/login"
    data = {
        "username": username,
        "password": password
    }
    response = requests.post(url, json=data)
    return response.json()

def add_friend(token, to_user_id):
    """发送好友申请"""
    url = f"{BASE_URL}/contacts/request"
    headers = {"Authorization": f"Bearer {token}"}
    data = {"to_user_id": to_user_id, "message": "测试好友申请"}
    response = requests.post(url, json=data, headers=headers)
    return response.json()

def send_message(token, to_id, content):
    """发送消息"""
    url = f"{BASE_URL}/messages"
    headers = {"Authorization": f"Bearer {token}"}
    data = {
        "to": to_id,
        "content": content,
        "encrypted": True
    }
    response = requests.post(url, json=data, headers=headers)
    return response.json()

def get_message_history(token, peer_id):
    """获取消息历史"""
    url = f"{BASE_URL}/messages/history/{peer_id}"
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(url, headers=headers)
    return response.json()

def main():
    print("=== 开始测试消息功能 ===")
    
    # 1. 注册两个测试用户
    print("\n1. 注册测试用户...")
    
    # 使用时间戳确保用户名唯一
    import time
    timestamp = str(int(time.time()))
    
    user1_data = register_user(f"testuser1_{timestamp}", f"test1_{timestamp}@example.com", "password123")
    print(f"用户1注册结果: {user1_data}")
    
    user2_data = register_user(f"testuser2_{timestamp}", f"test2_{timestamp}@example.com", "password123")
    print(f"用户2注册结果: {user2_data}")
    
    # 2. 用户登录
    print("\n2. 用户登录...")
    
    login1 = login_user(f"testuser1_{timestamp}", "password123")
    print(f"用户1登录结果: {login1}")
    
    login2 = login_user(f"testuser2_{timestamp}", "password123")
    print(f"用户2登录结果: {login2}")
    
    if not login1.get('success') or not login2.get('success'):
        print("登录失败，停止测试")
        return
    
    token1 = login1['data']['token']
    token2 = login2['data']['token']
    user1_id = login1['data']['user']['userId']
    user2_id = login2['data']['user']['userId']
    
    print(f"用户1 ID: {user1_id}, Token: {token1[:20]}...")
    print(f"用户2 ID: {user2_id}, Token: {token2[:20]}...")
    
    # 3. 添加好友关系
    print("\n3. 添加好友关系...")
    
    friend_result1 = add_friend(token1, user2_id)
    print(f"用户1添加用户2为好友: {friend_result1}")
    
    friend_result2 = add_friend(token2, user1_id)
    print(f"用户2添加用户1为好友: {friend_result2}")
    
    # 4. 发送消息
    print("\n4. 发送测试消息...")
    
    # 用户1发送消息给用户2
    msg1 = send_message(token1, user2_id, "你好，这是来自用户1的测试消息！")
    print(f"用户1发送消息: {msg1}")
    
    time.sleep(1)  # 等待一秒
    
    # 用户2发送消息给用户1
    msg2 = send_message(token2, user1_id, "收到！这是来自用户2的回复消息。")
    print(f"用户2发送消息: {msg2}")
    
    # 5. 获取消息历史
    print("\n5. 获取消息历史...")
    
    # 用户1获取与用户2的消息历史
    history1 = get_message_history(token1, user2_id)
    print(f"用户1的消息历史: {history1}")
    
    # 用户2获取与用户1的消息历史
    history2 = get_message_history(token2, user1_id)
    print(f"用户2的消息历史: {history2}")
    
    print("\n=== 测试完成 ===")
    
    # 验证消息是否正确存储和获取
    if history1.get('success') and history2.get('success'):
        messages1 = history1.get('data', {}).get('messages', [])
        messages2 = history2.get('data', {}).get('messages', [])
        
        print(f"\n消息验证:")
        print(f"用户1看到的消息数量: {len(messages1)}")
        print(f"用户2看到的消息数量: {len(messages2)}")
        
        if len(messages1) >= 2 and len(messages2) >= 2:
            print("✅ 消息功能测试成功！双方都能看到完整的消息历史。")
        else:
            print("❌ 消息功能测试失败！消息历史不完整。")
    else:
        print("❌ 无法获取消息历史，测试失败。")

if __name__ == "__main__":
    main()