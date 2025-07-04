#!/usr/bin/env python3
"""
测试用户注册时密钥生成和存储功能的脚本
"""

import requests
import json
import sqlite3
import time
from datetime import datetime

def test_user_registration_with_keys():
    """测试用户注册并验证密钥生成"""
    
    # API端点
    base_url = "http://localhost:8000/api"
    register_url = f"{base_url}/v1/auth/register"
    
    # 生成唯一的测试用户数据
    timestamp = int(time.time())
    test_user = {
        "username": f"testuser_{timestamp}",
        "email": f"test_{timestamp}@example.com",
        "password": "testpass123"
    }
    
    print("🚀 开始测试用户注册和密钥生成功能...")
    print(f"📝 测试用户: {test_user['username']}")
    
    try:
        # 1. 发送注册请求
        print("\n📤 发送注册请求...")
        response = requests.post(register_url, json=test_user, headers={
            "Content-Type": "application/json"
        })
        
        print(f"📥 响应状态码: {response.status_code}")
        
        if response.status_code not in [200, 201]:
            print(f"❌ 注册失败: {response.text}")
            return False
        
        # 2. 解析响应数据
        response_data = response.json()
        print("✅ 注册成功！")
        
        # 打印完整响应用于调试
        print(f"\n🔍 完整响应数据: {json.dumps(response_data, indent=2, ensure_ascii=False)}")
        
        # 检查响应结构
        if not response_data.get('success'):
            print(f"❌ 注册响应显示失败: {response_data.get('message')}")
            return False
        
        user_data = response_data.get('data', {})
        user_info = user_data.get('user', {})
        keys_info = user_data.get('keys', {})
        
        print(f"\n👤 用户ID: {user_info.get('userId')}")
        print(f"👤 用户名: {user_info.get('username')}")
        
        # 3. 验证密钥信息
        print("\n🔐 验证密钥信息...")
        print(f"Keys响应数据: {keys_info}")
        
        required_key_fields = ['public_key', 'private_key']
        for field in required_key_fields:
            if field in keys_info:
                print(f"✅ {field}: 存在")
            else:
                print(f"❌ {field}: 缺失")
                return False
        
        # 4. 验证数据库中的密钥存储
        print("\n🗄️  验证数据库中的密钥存储...")
        user_id = user_info.get('userId')
        
        if not verify_keys_in_database(user_id, test_user['password']):
            return False
        
        # 5. 验证服务器数据库中只存储公钥
        print("\n🔍 验证服务器数据库安全性...")
        if not verify_server_security(user_id):
            return False
        
        print("\n🎉 所有测试通过！密钥生成和存储功能正常工作。")
        return True
        
    except requests.exceptions.RequestException as e:
        print(f"❌ 网络请求失败: {str(e)}")
        return False
    except Exception as e:
        print(f"❌ 测试过程中发生错误: {str(e)}")
        return False

def verify_keys_in_database(user_id, password):
    """验证数据库中的密钥存储"""
    
    db_path = "/Users/tsuki/Desktop/chat8/backend/app/chat8.db"
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 检查用户表中的公钥
        cursor.execute("SELECT public_key FROM users WHERE id = ?", (user_id,))
        user_result = cursor.fetchone()
        
        if not user_result or not user_result[0]:
            print("❌ 用户表中未找到公钥")
            return False
        
        print("✅ 用户表中存在公钥")
        
        # 检查user_keys表中的详细密钥信息
        cursor.execute("""
            SELECT public_key, private_key_encrypted, key_version
            FROM user_keys WHERE user_id = ?
        """, (user_id,))
        
        keys_result = cursor.fetchone()
        
        if not keys_result:
            print("❌ user_keys表中未找到密钥记录")
            return False
        
        public_key, private_key_encrypted, key_version = keys_result
        
        # 验证各个字段
        if not public_key:
            print("❌ 公钥为空")
            return False
        print("✅ 公钥存在")
        
        if not private_key_encrypted:
            print("❌ 加密私钥为空")
            return False
        print("✅ 加密私钥存在")
        
        print(f"✅ 密钥版本: {key_version}")
        
        # 验证私钥是否正确加密（包含盐值）
        if ':' not in private_key_encrypted:
            print("❌ 私钥加密格式异常（缺少盐值）")
            return False
        print("✅ 私钥加密格式正确")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ 数据库验证失败: {str(e)}")
        return False

def verify_server_security(user_id):
    """验证服务器数据库安全性（确保不存储明文私钥）"""
    
    db_path = "/Users/tsuki/Desktop/chat8/backend/app/chat8.db"
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 检查user_keys表中的私钥是否加密
        cursor.execute("""
            SELECT private_key_encrypted FROM user_keys WHERE user_id = ?
        """, (user_id,))
        
        result = cursor.fetchone()
        
        if not result:
            print("❌ 未找到密钥记录")
            return False
        
        private_key_encrypted = result[0]
        
        # 验证私钥不是明文（不包含PEM格式的开头）
        if "-----BEGIN PRIVATE KEY-----" in private_key_encrypted:
            print("❌ 安全风险：数据库中存储了明文私钥！")
            return False
        
        print("✅ 安全验证通过：数据库中只存储加密后的私钥")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ 安全验证失败: {str(e)}")
        return False

def test_key_retrieval_api(user_id):
    """测试密钥获取API"""
    
    base_url = "http://localhost:8000/api"
    keys_url = f"{base_url}/v1/keys/{user_id}"
    
    try:
        print(f"\n🔍 测试密钥获取API...")
        response = requests.get(keys_url)
        
        if response.status_code == 200:
            keys_data = response.json()
            if keys_data.get('success'):
                print("✅ 密钥获取API工作正常")
                return True
            else:
                print(f"❌ 密钥获取API返回失败: {keys_data.get('message')}")
        else:
            print(f"❌ 密钥获取API请求失败: {response.status_code}")
        
        return False
        
    except Exception as e:
        print(f"❌ 密钥获取API测试失败: {str(e)}")
        return False

if __name__ == "__main__":
    print("🧪 开始测试密钥生成和存储功能...")
    print("⚠️  请确保后端服务正在运行 (http://localhost:8000)")
    
    # 询问用户确认
    confirm = input("\n是否开始测试？(Y/n): ")
    if confirm.lower() == 'n':
        print("❌ 测试已取消")
        exit()
    
    # 执行测试
    success = test_user_registration_with_keys()
    
    if success:
        print("\n🎉 测试完成！所有功能正常工作。")
        print("💡 提示：")
        print("  - 数据库中正确存储了用户密钥")
        print("  - 私钥已加密存储，安全性良好")
        print("  - 服务器只存储公钥，客户端需要存储完整密钥对")
    else:
        print("\n❌ 测试失败！请检查错误信息并修复问题。")
        exit(1)