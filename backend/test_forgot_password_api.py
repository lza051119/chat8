#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试忘记密码API完整流程
包括发送验证码和重置密码
"""

import requests
import json
import time

def test_forgot_password_flow():
    """
    测试完整的忘记密码流程
    """
    base_url = "http://localhost:8000/api/v1"
    test_email = "future_234@qq.com"
    
    print("=== 忘记密码API测试 ===")
    print(f"测试邮箱: {test_email}")
    print(f"API基础URL: {base_url}")
    
    # 步骤1: 发送忘记密码请求
    print("\n1. 发送忘记密码请求...")
    forgot_password_url = f"{base_url}/auth/forgot-password"
    
    payload = {
        "email": test_email
    }
    
    try:
        response = requests.post(
            forgot_password_url,
            json=payload,
            headers={"Content-Type": "application/json"}
        )
        
        print(f"   状态码: {response.status_code}")
        print(f"   响应内容: {response.text}")
        
        if response.status_code == 200:
            print("✅ 忘记密码请求发送成功!")
            response_data = response.json()
            print(f"   服务器响应: {response_data.get('message', '无消息')}")
            
            # 如果是开发模式，可能会在响应中包含验证码
            if 'verification_code' in response_data:
                verification_code = response_data['verification_code']
                print(f"   [开发模式] 验证码: {verification_code}")
            else:
                print("   请检查邮箱获取验证码")
                verification_code = input("   请输入收到的验证码: ").strip()
            
            # 步骤2: 验证验证码并重置密码
            print("\n2. 重置密码...")
            reset_password_url = f"{base_url}/auth/reset-password"
            
            new_password = "newpassword123"
            reset_payload = {
                "email": test_email,
                "code": verification_code,
                "new_password": new_password
            }
            
            reset_response = requests.post(
                reset_password_url,
                json=reset_payload,
                headers={"Content-Type": "application/json"}
            )
            
            print(f"   状态码: {reset_response.status_code}")
            print(f"   响应内容: {reset_response.text}")
            
            if reset_response.status_code == 200:
                print("✅ 密码重置成功!")
                reset_data = reset_response.json()
                print(f"   服务器响应: {reset_data.get('message', '无消息')}")
                
                # 步骤3: 测试新密码登录
                print("\n3. 测试新密码登录...")
                login_url = f"{base_url}/auth/login"
                
                login_payload = {
                    "username": "future_234",  # 假设用户名
                    "password": new_password
                }
                
                login_response = requests.post(
                    login_url,
                    data=login_payload,  # 使用form data
                    headers={"Content-Type": "application/x-www-form-urlencoded"}
                )
                
                print(f"   状态码: {login_response.status_code}")
                print(f"   响应内容: {login_response.text}")
                
                if login_response.status_code == 200:
                    print("✅ 新密码登录成功!")
                    login_data = login_response.json()
                    if 'access_token' in login_data:
                        print("   获得访问令牌，密码重置流程完全成功!")
                else:
                    print("❌ 新密码登录失败")
                    
            else:
                print("❌ 密码重置失败")
                if reset_response.status_code == 400:
                    print("   可能原因: 验证码错误或已过期")
                elif reset_response.status_code == 404:
                    print("   可能原因: 用户不存在")
                    
        elif response.status_code == 404:
            print("❌ 用户不存在")
            print("   请确保邮箱地址对应的用户已注册")
        elif response.status_code == 429:
            print("❌ 请求过于频繁")
            print("   请稍后再试")
        else:
            print(f"❌ 请求失败: {response.status_code}")
            
    except requests.exceptions.ConnectionError:
        print("❌ 连接失败")
        print("   请确保后端服务正在运行 (http://localhost:8000)")
    except Exception as e:
        print(f"❌ 测试过程中出现错误: {str(e)}")

def test_email_configuration():
    """
    测试邮件配置状态
    """
    print("\n=== 邮件配置检查 ===")
    
    import os
    from dotenv import load_dotenv
    
    # 加载环境变量
    load_dotenv()
    
    mail_username = os.getenv("MAIL_USERNAME")
    mail_password = os.getenv("MAIL_PASSWORD")
    development_mode = os.getenv("DEVELOPMENT_MODE", "false").lower() == "true"
    
    print(f"邮箱用户名: {mail_username}")
    print(f"邮箱密码: {'已设置' if mail_password and mail_password != 'your_qq_auth_code_here' else '未设置'}")
    print(f"开发模式: {development_mode}")
    
    if mail_password == "your_qq_auth_code_here":
        print("\n⚠️  需要配置QQ邮箱授权码:")
        print("1. 登录 https://mail.qq.com")
        print("2. 设置 -> 账户 -> POP3/IMAP/SMTP/Exchange/CardDAV/CalDAV服务")
        print("3. 开启SMTP服务")
        print("4. 生成授权码")
        print("5. 将授权码替换 .env 文件中的 MAIL_PASSWORD")
        return False
    
    return True

if __name__ == "__main__":
    # 首先检查邮件配置
    if test_email_configuration():
        print("\n邮件配置正常，开始API测试...")
        test_forgot_password_flow()
    else:
        print("\n请先配置邮件设置后再进行测试")