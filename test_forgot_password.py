#!/usr/bin/env python3
import requests
import json
import time

# 使用一个已存在的邮箱来测试忘记密码功能
test_email = "petrichor_umut@163.com"
base_url = "http://localhost:8000/api/v1/auth"

print("=== 完整的忘记密码流程测试 ===")

# 步骤1: 发送忘记密码请求
print("\n1. 发送忘记密码请求...")
forgot_url = f"{base_url}/forgot-password"
headers = {"Content-Type": "application/json"}
data = {"email": test_email}

try:
    response = requests.post(forgot_url, headers=headers, json=data)
    print(f"状态码: {response.status_code}")
    print(f"响应: {response.text}")
    
    if response.status_code == 200:
        print("✅ 忘记密码请求发送成功！")
        
        # 从控制台日志中可以看到验证码，这里模拟用户输入
        verification_code = input("\n请输入从后端日志中看到的验证码: ")
        
        # 步骤2: 验证验证码
        print("\n2. 验证验证码...")
        verify_url = f"{base_url}/verify-reset-code"
        verify_data = {
            "email": test_email,
            "code": verification_code
        }
        
        verify_response = requests.post(verify_url, headers=headers, json=verify_data)
        print(f"验证状态码: {verify_response.status_code}")
        print(f"验证响应: {verify_response.text}")
        
        if verify_response.status_code == 200:
            print("✅ 验证码验证成功！")
            
            # 步骤3: 重置密码
            print("\n3. 重置密码...")
            reset_url = f"{base_url}/reset-password"
            new_password = "newpassword123"
            reset_data = {
                "email": test_email,
                "code": verification_code,
                "new_password": new_password
            }
            
            reset_response = requests.post(reset_url, headers=headers, json=reset_data)
            print(f"重置状态码: {reset_response.status_code}")
            print(f"重置响应: {reset_response.text}")
            
            if reset_response.status_code == 200:
                print("✅ 密码重置成功！")
                print("\n🎉 完整的忘记密码流程测试通过！")
            else:
                print("❌ 密码重置失败")
        else:
            print("❌ 验证码验证失败")
    else:
        print("❌ 忘记密码请求失败")
        
except Exception as e:
    print(f"请求错误: {e}")