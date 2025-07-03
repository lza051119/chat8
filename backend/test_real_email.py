#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试真实邮件发送功能
使用 future_234@qq.com 作为测试邮箱
"""

import asyncio
import sys
import os
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.append(str(Path(__file__).parent))

from dotenv import load_dotenv
from app.core.email_config import send_verification_email
from app.services.verification_service import VerificationCodeService

# 加载环境变量
load_dotenv()

async def test_real_email_sending():
    """
    测试真实邮件发送功能
    """
    print("=== 真实邮件发送测试 ===")
    
    # 检查环境变量配置
    print("\n1. 检查环境变量配置:")
    mail_username = os.getenv("MAIL_USERNAME")
    mail_password = os.getenv("MAIL_PASSWORD")
    development_mode = os.getenv("DEVELOPMENT_MODE", "false").lower() == "true"
    
    print(f"   邮箱用户名: {mail_username}")
    print(f"   邮箱密码: {'已设置' if mail_password and mail_password != 'your_qq_auth_code_here' else '未设置或使用默认值'}")
    print(f"   开发模式: {development_mode}")
    
    if mail_password == "your_qq_auth_code_here":
        print("\n⚠️  警告: 请在 .env 文件中设置真实的QQ邮箱授权码!")
        print("   获取QQ邮箱授权码的步骤:")
        print("   1. 登录QQ邮箱网页版")
        print("   2. 进入设置 -> 账户")
        print("   3. 开启SMTP服务")
        print("   4. 生成授权码")
        print("   5. 将授权码填入 .env 文件的 MAIL_PASSWORD 字段")
        return
    
    # 测试邮箱地址
    test_email = "future_234@qq.com"
    test_username = "测试用户"
    
    # 生成验证码
    verification_service = VerificationCodeService()
    verification_code = verification_service.generate_code(test_email)
    
    print(f"\n2. 生成验证码: {verification_code}")
    print(f"   目标邮箱: {test_email}")
    
    # 发送邮件
    print("\n3. 正在发送邮件...")
    try:
        await send_verification_email(test_email, verification_code, test_username)
        print("✅ 邮件发送成功!")
        print(f"   请检查 {test_email} 的收件箱")
        
        # 验证码验证测试
        print("\n4. 验证码验证测试:")
        user_input = input(f"请输入收到的验证码 (或按回车跳过): ").strip()
        
        if user_input:
            is_valid = verification_service.verify_code(test_email, user_input)
            if is_valid:
                print("✅ 验证码验证成功!")
            else:
                print("❌ 验证码验证失败!")
        else:
            print("跳过验证码验证测试")
            
    except Exception as e:
        print(f"❌ 邮件发送失败: {str(e)}")
        print("\n可能的原因:")
        print("1. QQ邮箱授权码不正确")
        print("2. 网络连接问题")
        print("3. QQ邮箱SMTP服务未开启")
        print("4. 邮箱配置错误")

if __name__ == "__main__":
    asyncio.run(test_real_email_sending())