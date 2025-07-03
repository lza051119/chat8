#!/usr/bin/env python3

import requests
import json

# 配置
BASE_URL = "http://localhost:8000/api"
TEST_EMAIL = "future_234@qq.com"

def test_reset_password_error_handling():
    print("=== 测试重置密码错误处理 ===")
    
    test_cases = [
        {
            "name": "无效验证码",
            "payload": {
                "email": TEST_EMAIL,
                "code": "123456",  # 无效验证码
                "new_password": "newpassword123"
            }
        },
        {
            "name": "未注册邮箱",
            "payload": {
                "email": "nonexistent@example.com",
                "code": "123456",
                "new_password": "newpassword123"
            }
        },
        {
            "name": "缺少验证码字段",
            "payload": {
                "email": TEST_EMAIL,
                "new_password": "newpassword123"
            }
        },
        {
            "name": "空验证码",
            "payload": {
                "email": TEST_EMAIL,
                "code": "",
                "new_password": "newpassword123"
            }
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n{i}. 测试: {test_case['name']}")
        
        response = requests.post(
            f"{BASE_URL}/v1/auth/reset-password",
            json=test_case['payload'],
            headers={"Content-Type": "application/json"}
        )
        
        print(f"状态码: {response.status_code}")
        print(f"响应: {response.text}")
        
        try:
            response_data = response.json()
            if 'message' in response_data:
                print(f"错误信息 (message): {response_data['message']}")
            if 'detail' in response_data:
                print(f"错误信息 (detail): {response_data['detail']}")
        except json.JSONDecodeError:
            print("响应不是有效的JSON格式")
        
        print("-" * 50)

if __name__ == "__main__":
    test_reset_password_error_handling()
    print("\n=== 测试完成 ===")
    print("\n现在前端应该能够正确显示这些错误信息了！")