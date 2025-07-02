#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
图片上传功能测试脚本
测试后端图片上传API的各种场景
"""

import requests
import os
import json
from io import BytesIO
from PIL import Image

# 配置
BASE_URL = "http://localhost:8080/api"
TEST_USERNAME = "testuser"
TEST_PASSWORD = "testpass123"
TEST_TO_ID = 2  # 接收者ID

def create_test_image(width=100, height=100, format='PNG'):
    """创建测试图片"""
    img = Image.new('RGB', (width, height), color='red')
    img_bytes = BytesIO()
    img.save(img_bytes, format=format)
    img_bytes.seek(0)
    return img_bytes

def login_and_get_token():
    """登录并获取访问令牌"""
    login_data = {
        "username": TEST_USERNAME,
        "password": TEST_PASSWORD
    }
    
    response = requests.post(f"{BASE_URL}/auth/login", data=login_data)
    if response.status_code == 200:
        token_data = response.json()
        return token_data.get("access_token")
    else:
        print(f"登录失败: {response.status_code} - {response.text}")
        return None

def test_image_upload(token, test_name, **kwargs):
    """测试图片上传"""
    print(f"\n=== {test_name} ===")
    
    headers = {
        "Authorization": f"Bearer {token}"
    }
    
    # 准备文件和数据
    files = kwargs.get('files', {})
    data = kwargs.get('data', {})
    
    try:
        response = requests.post(
            f"{BASE_URL}/upload/image",
            headers=headers,
            files=files,
            data=data
        )
        
        print(f"状态码: {response.status_code}")
        print(f"响应: {response.text}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ 上传成功: 消息ID={result.get('id')}, 文件路径={result.get('file_path')}")
            return result
        else:
            print(f"❌ 上传失败: {response.status_code}")
            return None
            
    except Exception as e:
        print(f"❌ 请求异常: {str(e)}")
        return None

def test_image_access(filename):
    """测试图片访问"""
    print(f"\n=== 测试图片访问: {filename} ===")
    
    try:
        response = requests.get(f"{BASE_URL}/images/{filename}")
        print(f"状态码: {response.status_code}")
        
        if response.status_code == 200:
            print(f"✅ 图片访问成功, 内容长度: {len(response.content)} 字节")
            print(f"Content-Type: {response.headers.get('content-type')}")
            return True
        else:
            print(f"❌ 图片访问失败: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ 请求异常: {str(e)}")
        return False

def main():
    print("开始测试图片上传功能...")
    
    # 登录获取token
    token = login_and_get_token()
    if not token:
        print("无法获取访问令牌，测试终止")
        return
    
    print(f"✅ 登录成功，获取到token")
    
    # 测试1: 正常PNG图片上传
    test_img = create_test_image(200, 200, 'PNG')
    result1 = test_image_upload(
        token,
        "正常PNG图片上传",
        files={'file': ('test.png', test_img, 'image/png')},
        data={
            'to_id': TEST_TO_ID,
            'content': '这是一张测试图片',
            'encrypted': 'true',
            'method': 'Server'
        }
    )
    
    # 测试图片访问
    if result1 and result1.get('file_path'):
        test_image_access(result1['file_path'])
    
    # 测试2: JPEG图片上传
    test_img2 = create_test_image(150, 150, 'JPEG')
    result2 = test_image_upload(
        token,
        "JPEG图片上传",
        files={'file': ('test.jpg', test_img2, 'image/jpeg')},
        data={
            'to_id': TEST_TO_ID,
            'content': 'JPEG测试图片',
            'encrypted': 'false'
        }
    )
    
    # 测试3: 无效文件类型
    test_image_upload(
        token,
        "无效文件类型测试",
        files={'file': ('test.txt', BytesIO(b'not an image'), 'text/plain')},
        data={'to_id': TEST_TO_ID}
    )
    
    # 测试4: 缺少文件
    test_image_upload(
        token,
        "缺少文件测试",
        files={},
        data={'to_id': TEST_TO_ID, 'content': '没有文件'}
    )
    
    # 测试5: 大文件测试（创建一个较大的图片）
    large_img = create_test_image(2000, 2000, 'PNG')
    test_image_upload(
        token,
        "大文件测试",
        files={'file': ('large.png', large_img, 'image/png')},
        data={'to_id': TEST_TO_ID, 'content': '大图片测试'}
    )
    
    print("\n=== 测试完成 ===")

if __name__ == "__main__":
    main()