#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试重置密码后能否正常登录
"""

import requests
import json
# 测试配置
BASE_URL = "http://localhost:8000/api/v1"
TEST_EMAIL = "future_234@qq.com"
TEST_USERNAME = "user"  # 使用正确的用户名
NEW_PASSWORD = "newpassword123"

def test_reset_password_and_login():
    print("=== 测试重置密码后登录功能 ===")
    
    # 步骤1: 发送验证码
    print("\n1. 发送验证码...")
    forgot_response = requests.post(
        f"{BASE_URL}/auth/forgot-password",
        json={"email": TEST_EMAIL},
        headers={"Content-Type": "application/json"}
    )
    
    print(f"发送验证码状态码: {forgot_response.status_code}")
    if forgot_response.status_code != 200:
        print("❌ 发送验证码失败")
        return
    
    # 步骤2: 用户输入验证码
    verification_code = input("\n2. 请检查邮箱并输入收到的验证码: ")
    
    # 步骤3: 重置密码
    print("\n3. 重置密码...")
    reset_response = requests.post(
        f"{BASE_URL}/auth/reset-password",
        json={
            "email": TEST_EMAIL,
            "code": verification_code,
            "new_password": NEW_PASSWORD
        },
        headers={"Content-Type": "application/json"}
    )
    
    print(f"重置密码状态码: {reset_response.status_code}")
    print(f"重置密码响应: {reset_response.text}")
    
    if reset_response.status_code != 200:
        print("❌ 密码重置失败")
        return
    
    print("✅ 密码重置成功!")
    
    # 步骤4: 使用新密码登录
    print("\n4. 使用新密码登录...")
    login_response = requests.post(
        f"{BASE_URL}/auth/login",
        json={
            "username": TEST_USERNAME,
            "password": NEW_PASSWORD
        },
        headers={"Content-Type": "application/json"}
    )
    
    print(f"登录状态码: {login_response.status_code}")
    print(f"登录响应: {login_response.text}")
    
    if login_response.status_code == 200:
        print("✅ 使用新密码登录成功!")
        try:
            login_data = login_response.json()
            if 'data' in login_data and 'access_token' in login_data['data']:
                print(f"获得访问令牌: {login_data['data']['access_token'][:20]}...")
        except:
            pass
    else:
        print("❌ 使用新密码登录失败")
        try:
            error_data = login_response.json()
            print(f"登录错误详情: {error_data}")
        except:
            print(f"原始登录错误响应: {login_response.text}")
    
    print("\n=== 测试完成 ===")

if __name__ == "__main__":
    test_reset_password_and_login()