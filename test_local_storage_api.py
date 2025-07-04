#!/usr/bin/env python3
import requests
import json

# 测试local-storage API的422错误
def test_local_storage_api():
    base_url = "http://localhost:8000/api/v1"
    
    # 1. 登录获取token
    login_data = {
        "username": "testuser1_1751584222",
        "password": "password123"
    }
    
    login_response = requests.post(f"{base_url}/auth/login", json=login_data)
    print(f"登录状态: {login_response.status_code}")
    
    if login_response.status_code != 200:
        print(f"登录失败: {login_response.text}")
        return
    
    login_result = login_response.json()
    token = login_result['data']['token']
    user_id = login_result['data']['user']['userId']
    
    print(f"登录成功，用户ID: {user_id}")
    
    # 2. 准备headers
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    # 3. 测试发送消息到local-storage API
    message_data = {
        "to": 38,  # 目标用户ID
        "content": "测试消息内容",
        "messageType": "text",
        "method": "Server",
        "encrypted": False
    }
    
    print(f"发送消息数据: {json.dumps(message_data, ensure_ascii=False, indent=2)}")
    
    response = requests.post(f"{base_url}/local-storage/messages", json=message_data, headers=headers)
    print(f"响应状态: {response.status_code}")
    print(f"响应内容: {response.text}")
    
    if response.status_code == 422:
        try:
            error_detail = response.json()
            print(f"详细错误信息: {json.dumps(error_detail, ensure_ascii=False, indent=2)}")
        except:
            print("无法解析错误详情")

if __name__ == "__main__":
    test_local_storage_api()