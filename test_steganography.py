#!/usr/bin/env python3
"""
隐写术功能测试脚本

这个脚本用于测试图像隐写术功能的嵌入和提取操作。
"""

import os
import sys
import tempfile
from PIL import Image
import numpy as np

# 添加backend路径到sys.path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend', 'app'))

from services.steganography import embed, extract

def create_test_image(width=800, height=600, filename="test_image.png"):
    """
    创建一个测试用的彩色图像
    """
    # 创建一个渐变彩色图像
    image_array = np.zeros((height, width, 3), dtype=np.uint8)
    
    for y in range(height):
        for x in range(width):
            # 创建彩色渐变效果
            r = int(255 * x / width)
            g = int(255 * y / height)
            b = int(255 * (x + y) / (width + height))
            image_array[y, x] = [r, g, b]
    
    # 转换为PIL图像并保存
    image = Image.fromarray(image_array, 'RGB')
    image.save(filename)
    print(f"✅ 测试图像已创建: {filename} (尺寸: {width}x{height})")
    return filename

def test_steganography():
    """
    测试隐写术的完整流程
    """
    print("🔍 开始隐写术功能测试...\n")
    
    # 测试参数
    secret_message = "这是一条秘密信息！Hello, this is a secret message! 🔒"
    password = "test_password_123"
    
    # 创建临时目录
    with tempfile.TemporaryDirectory() as temp_dir:
        # 1. 创建测试图像
        original_image = os.path.join(temp_dir, "original.png")
        create_test_image(800, 600, original_image)
        
        # 2. 嵌入测试
        print("\n📝 开始嵌入测试...")
        embedded_image = os.path.join(temp_dir, "embedded.png")
        
        try:
            embed(original_image, secret_message, password, embedded_image)
            print("✅ 信息嵌入成功！")
        except Exception as e:
            print(f"❌ 嵌入失败: {e}")
            return False
        
        # 3. 提取测试
        print("\n🔍 开始提取测试...")
        
        try:
            extracted_message = extract(embedded_image, password)
            
            if extracted_message == secret_message:
                print("✅ 信息提取成功！")
                print(f"原始信息: {secret_message}")
                print(f"提取信息: {extracted_message}")
                print("✅ 信息完全匹配！")
            else:
                print("❌ 提取的信息与原始信息不匹配")
                print(f"原始信息: {repr(secret_message)}")
                print(f"提取信息: {repr(extracted_message)}")
                print(f"原始信息长度: {len(secret_message)}")
                print(f"提取信息长度: {len(extracted_message) if extracted_message else 0}")
                # 显示字符级别的差异
                if extracted_message:
                    for i, (orig, extr) in enumerate(zip(secret_message, extracted_message)):
                        if orig != extr:
                            print(f"第{i}个字符不同: 原始='{orig}' (ord={ord(orig)}), 提取='{extr}' (ord={ord(extr)})")
                            break
                return False
                
        except Exception as e:
            print(f"❌ 提取失败: {e}")
            return False
        
        # 4. 错误密码测试
        print("\n🔐 测试错误密码...")
        
        try:
            wrong_extracted = extract(embedded_image, "wrong_password")
            if wrong_extracted is None:
                print("✅ 错误密码正确地返回了None")
            else:
                print(f"⚠️  错误密码意外地提取到了信息: {wrong_extracted}")
        except Exception as e:
            print(f"✅ 错误密码正确地抛出了异常: {e}")
        
        # 5. 图像质量对比
        print("\n🖼️  检查图像质量...")
        
        original_img = Image.open(original_image)
        embedded_img = Image.open(embedded_image)
        
        # 计算像素差异
        orig_array = np.array(original_img)
        emb_array = np.array(embedded_img)
        
        diff = np.abs(orig_array.astype(int) - emb_array.astype(int))
        max_diff = np.max(diff)
        avg_diff = np.mean(diff)
        
        print(f"最大像素差异: {max_diff}")
        print(f"平均像素差异: {avg_diff:.2f}")
        
        if max_diff <= 1:  # LSB修改最大差异应该是1
            print("✅ 图像质量保持良好（最大差异 ≤ 1）")
        else:
            print(f"⚠️  图像差异较大: {max_diff}")
    
    print("\n🎉 所有测试完成！")
    return True

def test_capacity():
    """
    测试图像容量限制
    """
    print("\n📊 测试图像容量...")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        # 创建小图像
        small_image = os.path.join(temp_dir, "small.png")
        create_test_image(100, 100, small_image)  # 10,000像素
        
        # 尝试嵌入过长的信息
        long_message = "A" * 2000  # 2000字符 = 16,000位 > 10,000像素
        password = "test"
        output_image = os.path.join(temp_dir, "output.png")
        
        try:
            embed(small_image, long_message, password, output_image)
            # 如果没有抛出异常，检查输出文件是否存在
            if os.path.exists(output_image):
                print("❌ 应该因为容量不足而失败，但却成功了")
                return False
            else:
                print("✅ 正确地检测到容量不足（函数返回但未创建文件）")
                return True
        except Exception as e:
            print(f"✅ 正确地检测到容量不足: {e}")
            return True

def main():
    """
    主测试函数
    """
    print("🚀 隐写术功能完整测试")
    print("=" * 50)
    
    # 基本功能测试
    success1 = test_steganography()
    
    # 容量测试
    success2 = test_capacity()
    
    print("\n" + "=" * 50)
    if success1 and success2:
        print("🎉 所有测试通过！隐写术功能正常工作。")
        return 0
    else:
        print("❌ 部分测试失败，请检查代码。")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)