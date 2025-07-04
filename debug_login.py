#!/usr/bin/env python3
import requests
import json
import random
import string

def generate_random_username():
    return 'testuser_' + str(random.randint(1000000000, 9999999999))

def test_login_debug():
    base_url = "http://localhost:8000"
    
    # 先注册一个用户
    username = generate_random_username()
    register_data = {
        "username": username,
        "email": f"{username}@test.com",
        "password": "testpass123"
    }
    
    print(f"🔐 调试登录测试")
    print("=" * 50)
    print(f"🧪 注册用户: {username}")
    
    try:
        # 注册
        response = requests.post(f"{base_url}/api/v1/auth/register", json=register_data)
        print(f"注册响应状态码: {response.status_code}")
        
        if response.status_code != 200:
            print(f"❌ 注册失败: {response.text}")
            return
        
        print("✅ 注册成功")
        
        # 登录
        login_data = {
            "username": username,
            "password": "testpass123"
        }
        
        print(f"🧪 登录用户: {username}")
        response = requests.post(f"{base_url}/api/v1/auth/login", json=login_data)
        print(f"登录响应状态码: {response.status_code}")
        
        if response.status_code == 200:
            print("✅ 登录成功")
            try:
                data = response.json()
                print(f"响应数据类型: {type(data)}")
                print(f"响应数据: {data}")
            except Exception as e:
                print(f"❌ 解析响应JSON失败: {e}")
                print(f"原始响应: {response.text}")
        else:
            print(f"❌ 登录失败: {response.text}")
            
    except Exception as e:
        print(f"❌ 测试异常: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_login_debug()