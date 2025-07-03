#!/usr/bin/env python3
"""
测试邮件发送功能
"""

import asyncio
import sys
import os

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.services.password_reset_service import PasswordResetService
from app.services.verification_service import VerificationCodeService

async def test_email_send():
    email = "petrichor_umut@163.com"
    
    print(f"测试向 {email} 发送验证码...")
    
    # 清除可能存在的验证码缓存
    VerificationCodeService.clear_code(email)
    print("已清除验证码缓存")
    
    try:
        # 发送验证码
        result = await PasswordResetService.send_reset_code(email)
        print("发送成功!")
        print(f"结果: {result}")
    except Exception as e:
        print(f"发送失败: {str(e)}")
        print(f"错误类型: {type(e).__name__}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_email_send())