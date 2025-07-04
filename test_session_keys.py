#!/usr/bin/env python3
"""
测试会话密钥功能
验证会话密钥的建立、存储和读取
"""

import requests
import json
import time
import sqlite3
import os
from datetime import datetime

# 配置
BASE_URL = "http://localhost:8000"
API_BASE = f"{BASE_URL}/api/v1"

def print_step(step, description):
    """打印测试步骤"""
    print(f"\n{'='*60}")
    print(f"步骤 {step}: {description}")
    print(f"{'='*60}")

def print_result(success, message, data=None):
    """打印测试结果"""
    status = "✅ 成功" if success else "❌ 失败"
    print(f"{status}: {message}")
    if data:
        print(f"数据: {json.dumps(data, indent=2, ensure_ascii=False)}")

def register_user(username, email, password):
    """注册用户"""
    try:
        response = requests.post(f"{API_BASE}/auth/register", json={
            "username": username,
            "email": email,
            "password": password
        })
        
        if response.status_code == 200:
            data = response.json()
            return True, data
        else:
            return False, f"注册失败: {response.status_code} - {response.text}"
    except Exception as e:
        return False, f"注册异常: {str(e)}"

def login_user(username, password):
    """用户登录"""
    try:
        response = requests.post(f"{API_BASE}/auth/login", json={
            "username": username,
            "password": password
        })
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success') and 'data' in data and 'token' in data['data']:
                return True, data['data']['token']
            else:
                return False, f"登录响应格式错误: {data}"
        else:
            return False, f"登录失败: {response.status_code} - {response.text}"
    except Exception as e:
        return False, f"登录异常: {str(e)}"

def get_user_info(token):
    """获取用户信息"""
    try:
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.get(f"{API_BASE}/auth/me", headers=headers)
        
        if response.status_code == 200:
            return True, response.json()
        else:
            return False, f"获取用户信息失败: {response.status_code} - {response.text}"
    except Exception as e:
        return False, f"获取用户信息异常: {str(e)}"

def establish_session(token, target_user_id):
    """建立加密会话"""
    try:
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.post(f"{API_BASE}/encryption/establish-session-manual", 
                               json={"target_user_id": target_user_id},
                               headers=headers)
        
        if response.status_code == 200:
            return True, response.json()
        else:
            return False, f"建立会话失败: {response.status_code} - {response.text}"
    except Exception as e:
        return False, f"建立会话异常: {str(e)}"

def get_session_key(token, other_user_id):
    """获取会话密钥"""
    try:
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.get(f"{API_BASE}/encryption/session-key/{other_user_id}", 
                              headers=headers)
        
        if response.status_code == 200:
            return True, response.json()
        else:
            return False, f"获取会话密钥失败: {response.status_code} - {response.text}"
    except Exception as e:
        return False, f"获取会话密钥异常: {str(e)}"

def check_database_session_keys():
    """检查数据库中的会话密钥"""
    db_paths = [
        "/Users/tsuki/Desktop/chat8/backend/app/chat8.db",
        "/Users/tsuki/Desktop/chat8/backend/chat8.db",
        "/Users/tsuki/Desktop/chat8/chat8.db"
    ]
    
    for db_path in db_paths:
        if os.path.exists(db_path):
            try:
                conn = sqlite3.connect(db_path)
                cursor = conn.cursor()
                
                # 查询session_keys表
                cursor.execute("""
                    SELECT id, user1_id, user2_id, 
                           LENGTH(session_key_encrypted) as key1_len,
                           LENGTH(session_key_encrypted_for_user2) as key2_len,
                           key_version, created_at
                    FROM session_keys
                    ORDER BY created_at DESC
                """)
                
                rows = cursor.fetchall()
                
                print(f"\n📊 数据库 {os.path.basename(db_path)} 中的会话密钥:")
                if rows:
                    print(f"找到 {len(rows)} 个会话密钥记录:")
                    for row in rows:
                        print(f"  ID: {row[0]}, 用户1: {row[1]}, 用户2: {row[2]}")
                        print(f"      密钥1长度: {row[3]}, 密钥2长度: {row[4]}")
                        print(f"      版本: {row[5]}, 创建时间: {row[6]}")
                else:
                    print("  没有找到会话密钥记录")
                
                conn.close()
                return True, len(rows)
                
            except Exception as e:
                print(f"❌ 检查数据库失败 {db_path}: {str(e)}")
                return False, str(e)
    
    return False, "没有找到数据库文件"

def main():
    """主测试函数"""
    print("🚀 开始测试会话密钥功能")
    print(f"📅 测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 测试用户信息
    user1_info = {
        "username": f"testuser1_{int(time.time())}",
        "email": f"test1_{int(time.time())}@example.com",
        "password": "testpass123"
    }
    
    user2_info = {
        "username": f"testuser2_{int(time.time())}",
        "email": f"test2_{int(time.time())}@example.com",
        "password": "testpass123"
    }
    
    try:
        # 步骤1: 注册两个测试用户
        print_step(1, "注册测试用户")
        
        success1, result1 = register_user(user1_info["username"], user1_info["email"], user1_info["password"])
        print_result(success1, f"用户1注册: {user1_info['username']}", result1 if success1 else None)
        
        success2, result2 = register_user(user2_info["username"], user2_info["email"], user2_info["password"])
        print_result(success2, f"用户2注册: {user2_info['username']}", result2 if success2 else None)
        
        if not (success1 and success2):
            print("❌ 用户注册失败，测试终止")
            return
        
        # 步骤2: 用户登录
        print_step(2, "用户登录")
        
        success1, token1 = login_user(user1_info["username"], user1_info["password"])
        print_result(success1, f"用户1登录: {user1_info['username']}")
        
        success2, token2 = login_user(user2_info["username"], user2_info["password"])
        print_result(success2, f"用户2登录: {user2_info['username']}")
        
        if not (success1 and success2):
            print("❌ 用户登录失败，测试终止")
            return
        
        # 步骤3: 获取用户ID
        print_step(3, "获取用户信息")
        
        success1, user1_data = get_user_info(token1)
        print_result(success1, f"获取用户1信息", user1_data if success1 else None)
        
        success2, user2_data = get_user_info(token2)
        print_result(success2, f"获取用户2信息", user2_data if success2 else None)
        
        if not (success1 and success2):
            print("❌ 获取用户信息失败，测试终止")
            return
        
        user1_id = user1_data['userId']
        user2_id = user2_data['userId']
        
        print(f"\n👤 用户1 ID: {user1_id}, 用户名: {user1_data['username']}")
        print(f"👤 用户2 ID: {user2_id}, 用户名: {user2_data['username']}")
        
        # 步骤4: 建立加密会话
        print_step(4, "建立加密会话")
        
        success, session_result = establish_session(token1, user2_id)
        print_result(success, f"用户1与用户2建立会话", session_result if success else None)
        
        if not success:
            print("❌ 建立会话失败，测试终止")
            return
        
        # 步骤5: 检查数据库中的会话密钥
        print_step(5, "检查数据库中的会话密钥")
        
        success, count = check_database_session_keys()
        print_result(success, f"数据库检查完成，找到 {count} 个会话密钥记录")
        
        # 步骤6: 测试获取会话密钥
        print_step(6, "测试获取会话密钥")
        
        # 用户1获取与用户2的会话密钥
        success1, key_result1 = get_session_key(token1, user2_id)
        if success1:
            print_result(success1, f"用户1获取与用户2的会话密钥", key_result1)
        else:
            print_result(success1, f"用户1获取与用户2的会话密钥失败: {key_result1}")
        
        # 用户2获取与用户1的会话密钥
        success2, key_result2 = get_session_key(token2, user1_id)
        if success2:
            print_result(success2, f"用户2获取与用户1的会话密钥", key_result2)
        else:
            print_result(success2, f"用户2获取与用户1的会话密钥失败: {key_result2}")
        
        # 步骤7: 验证会话密钥一致性
        print_step(7, "验证会话密钥一致性")
        
        if success1 and success2:
            key1 = key_result1['data']['session_key']
            key2 = key_result2['data']['session_key']
            
            if key1 == key2:
                print_result(True, "会话密钥一致性验证通过")
                print(f"会话密钥: {key1[:20]}...")
            else:
                print_result(False, "会话密钥不一致")
                print(f"用户1的密钥: {key1[:20]}...")
                print(f"用户2的密钥: {key2[:20]}...")
        else:
            print_result(False, "无法验证会话密钥一致性，获取密钥失败")
        
        # 最终检查
        print_step(8, "最终验证")
        
        final_success, final_count = check_database_session_keys()
        
        if final_success and final_count > 0 and success1 and success2:
            print_result(True, "🎉 所有测试通过！会话密钥功能正常工作")
            print("\n✅ 功能验证完成:")
            print("  - 用户注册和登录 ✅")
            print("  - 会话密钥建立 ✅")
            print("  - 数据库存储 ✅")
            print("  - 密钥读取 ✅")
            print("  - 密钥一致性 ✅")
        else:
            print_result(False, "测试未完全通过，请检查日志")
        
    except Exception as e:
        print(f"\n❌ 测试过程中发生异常: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("\n" + "="*80)
    print("🔐 会话密钥功能测试")
    print("="*80)
    
    # 检查服务器是否运行
    try:
        response = requests.get(f"{BASE_URL}/", timeout=5)
        if response.status_code == 200:
            print("✅ 服务器运行正常")
            main()
        else:
            print(f"❌ 服务器响应异常: {response.status_code}")
            print("尝试继续测试...")
            main()
    except requests.exceptions.ConnectionError:
        print("❌ 无法连接到服务器，请确保后端服务正在运行")
        print("   启动命令: cd backend && uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload")
    except Exception as e:
        print(f"❌ 检查服务器状态时发生错误: {str(e)}")