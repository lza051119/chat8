#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import requests
import os
from io import BytesIO
from PIL import Image

# 配置
BASE_URL = "http://localhost:8000/api"
TEST_USERNAME = "test2"
TEST_PASSWORD = "A1841770898"
TEST_TO_ID = 19  # 测试接收者ID

def login_and_get_token():
    """登录并获取访问令牌"""
    login_data = {
        "username": TEST_USERNAME,
        "password": TEST_PASSWORD
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/auth/login",
            json=login_data
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"登录响应: {result}")
            token = result.get('data', {}).get('token')
            if token:
                print(f"✅ 登录成功，获取到token")
                return token
            else:
                print(f"❌ 登录成功但未获取到token")
                return None
        else:
            print(f"❌ 登录失败: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        print(f"❌ 登录异常: {e}")
        return None

def create_test_image():
    """创建一个简单的测试图片"""
    img = Image.new('RGB', (100, 100), color='red')
    img_bytes = BytesIO()
    img.save(img_bytes, format='PNG')
    img_bytes.seek(0)
    return img_bytes

def test_upload_with_auth():
    """测试图片上传API（需要认证）"""
    print("测试图片上传API...")
    
    # 先登录获取token
    token = login_and_get_token()
    if not token:
        print("无法获取访问令牌，测试终止")
        return False
    
    # 创建测试图片
    test_img = create_test_image()
    
    # 准备上传数据
    files = {
        'file': ('test.png', test_img, 'image/png')
    }
    
    data = {
        'to_id': TEST_TO_ID,
        'content': '测试图片上传'
    }
    
    try:
        # 带认证调用上传API
        response = requests.post(
            f"{BASE_URL}/upload/image",
            headers={
                'Authorization': f'Bearer {token}'
            },
            files=files,
            data=data,
            timeout=30
        )
        
        print(f"响应状态码: {response.status_code}")
        print(f"响应内容: {response.text}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"上传成功! 消息ID: {result.get('id')}")
            print(f"文件路径: {result.get('filePath')}")
            return True
        else:
            print(f"上传失败: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"上传异常: {e}")
        return False

if __name__ == "__main__":
    test_upload_with_auth()