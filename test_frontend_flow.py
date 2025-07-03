#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
模拟前端重置密码流程的测试脚本
测试先验证验证码，再重置密码的完整流程
"""

import requests
import json

BASE_URL = "http://localhost:8000/api/v1"
TEST_EMAIL = "future_234@qq.com"
NEW_PASSWORD = "newpassword123"

def test_frontend_reset_flow():
    print("=== 模拟前端重置密码流程测试 ===")
    
    # 步骤1: 发送验证码
    print("\n1. 发送验证码...")
    forgot_response = requests.post(
        f"{BASE_URL}/auth/forgot-password",
        json={"email": TEST_EMAIL},
        headers={"Content-Type": "application/json"}
    )
    
    print(f"发送验证码状态码: {forgot_response.status_code}")
    print(f"发送验证码响应: {forgot_response.text}")
    
    if forgot_response.status_code != 200:
        print("❌ 发送验证码失败")
        return
    
    # 步骤2: 用户输入验证码
    verification_code = input("\n2. 请检查邮箱并输入收到的验证码: ")
    
    # 步骤3: 验证验证码（模拟前端验证步骤）
    print("\n3. 验证验证码...")
    verify_response = requests.post(
        f"{BASE_URL}/auth/verify-reset-code",
        json={
            "email": TEST_EMAIL,
            "code": verification_code
        },
        headers={"Content-Type": "application/json"}
    )
    
    print(f"验证验证码状态码: {verify_response.status_code}")
    print(f"验证验证码响应: {verify_response.text}")
    
    if verify_response.status_code != 200:
        print("❌ 验证码验证失败")
        return
    
    print("✅ 验证码验证成功!")
    
    # 步骤4: 重置密码（使用相同的验证码）
    print("\n4. 重置密码...")
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
    
    if reset_response.status_code == 200:
        print("✅ 密码重置成功!")
    else:
        print("❌ 密码重置失败")
        try:
            error_data = reset_response.json()
            print(f"错误详情: {error_data}")
        except:
            print(f"原始错误响应: {reset_response.text}")
    
    print("\n=== 测试完成 ===")

if __name__ == "__main__":
    test_frontend_reset_flow()