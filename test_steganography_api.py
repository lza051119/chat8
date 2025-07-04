#!/usr/bin/env python3

import requests
import os
from PIL import Image
import tempfile

def test_steganography_api():
    """测试隐写术API功能"""
    
    # API基础URL
    base_url = "http://localhost:8000/api/steganography"
    
    # 创建一个简单的测试图片
    with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as temp_file:
        # 创建一个100x100的红色图片
        img = Image.new('RGB', (100, 100), color='red')
        img.save(temp_file.name, 'PNG')
        test_image_path = temp_file.name
    
    try:
        print("=== 隐写术API测试 ===")
        
        # 1. 测试API连通性
        print("\n1. 测试API连通性...")
        response = requests.get(f"{base_url}/test")
        print(f"测试端点状态: {response.status_code}")
        if response.status_code == 200:
            print(f"响应: {response.json()}")
        else:
            print(f"错误: {response.text}")
            return
        
        # 2. 测试嵌入功能
        print("\n2. 测试信息嵌入...")
        secret_message = "这是一个测试的秘密信息！🔒"
        password = "test_password_123"
        
        with open(test_image_path, 'rb') as f:
            files = {'image': ('test.png', f, 'image/png')}
            data = {
                'secret_message': secret_message,
                'password': password
            }
            
            response = requests.post(f"{base_url}/embed", files=files, data=data)
            print(f"嵌入请求状态: {response.status_code}")
            
            if response.status_code == 200:
                # 保存嵌入后的图片
                with tempfile.NamedTemporaryFile(suffix='_stego.png', delete=False) as stego_file:
                    stego_file.write(response.content)
                    stego_image_path = stego_file.name
                    print(f"隐写术图片已保存: {stego_image_path}")
                    print(f"文件大小: {len(response.content)} 字节")
                
                # 3. 测试提取功能
                print("\n3. 测试信息提取...")
                with open(stego_image_path, 'rb') as f:
                    files = {'image': ('stego.png', f, 'image/png')}
                    data = {'password': password}
                    
                    response = requests.post(f"{base_url}/extract", files=files, data=data)
                    print(f"提取请求状态: {response.status_code}")
                    
                    if response.status_code == 200:
                        result = response.json()
                        extracted_message = result.get('secret_message', '')
                        print(f"提取的信息: {extracted_message}")
                        
                        # 验证提取的信息是否正确
                        if extracted_message == secret_message:
                            print("✅ 隐写术功能测试成功！信息嵌入和提取都正常工作。")
                        else:
                            print(f"❌ 提取的信息不匹配！")
                            print(f"原始: {secret_message}")
                            print(f"提取: {extracted_message}")
                    else:
                        print(f"❌ 提取失败: {response.status_code}")
                        print(f"错误信息: {response.text}")
                
                # 清理临时文件
                try:
                    os.unlink(stego_image_path)
                except:
                    pass
                    
            else:
                print(f"❌ 嵌入失败: {response.status_code}")
                print(f"错误信息: {response.text}")
        
    except Exception as e:
        print(f"❌ 测试过程中发生错误: {str(e)}")
        import traceback
        traceback.print_exc()
    
    finally:
        # 清理临时文件
        try:
            os.unlink(test_image_path)
        except:
            pass

if __name__ == "__main__":
    test_steganography_api()