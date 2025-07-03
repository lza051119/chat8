#!/usr/bin/env python3
"""
同步测试邮件发送功能
"""

import sys
import os

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.core.email_config import send_verification_email
import asyncio

def test_sync_email():
    email = "petrichor_umut@163.com"
    code = "123456"
    username = "petrichor_umut"
    
    print(f"测试向 {email} 发送验证码...")
    
    try:
        # 在新的事件循环中运行
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(send_verification_email(email, code, username))
        print("发送成功!")
        print(f"结果: {result}")
    except Exception as e:
        print(f"发送失败: {str(e)}")
        print(f"错误类型: {type(e).__name__}")
        import traceback
        traceback.print_exc()
    finally:
        loop.close()

if __name__ == "__main__":
    test_sync_email()