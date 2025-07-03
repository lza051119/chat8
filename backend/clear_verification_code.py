#!/usr/bin/env python3
"""
清除验证码缓存的临时脚本
"""

import sys
import os

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.services.verification_service import VerificationCodeService

def main():
    email = "future_234@qq.com"
    
    print(f"清除邮箱 {email} 的验证码缓存...")
    
    # 检查是否有验证码
    if VerificationCodeService.has_valid_code(email):
        remaining = VerificationCodeService.get_remaining_time(email)
        print(f"发现有效验证码，剩余时间: {remaining} 秒")
        
        # 清除验证码
        if VerificationCodeService.clear_code(email):
            print("验证码已成功清除")
        else:
            print("清除验证码失败")
    else:
        print("没有找到有效的验证码")
    
    # 再次检查
    if not VerificationCodeService.has_valid_code(email):
        print("确认：验证码缓存已清空，可以重新发送验证码")
    else:
        print("警告：验证码仍然存在")

if __name__ == "__main__":
    main()