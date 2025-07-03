#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
真实邮件发送功能演示
展示如何配置和使用QQ邮箱发送验证码
"""

import asyncio
import sys
import os
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.append(str(Path(__file__).parent))

from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

def show_email_configuration_guide():
    """
    显示邮件配置指南
    """
    print("=== QQ邮箱配置指南 ===")
    print()
    print("1. 获取QQ邮箱授权码:")
    print("   • 登录 https://mail.qq.com")
    print("   • 点击左上角'设置' -> '账户'")
    print("   • 找到'POP3/IMAP/SMTP/Exchange/CardDAV/CalDAV服务'")
    print("   • 开启'SMTP服务'")
    print("   • 点击'生成授权码'")
    print("   • 按提示发送短信获取授权码")
    print()
    print("2. 配置环境变量 (.env文件):")
    print("   MAIL_USERNAME=your_qq_email@qq.com")
    print("   MAIL_PASSWORD=your_authorization_code")
    print("   MAIL_FROM=your_qq_email@qq.com")
    print("   MAIL_SERVER=smtp.qq.com")
    print("   DEVELOPMENT_MODE=false")
    print()
    print("3. 当前配置状态:")
    
    mail_username = os.getenv("MAIL_USERNAME")
    mail_password = os.getenv("MAIL_PASSWORD")
    development_mode = os.getenv("DEVELOPMENT_MODE", "false").lower() == "true"
    
    print(f"   邮箱用户名: {mail_username}")
    print(f"   邮箱密码: {'✅ 已配置' if mail_password and mail_password != 'your_qq_auth_code_here' else '❌ 未配置'}")
    print(f"   开发模式: {'✅ 开启 (模拟发送)' if development_mode else '❌ 关闭 (真实发送)'}")
    
    return mail_password and mail_password != 'your_qq_auth_code_here'

async def demo_email_sending():
    """
    演示邮件发送功能
    """
    try:
        from app.core.email_config import send_verification_email
        from app.services.verification_service import VerificationCodeService
        
        print("\n=== 邮件发送演示 ===")
        
        # 生成验证码
        verification_service = VerificationCodeService()
        test_email = "future_234@qq.com"
        verification_code = verification_service.generate_code(test_email)
        
        print(f"目标邮箱: {test_email}")
        print(f"验证码: {verification_code}")
        print("正在发送邮件...")
        
        # 发送邮件
        await send_verification_email(test_email, verification_code, "测试用户")
        
        print("✅ 邮件发送成功!")
        
        # 如果是开发模式，显示验证码
        development_mode = os.getenv("DEVELOPMENT_MODE", "false").lower() == "true"
        if development_mode:
            print(f"[开发模式] 验证码: {verification_code}")
        else:
            print("请检查邮箱收件箱")
            
        # 验证码验证演示
        print("\n=== 验证码验证演示 ===")
        user_input = input("请输入验证码进行验证 (或按回车跳过): ").strip()
        
        if user_input:
            is_valid = verification_service.verify_code(test_email, user_input)
            if is_valid:
                print("✅ 验证码验证成功!")
            else:
                print("❌ 验证码验证失败!")
                
    except Exception as e:
        print(f"❌ 邮件发送失败: {str(e)}")
        print("\n可能的原因:")
        print("• QQ邮箱授权码不正确")
        print("• 网络连接问题")
        print("• QQ邮箱SMTP服务未开启")
        print("• 邮箱配置错误")

def show_api_usage_example():
    """
    显示API使用示例
    """
    print("\n=== API使用示例 ===")
    print()
    print("1. 发送忘记密码请求:")
    print("   POST /api/v1/auth/forgot-password")
    print("   Content-Type: application/json")
    print("   Body: {\"email\": \"future_234@qq.com\"}")
    print()
    print("   curl示例:")
    print("   curl -X POST http://localhost:8000/api/v1/auth/forgot-password \\")
    print("        -H 'Content-Type: application/json' \\")
    print("        -d '{\"email\": \"future_234@qq.com\"}'")
    print()
    print("2. 重置密码:")
    print("   POST /api/v1/auth/reset-password")
    print("   Content-Type: application/json")
    print("   Body: {")
    print("     \"email\": \"future_234@qq.com\",")
    print("     \"verification_code\": \"123456\",")
    print("     \"new_password\": \"newpassword123\"")
    print("   }")
    print()
    print("   curl示例:")
    print("   curl -X POST http://localhost:8000/api/v1/auth/reset-password \\")
    print("        -H 'Content-Type: application/json' \\")
    print("        -d '{")
    print("          \"email\": \"future_234@qq.com\",")
    print("          \"verification_code\": \"123456\",")
    print("          \"new_password\": \"newpassword123\"")
    print("        }'")

def show_frontend_integration():
    """
    显示前端集成示例
    """
    print("\n=== 前端集成示例 ===")
    print()
    print("JavaScript代码示例:")
    print()
    print("```javascript")
    print("// 发送忘记密码请求")
    print("async function sendForgotPasswordRequest(email) {")
    print("  try {")
    print("    const response = await fetch('/api/v1/auth/forgot-password', {")
    print("      method: 'POST',")
    print("      headers: {")
    print("        'Content-Type': 'application/json'")
    print("      },")
    print("      body: JSON.stringify({ email })")
    print("    });")
    print("    ")
    print("    if (response.ok) {")
    print("      const data = await response.json();")
    print("      alert('验证码已发送到您的邮箱');")
    print("      return true;")
    print("    } else {")
    print("      const error = await response.json();")
    print("      alert('发送失败: ' + error.message);")
    print("      return false;")
    print("    }")
    print("  } catch (error) {")
    print("    alert('网络错误: ' + error.message);")
    print("    return false;")
    print("  }")
    print("}")
    print("")
    print("// 重置密码")
    print("async function resetPassword(email, verificationCode, newPassword) {")
    print("  try {")
    print("    const response = await fetch('/api/v1/auth/reset-password', {")
    print("      method: 'POST',")
    print("      headers: {")
    print("        'Content-Type': 'application/json'")
    print("      },")
    print("      body: JSON.stringify({")
    print("        email,")
    print("        verification_code: verificationCode,")
    print("        new_password: newPassword")
    print("      })")
    print("    });")
    print("    ")
    print("    if (response.ok) {")
    print("      const data = await response.json();")
    print("      alert('密码重置成功');")
    print("      return true;")
    print("    } else {")
    print("      const error = await response.json();")
    print("      alert('重置失败: ' + error.message);")
    print("      return false;")
    print("    }")
    print("  } catch (error) {")
    print("    alert('网络错误: ' + error.message);")
    print("    return false;")
    print("  }")
    print("}")
    print("```")

async def main():
    """
    主函数
    """
    print("🔐 Chat8 真实邮件发送功能演示")
    print("=" * 50)
    
    # 显示配置指南
    is_configured = show_email_configuration_guide()
    
    if is_configured:
        print("\n✅ 邮件配置完成，可以进行真实邮件发送测试")
        
        # 询问是否进行邮件发送测试
        test_email = input("\n是否进行邮件发送测试? (y/n): ").strip().lower()
        if test_email == 'y':
            await demo_email_sending()
    else:
        print("\n⚠️  请先完成邮件配置")
    
    # 显示API使用示例
    show_api_usage_example()
    
    # 显示前端集成示例
    show_frontend_integration()
    
    print("\n=== 总结 ===")
    print("1. 配置QQ邮箱授权码到 .env 文件")
    print("2. 设置 DEVELOPMENT_MODE=false 启用真实邮件发送")
    print("3. 使用API端点发送验证码和重置密码")
    print("4. 在前端集成相应的JavaScript代码")
    print("\n🎉 真实邮件发送功能已准备就绪!")

if __name__ == "__main__":
    asyncio.run(main())