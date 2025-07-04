#!/usr/bin/env python3
import requests
import json
import time

def test_simple_register():
    """简单的用户注册测试"""
    base_url = "http://localhost:8000"
    
    # 生成唯一用户名
    timestamp = int(time.time())
    username = f"testuser_{timestamp}"
    
    print(f"🧪 测试用户注册: {username}")
    
    # 注册用户
    register_data = {
        "username": username,
        "email": f"{username}@test.com",
        "password": "testpass123"
    }
    
    try:
        response = requests.post(f"{base_url}/api/v1/auth/register", json=register_data)
        print(f"注册响应状态码: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ 注册成功: {data.get('message')}")
            print(f"用户ID: {data.get('data', {}).get('user', {}).get('userId')}")
            return True
        else:
            print(f"❌ 注册失败: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ 注册异常: {str(e)}")
        return False

if __name__ == "__main__":
    print("🔐 简单用户注册测试")
    print("=" * 50)
    
    success = test_simple_register()
    
    if success:
        print("\n✅ 测试通过")
    else:
        print("\n❌ 测试失败")