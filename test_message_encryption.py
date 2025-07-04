#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试消息加解密功能
验证发送消息过程中的透明加解密是否正常工作
"""

import requests
import json
import time
from datetime import datetime

# 配置
BASE_URL = "http://localhost:8000"
API_BASE = f"{BASE_URL}/api/v1"

# 测试用户
USER1_USERNAME = "testuser1_1751584222"
USER1_PASSWORD = "password123"
USER2_USERNAME = "testuser2_1751584222"
USER2_PASSWORD = "password123"

def login_user(username, password):
    """用户登录并获取token"""
    login_data = {
        "username": username,
        "password": password
    }
    
    # 登录获取token
    response = requests.post(f"{API_BASE}/auth/login", json=login_data)
    if response.status_code == 200:
        result = response.json()
        if result.get('success'):
            token = result['data']['token']
            user_info = result['data']['user']
            headers = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
            }
            print(f"✓ 用户 {username} (ID: {user_info['userId']}) 登录成功")
            return headers, user_info
        else:
            print(f"✗ 用户 {username} 登录失败: {result.get('message')}")
            return None, None
    else:
        print(f"✗ 用户 {username} 登录失败: {response.status_code} - {response.text}")
        return None, None

def send_message_api(from_headers, to_id, content, encrypted=True, method="E2E"):
    """通过API发送消息"""
    message_data = {
        "to": to_id,
        "content": content,
        "encrypted": encrypted,
        "method": method,
        "messageType": "text"
    }
    
    response = requests.post(
        f"{API_BASE}/messages",
        headers=from_headers,
        json=message_data
    )
    
    if response.status_code == 200:
        result = response.json()
        print(f"✓ 消息发送成功: ID={result.get('id')}")
        return result
    else:
        print(f"✗ 消息发送失败: {response.status_code} - {response.text}")
        return None

def get_message_history(headers, peer_id, page=1, limit=10):
    """获取消息历史"""
    response = requests.get(
        f"{API_BASE}/messages/history/{peer_id}?page={page}&limit={limit}",
        headers=headers
    )
    
    if response.status_code == 200:
        result = response.json()
        print(f"✓ 获取消息历史成功: 共 {len(result['messages'])} 条消息")
        return result
    else:
        print(f"✗ 获取消息历史失败: {response.status_code} - {response.text}")
        return None

def test_message_encryption():
    """测试消息加解密功能"""
    print("=== 测试消息加解密功能 ===")
    print(f"测试时间: {datetime.now()}")
    print()
    
    # 1. 用户登录
    print("1. 用户登录测试")
    user1_headers, user1_info = login_user(USER1_USERNAME, USER1_PASSWORD)
    user2_headers, user2_info = login_user(USER2_USERNAME, USER2_PASSWORD)
    
    if not user1_headers or not user2_headers:
        print("✗ 用户登录失败，无法继续测试")
        return False
    
    user1_id = int(user1_info['userId'])
    user2_id = int(user2_info['userId'])
    
    print()
    
    # 2. 发送加密消息
    print("2. 发送加密消息测试")
    test_message = f"这是一条测试加密消息 - {int(time.time())}"
    
    # 用户1发送给用户2
    sent_msg = send_message_api(user1_headers, user2_id, test_message, encrypted=True, method="E2E")
    if not sent_msg:
        print("✗ 发送消息失败")
        return False
    
    print()
    
    # 3. 等待消息处理
    print("3. 等待消息处理...")
    time.sleep(2)
    
    # 4. 获取消息历史并验证解密
    print("4. 获取消息历史并验证解密")
    
    # 用户1查看发送的消息
    print("用户1查看发送的消息:")
    user1_history = get_message_history(user1_headers, user2_id, limit=5)
    if user1_history and user1_history['messages']:
        latest_msg = user1_history['messages'][0]  # 最新消息
        print(f"  消息内容: {latest_msg['content']}")
        print(f"  加密状态: {latest_msg['encrypted']}")
        print(f"  加密方法: {latest_msg['method']}")
        
        if latest_msg['content'] == test_message:
            print("✓ 用户1看到的消息内容正确（明文）")
        else:
            print(f"✗ 用户1看到的消息内容不正确")
            print(f"  期望: {test_message}")
            print(f"  实际: {latest_msg['content']}")
    
    print()
    
    # 用户2查看接收的消息
    print("用户2查看接收的消息:")
    user2_history = get_message_history(user2_headers, user1_id, limit=5)
    if user2_history and user2_history['messages']:
        latest_msg = user2_history['messages'][0]  # 最新消息
        print(f"  消息内容: {latest_msg['content']}")
        print(f"  加密状态: {latest_msg['encrypted']}")
        print(f"  加密方法: {latest_msg['method']}")
        
        if latest_msg['content'] == test_message:
            print("✓ 用户2看到的消息内容正确（已解密）")
        else:
            print(f"✗ 用户2看到的消息内容不正确")
            print(f"  期望: {test_message}")
            print(f"  实际: {latest_msg['content']}")
    
    print()
    
    # 5. 反向发送消息测试
    print("5. 反向发送消息测试")
    reverse_message = f"这是反向测试消息 - {int(time.time())}"
    
    # 用户2发送给用户1
    sent_msg2 = send_message_api(user2_headers, user1_id, reverse_message, encrypted=True, method="E2E")
    if not sent_msg2:
        print("✗ 反向发送消息失败")
        return False
    
    time.sleep(2)
    
    # 验证反向消息
    user1_history2 = get_message_history(user1_headers, user2_id, limit=5)
    if user1_history2 and user1_history2['messages']:
        latest_msg = user1_history2['messages'][0]  # 最新消息
        if latest_msg['content'] == reverse_message:
            print("✓ 反向消息解密成功")
        else:
            print(f"✗ 反向消息解密失败")
            print(f"  期望: {reverse_message}")
            print(f"  实际: {latest_msg['content']}")
    
    print()
    print("=== 测试完成 ===")
    return True

if __name__ == "__main__":
    test_message_encryption()