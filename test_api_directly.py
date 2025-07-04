#!/usr/bin/env python3
import sys
sys.path.append('/Users/tsuki/Desktop/chat8/backend')

from app.services.encryption_service import encryption_service

def test_get_session_key_directly():
    """直接测试encryption_service的get_session_key方法"""
    print("=== 直接测试 get_session_key 方法 ===")
    
    # 测试用户37获取与用户38的会话密钥
    print("\n--- 用户37获取与用户38的会话密钥 ---")
    result1 = encryption_service.get_session_key(37, 38)
    print(f"结果: {result1}")
    
    # 测试用户38获取与用户37的会话密钥
    print("\n--- 用户38获取与用户37的会话密钥 ---")
    result2 = encryption_service.get_session_key(38, 37)
    print(f"结果: {result2}")
    
    # 比较结果
    if result1.get('success') and result2.get('success'):
        key1 = result1.get('session_key')
        key2 = result2.get('session_key')
        print(f"\n--- 密钥比较 ---")
        print(f"用户37获取的密钥: {key1}")
        print(f"用户38获取的密钥: {key2}")
        print(f"密钥一致: {key1 == key2}")
    else:
        print("\n--- 获取密钥失败 ---")
        if not result1.get('success'):
            print(f"用户37失败: {result1.get('error')}")
        if not result2.get('success'):
            print(f"用户38失败: {result2.get('error')}")

if __name__ == "__main__":
    test_get_session_key_directly()