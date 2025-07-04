#!/usr/bin/env python3
import sys
sys.path.append('/Users/tsuki/Desktop/chat8/backend')

from app.core.security import get_current_user
from app.services.encryption_service import encryption_service
from fastapi import Depends
import requests

def test_user_id_types():
    """测试用户ID类型问题"""
    print("=== 测试用户ID类型问题 ===")
    
    # 模拟获取token
    API_BASE = "http://localhost:8000/api/v1"
    
    # 登录用户37
    login_data = {
        "username": "testuser1_1751584222",
        "password": "password123"
    }
    
    response = requests.post(f"{API_BASE}/auth/login", json=login_data)
    if response.status_code != 200:
        print(f"登录失败: {response.text}")
        return
    
    token = response.json()['data']['token']
    print(f"获取到token: {token[:50]}...")
    
    # 测试通过token获取用户信息
    headers = {"Authorization": f"Bearer {token}"}
    me_response = requests.get(f"{API_BASE}/auth/me", headers=headers)
    
    if me_response.status_code == 200:
        user_info = me_response.json()
        print(f"用户信息: {user_info}")
        user_id = user_info.get('userId') or user_info.get('id')
        print(f"用户ID类型: {type(user_id)}, 值: {user_id}")
    
    # 直接测试加密服务
    print("\n--- 直接测试加密服务 ---")
    
    # 使用字符串ID
    print("使用字符串ID '37':")
    try:
        result1 = encryption_service.get_session_key('37', 38)
        print(f"结果: {result1}")
    except Exception as e:
        print(f"错误: {e}")
    
    # 使用整数ID
    print("\n使用整数ID 37:")
    try:
        result2 = encryption_service.get_session_key(37, 38)
        print(f"结果: {result2}")
    except Exception as e:
        print(f"错误: {e}")

if __name__ == "__main__":
    test_user_id_types()