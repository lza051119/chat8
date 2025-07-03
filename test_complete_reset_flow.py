#!/usr/bin/env python3

import requests
import json
import time

# 配置
BASE_URL = "http://localhost:8000/api"
TEST_EMAIL = "future_234@qq.com"
NEW_PASSWORD = "newpassword123"

def test_complete_reset_flow():
    print("=== 完整重置密码流程测试 ===")
    
    # 步骤1: 发送验证码
    print("\n1. 发送验证码...")
    forgot_response = requests.post(
        f"{BASE_URL}/v1/auth/forgot-password",
        json={"email": TEST_EMAIL},
        headers={"Content-Type": "application/json"}
    )
    
    print(f"发送验证码状态码: {forgot_response.status_code}")
    print(f"发送验证码响应: {forgot_response.text}")
    
    if forgot_response.status_code != 200:
        print("❌ 发送验证码失败")
        return False
    
    # 步骤2: 等待用户输入验证码
    print("\n2. 请检查邮箱并输入收到的验证码:")
    verification_code = input("验证码: ").strip()
    
    if not verification_code:
        print("❌ 验证码不能为空")
        return False
    
    # 步骤3: 重置密码
    print("\n3. 重置密码...")
    reset_response = requests.post(
        f"{BASE_URL}/v1/auth/reset-password",
        json={
            "email": TEST_EMAIL,
            "code": verification_code,
            "new_password": NEW_PASSWORD
        },
        headers={"Content-Type": "application/json"}
    )
    
    print(f"重置密码状态码: {reset_response.status_code}")
    print(f"重置密码响应: {reset_response.text}")
    
    if reset_response.status_code == 200:
        try:
            response_data = reset_response.json()
            if response_data.get('success'):
                print("✅ 密码重置成功!")
                return True
            else:
                print(f"❌ 密码重置失败: {response_data.get('message', '未知错误')}")
                return False
        except json.JSONDecodeError:
            print("❌ 响应格式错误")
            return False
    else:
        try:
            error_data = reset_response.json()
            print(f"❌ 密码重置失败: {error_data.get('message', error_data.get('detail', '未知错误'))}")
        except json.JSONDecodeError:
            print(f"❌ 密码重置失败: HTTP {reset_response.status_code}")
        return False

def test_login_with_new_password():
    print("\n=== 测试新密码登录 ===")
    
    login_response = requests.post(
        f"{BASE_URL}/v1/auth/login",
        json={
            "email": TEST_EMAIL,
            "password": NEW_PASSWORD
        },
        headers={"Content-Type": "application/json"}
    )
    
    print(f"登录状态码: {login_response.status_code}")
    print(f"登录响应: {login_response.text}")
    
    if login_response.status_code == 200:
        try:
            response_data = login_response.json()
            if response_data.get('success'):
                print("✅ 新密码登录成功!")
                return True
            else:
                print(f"❌ 新密码登录失败: {response_data.get('message', '未知错误')}")
                return False
        except json.JSONDecodeError:
            print("❌ 登录响应格式错误")
            return False
    else:
        try:
            error_data = login_response.json()
            print(f"❌ 新密码登录失败: {error_data.get('message', error_data.get('detail', '未知错误'))}")
        except json.JSONDecodeError:
            print(f"❌ 新密码登录失败: HTTP {login_response.status_code}")
        return False

if __name__ == "__main__":
    # 测试完整的重置密码流程
    reset_success = test_complete_reset_flow()
    
    if reset_success:
        # 如果重置成功，测试新密码登录
        test_login_with_new_password()
    
    print("\n=== 测试完成 ===")