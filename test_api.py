#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试Chat8 API端点和数据库连接
"""

import requests
import json
from datetime import datetime

# API基础URL
API_BASE_URL = "http://localhost:8000/api"

def test_api_endpoints():
    """测试API端点"""
    print("=== Chat8 API 端点测试 ===")
    
    # 测试基础连接
    try:
        response = requests.get(f"{API_BASE_URL}/auth/me", timeout=5)
        print(f"✅ 服务器连接正常 - 状态码: {response.status_code}")
        if response.status_code == 401:
            print("⚠️  需要认证 - 用户未登录")
        elif response.status_code == 200:
            print(f"✅ 用户已登录: {response.json()}")
    except requests.exceptions.ConnectionError:
        print("❌ 无法连接到服务器 - 请确保后端服务正在运行")
        return False
    except Exception as e:
        print(f"❌ 连接测试失败: {e}")
        return False
    
    # 测试local-storage状态端点（不需要认证）
    try:
        response = requests.get(f"{API_BASE_URL}/local-storage/status?user_id=18", timeout=5)
        print(f"\n📊 Local Storage 状态测试:")
        print(f"状态码: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ 响应数据: {json.dumps(data, indent=2, ensure_ascii=False)}")
        else:
            print(f"❌ 错误响应: {response.text}")
    except Exception as e:
        print(f"❌ Local Storage 状态测试失败: {e}")
    
    # 测试需要认证的端点
    try:
        response = requests.get(f"{API_BASE_URL}/local-storage/messages/19?limit=5&offset=0", timeout=5)
        print(f"\n🔐 认证端点测试:")
        print(f"状态码: {response.status_code}")
        if response.status_code == 401:
            print("⚠️  需要认证 - 这是正常的，因为没有提供token")
        elif response.status_code == 200:
            print(f"✅ 意外成功 - 可能认证被绕过")
        else:
            print(f"❌ 其他错误: {response.text}")
    except Exception as e:
        print(f"❌ 认证端点测试失败: {e}")
    
    return True

def test_database_files():
    """测试数据库文件"""
    print("\n=== 数据库文件测试 ===")
    
    import os
    import sqlite3
    
    db_dir = "backend/app/local_storage/messages"
    if not os.path.exists(db_dir):
        print(f"❌ 数据库目录不存在: {db_dir}")
        return False
    
    db_files = [f for f in os.listdir(db_dir) if f.endswith('.db')]
    print(f"📁 找到 {len(db_files)} 个数据库文件: {db_files}")
    
    for db_file in db_files:
        db_path = os.path.join(db_dir, db_file)
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # 检查表结构
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = cursor.fetchall()
            print(f"\n📋 {db_file} 表结构: {[t[0] for t in tables]}")
            
            # 检查消息数量
            if ('messages',) in tables:
                cursor.execute("SELECT COUNT(*) FROM messages WHERE is_deleted = FALSE")
                count = cursor.fetchone()[0]
                print(f"📊 {db_file} 消息数量: {count}")
                
                # 显示最近几条消息
                cursor.execute("SELECT from_user, to_user, content, timestamp FROM messages WHERE is_deleted = FALSE ORDER BY timestamp DESC LIMIT 3")
                recent = cursor.fetchall()
                print(f"📝 最近消息:")
                for msg in recent:
                    print(f"  {msg[0]} -> {msg[1]}: {msg[2][:30]}... ({msg[3]})")
            
            conn.close()
            
        except Exception as e:
            print(f"❌ 检查 {db_file} 失败: {e}")
    
    return True

if __name__ == "__main__":
    print(f"🚀 开始测试 Chat8 系统 - {datetime.now()}")
    
    # 测试API端点
    api_ok = test_api_endpoints()
    
    # 测试数据库文件
    db_ok = test_database_files()
    
    print(f"\n=== 测试总结 ===")
    print(f"API端点: {'✅ 正常' if api_ok else '❌ 异常'}")
    print(f"数据库文件: {'✅ 正常' if db_ok else '❌ 异常'}")
    
    if not api_ok or not db_ok:
        print("\n💡 建议检查:")
        print("1. 后端服务是否正在运行 (python backend/app/main.py)")
        print("2. 用户是否已登录")
        print("3. 数据库文件权限是否正确")
        print("4. API路由配置是否正确")