#!/usr/bin/env python3
"""
测试隐写术解密功能的API调用
验证修复后的前端是否能正确调用后端API
"""

import requests
import json
from PIL import Image
import io
import tempfile
import os

def test_local_storage_api():
    """测试本地存储API是否可访问"""
    print("=== 测试本地存储API连接 ===")
    
    # 测试API连通性
    base_url = "http://localhost:8000/api/v1"
    
    try:
        # 测试健康检查端点（如果存在）
        response = requests.get(f"{base_url}/health", timeout=5)
        print(f"健康检查状态: {response.status_code}")
    except requests.exceptions.RequestException as e:
        print(f"健康检查失败: {e}")
    
    # 测试本地存储端点的基本连接
    try:
        # 尝试访问一个不存在的消息ID，应该返回404而不是500
        response = requests.put(
            f"{base_url}/local-storage/messages/test_id/field",
            headers={
                'Content-Type': 'application/json',
                'Authorization': 'Bearer test_token'
            },
            json={
                'field_name': 'test_field',
                'field_value': 'test_value'
            },
            timeout=5
        )
        print(f"本地存储API响应状态: {response.status_code}")
        if response.status_code != 500:
            print("✓ API端点可访问（非500错误）")
        else:
            print("✗ API返回500错误")
            print(f"错误详情: {response.text}")
    except requests.exceptions.RequestException as e:
        print(f"本地存储API连接失败: {e}")

def test_steganography_with_local_storage():
    """测试完整的隐写术流程，包括本地存储更新"""
    print("\n=== 测试隐写术完整流程 ===")
    
    # 创建测试图片
    img = Image.new('RGB', (100, 100), color='red')
    img_buffer = io.BytesIO()
    img.save(img_buffer, format='PNG')
    img_buffer.seek(0)
    
    # 测试嵌入
    embed_url = "http://localhost:8000/api/steganography/embed"
    files = {'image': ('test.png', img_buffer, 'image/png')}
    data = {
        'secret_message': '测试隐藏消息 🔐',
        'password': 'test_password'
    }
    
    try:
        print("正在测试隐写术嵌入...")
        embed_response = requests.post(embed_url, files=files, data=data, timeout=10)
        print(f"嵌入响应状态: {embed_response.status_code}")
        
        if embed_response.status_code == 200:
            print("✓ 隐写术嵌入成功")
            
            # 保存嵌入后的图片到临时文件
            with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as temp_file:
                temp_file.write(embed_response.content)
                temp_image_path = temp_file.name
            
            # 测试提取
            extract_url = "http://localhost:8000/api/steganography/extract"
            with open(temp_image_path, 'rb') as f:
                files = {'image': ('test.png', f, 'image/png')}
                data = {'password': 'test_password'}
                
                print("正在测试隐写术提取...")
                extract_response = requests.post(extract_url, files=files, data=data, timeout=10)
                print(f"提取响应状态: {extract_response.status_code}")
                
                if extract_response.status_code == 200:
                    result = extract_response.json()
                    extracted_message = result.get('secret_message', '')
                    print(f"提取的消息: {extracted_message}")
                    
                    if extracted_message == '测试隐藏消息 🔐':
                        print("✓ 隐写术提取成功，消息匹配")
                    else:
                        print("✗ 提取的消息不匹配")
                else:
                    print(f"✗ 隐写术提取失败: {extract_response.text}")
            
            # 清理临时文件
            os.unlink(temp_image_path)
            
        else:
            print(f"✗ 隐写术嵌入失败: {embed_response.text}")
            
    except requests.exceptions.RequestException as e:
        print(f"隐写术API测试失败: {e}")

def main():
    print("隐写术解密功能测试")
    print("=" * 50)
    
    test_local_storage_api()
    test_steganography_with_local_storage()
    
    print("\n=== 测试总结 ===")
    print("如果所有测试都通过，说明修复成功")
    print("前端现在应该能够正确调用后端API而不会出现500错误")

if __name__ == "__main__":
    main()