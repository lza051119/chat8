#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试修改后的隐写术算法（使用RGB三通道）
"""

import os
import sys
from PIL import Image

# 添加backend路径到sys.path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend', 'app'))

from services.steganography import embed, extract

def create_test_image(width=100, height=100, filename="test_image.png"):
    """创建一个测试用的图像"""
    # 创建一个简单的彩色图像
    image = Image.new('RGB', (width, height), color=(128, 128, 128))
    
    # 添加一些图案使图像更有趣
    pixels = image.load()
    for x in range(width):
        for y in range(height):
            r = (x * 255) // width
            g = (y * 255) // height
            b = ((x + y) * 255) // (width + height)
            pixels[x, y] = (r, g, b)
    
    image.save(filename)
    print(f"创建测试图像: {filename} ({width}x{height})")
    return filename

def test_steganography():
    """测试隐写术的嵌入和提取功能"""
    print("=== 隐写术RGB三通道测试 ===")
    
    # 1. 创建测试图像
    test_image = create_test_image(100, 100, "test_rgb.png")
    
    # 2. 准备测试消息
    test_messages = [
        "Hello World!",
        "这是一个中文测试消息",
        "A" * 50,  # 较长的消息
        "🎉 Unicode test with emoji! 🚀",
        "Short"
    ]
    
    password = "test_password_123"
    
    for i, message in enumerate(test_messages):
        print(f"\n--- 测试消息 {i+1}: '{message}' ---")
        
        # 计算消息的bit数
        message_bits = len(message.encode('utf-8')) * 8
        total_bits = 32 + message_bits  # 32bit长度头 + 消息内容
        
        # 计算图像容量
        image_capacity = 100 * 100 * 3  # 100x100像素，每像素3bit
        
        print(f"消息长度: {len(message)} 字符")
        print(f"消息bit数: {message_bits} bits")
        print(f"总bit数(含长度头): {total_bits} bits")
        print(f"图像容量: {image_capacity} bits")
        print(f"容量利用率: {(total_bits/image_capacity)*100:.2f}%")
        
        if total_bits > image_capacity:
            print("❌ 消息太长，跳过此测试")
            continue
        
        # 3. 嵌入消息
        output_image = f"test_output_{i+1}.png"
        try:
            embed(test_image, message, password, output_image)
            print("✅ 嵌入成功")
        except Exception as e:
            print(f"❌ 嵌入失败: {e}")
            continue
        
        # 4. 提取消息
        try:
            extracted_message = extract(output_image, password)
            if extracted_message == message:
                print("✅ 提取成功，消息完全匹配")
            else:
                print(f"❌ 提取失败，消息不匹配")
                print(f"原始: {repr(message)}")
                print(f"提取: {repr(extracted_message)}")
        except Exception as e:
            print(f"❌ 提取失败: {e}")
        
        # 5. 测试错误密码
        try:
            wrong_extracted = extract(output_image, "wrong_password")
            if wrong_extracted != message:
                print("✅ 错误密码测试通过（无法提取正确消息）")
            else:
                print("⚠️ 错误密码测试异常（竟然提取出了正确消息）")
        except Exception as e:
            print(f"✅ 错误密码测试通过（提取失败）: {e}")
        
        # 清理输出文件
        if os.path.exists(output_image):
            os.remove(output_image)
    
    # 清理测试图像
    if os.path.exists(test_image):
        os.remove(test_image)
    
    print("\n=== 测试完成 ===")

def test_capacity_improvement():
    """测试容量改进效果"""
    print("\n=== 容量改进测试 ===")
    
    # 创建不同尺寸的图像进行容量测试
    test_sizes = [(50, 50), (100, 100), (200, 200)]
    
    for width, height in test_sizes:
        pixels = width * height
        old_capacity_bits = pixels  # 旧算法：每像素1bit
        new_capacity_bits = pixels * 3  # 新算法：每像素3bit
        
        # 计算可以存储的字符数（假设平均每字符8bit）
        old_chars = (old_capacity_bits - 32) // 8  # 减去32bit长度头
        new_chars = (new_capacity_bits - 32) // 8
        
        improvement = new_capacity_bits / old_capacity_bits
        
        print(f"图像尺寸: {width}x{height} ({pixels} 像素)")
        print(f"  旧算法容量: {old_capacity_bits} bits (~{old_chars} 字符)")
        print(f"  新算法容量: {new_capacity_bits} bits (~{new_chars} 字符)")
        print(f"  容量提升: {improvement:.1f}倍")
        print()

if __name__ == "__main__":
    test_steganography()
    test_capacity_improvement()