#!/usr/bin/env python3
"""
测试注册API的调试脚本
"""

import requests
import json

def test_register():
    """测试用户注册API"""
    url = "http://localhost:8001/api/v1/auth/register"
    
    import time
    timestamp = int(time.time())
    data = {
        "username": f"testuser_{timestamp}",
        "email": f"test_{timestamp}@example.com",
        "password": "testpass123"
    }
    
    headers = {
        "Content-Type": "application/json"
    }
    
    try:
        print(f"发送注册请求到: {url}")
        print(f"请求数据: {json.dumps(data, indent=2)}")
        
        response = requests.post(url, json=data, headers=headers)
        
        print(f"\n响应状态码: {response.status_code}")
        print(f"响应头: {dict(response.headers)}")
        
        try:
            response_data = response.json()
            print(f"响应内容: {json.dumps(response_data, indent=2, ensure_ascii=False)}")
        except json.JSONDecodeError:
            print(f"响应内容 (原始): {response.text}")
            
    except requests.exceptions.RequestException as e:
        print(f"请求失败: {e}")
    except Exception as e:
        print(f"其他错误: {e}")

if __name__ == "__main__":
    test_register()