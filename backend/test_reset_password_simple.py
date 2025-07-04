#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import requests
import json

def test_forgot_password_flow():
    base_url = "http://127.0.0.1:8000/api/v1"
    test_email = "future_234@qq.com"
    
    print("=== 忘记密码功能测试 ===")
    print(f"测试邮箱: {test_email}")
    
    # 步骤1: 发送忘记密码请求
    print("\n1. 发送忘记密码请求...")
    forgot_password_url = f"{base_url}/auth/forgot-password"
    
    payload = {"email": test_email}
    
    try:
        response = requests.post(
            forgot_password_url,
            json=payload,
            headers={"Content-Type": "application/json"}
        )
        
        print(f"状态码: {response.status_code}")
        print(f"响应内容: {response.text}")
        
        if response.status_code == 200:
            print("验证码发送成功！")
            response_data = response.json()
            print(f"响应数据: {json.dumps(response_data, indent=2, ensure_ascii=False)}")
            
            # 提示用户输入验证码
            print("\n请检查邮箱并输入收到的6位验证码:")
            verification_code = input("验证码: ").strip()
            
            if len(verification_code) == 6 and verification_code.isdigit():
                # 步骤2: 验证验证码
                print("\n2. 验证验证码...")
                verify_url = f"{base_url}/auth/verify-reset-code"
                verify_payload = {
                    "email": test_email,
                    "code": verification_code
                }
                
                verify_response = requests.post(
                    verify_url,
                    json=verify_payload,
                    headers={"Content-Type": "application/json"}
                )
                
                print(f"验证状态码: {verify_response.status_code}")
                print(f"验证响应: {verify_response.text}")
                
                if verify_response.status_code == 200:
                    print("验证码验证成功！")
                    
                    # 步骤3: 重置密码
                    print("\n3. 重置密码...")
                    new_password = "newpassword123"
                    reset_url = f"{base_url}/auth/reset-password"
                    reset_payload = {
                        "email": test_email,
                        "code": verification_code,
                        "new_password": new_password
                    }
                    
                    reset_response = requests.post(
                        reset_url,
                        json=reset_payload,
                        headers={"Content-Type": "application/json"}
                    )
                    
                    print(f"重置状态码: {reset_response.status_code}")
                    print(f"重置响应: {reset_response.text}")
                    
                    if reset_response.status_code == 200:
                        print("密码重置成功！")
                        return True
                    else:
                        print("密码重置失败")
                        return False
                else:
                    print("验证码验证失败")
                    return False
            else:
                print("验证码格式不正确")
                return False
        else:
            print("发送验证码失败")
            return False
            
    except Exception as e:
        print(f"测试过程中出现错误: {e}")
        return False

if __name__ == "__main__":
    success = test_forgot_password_flow()
    if success:
        print("\n忘记密码功能测试通过！")
    else:
        print("\n忘记密码功能测试失败！")