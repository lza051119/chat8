#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
调试重置密码API的详细测试脚本
"""

import requests
import json

def test_reset_password_debug():
    """
    测试重置密码API并获取详细错误信息
    """
    base_url = "http://localhost:8000/api/v1"
    
    print("=== 重置密码API调试测试 ===")
    
    # 测试不同的请求格式
    test_cases = [
        {
            "name": "正确格式测试",
            "payload": {
                "email": "future_234@qq.com",
                "code": "123456",
                "new_password": "newpassword123"
            }
        },
        {
            "name": "缺少email字段",
            "payload": {
                "code": "123456",
                "new_password": "newpassword123"
            }
        },
        {
            "name": "缺少code字段",
            "payload": {
                "email": "future_234@qq.com",
                "new_password": "newpassword123"
            }
        },
        {
            "name": "缺少new_password字段",
            "payload": {
                "email": "future_234@qq.com",
                "code": "123456"
            }
        },
        {
            "name": "空字符串测试",
            "payload": {
                "email": "",
                "code": "",
                "new_password": ""
            }
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n{i}. {test_case['name']}")
        print(f"   请求数据: {json.dumps(test_case['payload'], ensure_ascii=False)}")
        
        try:
            response = requests.post(
                f"{base_url}/auth/reset-password",
                json=test_case['payload'],
                headers={"Content-Type": "application/json"},
                timeout=10
            )
            
            print(f"   状态码: {response.status_code}")
            print(f"   响应头: {dict(response.headers)}")
            
            try:
                response_data = response.json()
                print(f"   响应内容: {json.dumps(response_data, ensure_ascii=False, indent=2)}")
            except json.JSONDecodeError:
                print(f"   响应内容(原始): {response.text}")
                
        except requests.exceptions.RequestException as e:
            print(f"   请求异常: {str(e)}")
        except Exception as e:
            print(f"   其他异常: {str(e)}")
            
        print("-" * 50)

if __name__ == "__main__":
    test_reset_password_debug()