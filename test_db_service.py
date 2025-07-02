#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
直接测试 MessageDBService 的脚本
绕过 API 认证，直接测试数据库服务层
"""

import sys
import os

# 添加后端路径到 Python 路径
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend', 'app'))

from services.message_db_service import MessageDBService
import json

def test_get_messages():
    """测试获取消息功能"""
    print("=== 测试 MessageDBService.get_messages_with_friend ===")
    
    # 测试参数
    user_id = 18  # 用户 18
    friend_id = 19  # 好友 19
    limit = 20
    offset = 0
    
    try:
        print(f"正在获取用户 {user_id} 与好友 {friend_id} 的消息...")
        
        # 调用服务方法
        messages, total_count, has_more = MessageDBService.get_messages_with_friend(
            user_id=user_id,
            friend_id=friend_id,
            limit=limit,
            offset=offset
        )
        
        print(f"\n✅ 成功获取消息！")
        print(f"📊 统计信息:")
        print(f"   - 返回消息数量: {len(messages)}")
        print(f"   - 总消息数量: {total_count}")
        print(f"   - 是否还有更多: {has_more}")
        
        if messages:
            print(f"\n📝 消息详情:")
            for i, msg in enumerate(messages[:5]):  # 只显示前5条
                print(f"   消息 {i+1}:")
                print(f"     - ID: {msg.get('id')}")
                print(f"     - 发送者: {msg.get('from')}")
                print(f"     - 接收者: {msg.get('to')}")
                print(f"     - 内容: {msg.get('content')[:50]}{'...' if len(msg.get('content', '')) > 50 else ''}")
                print(f"     - 时间: {msg.get('timestamp')}")
                print(f"     - 消息类型: {msg.get('messageType')}")
                print(f"     - 文件路径: {msg.get('filePath')}")
                print(f"     - 文件名: {msg.get('fileName')}")
                print()
            
            if len(messages) > 5:
                print(f"   ... 还有 {len(messages) - 5} 条消息未显示")
        else:
            print("\n📭 没有找到消息")
            
        return True
        
    except Exception as e:
        print(f"\n❌ 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def test_database_status():
    """测试数据库状态"""
    print("\n=== 测试数据库状态 ===")
    
    user_id = 18
    
    try:
        # 获取数据库路径
        db_path = MessageDBService.get_user_db_path(user_id)
        print(f"数据库路径: {db_path}")
        print(f"数据库文件存在: {os.path.exists(db_path)}")
        
        # 获取数据库状态
        status = MessageDBService.get_database_status(user_id)
        print(f"数据库状态: {json.dumps(status, indent=2, ensure_ascii=False)}")
        
        return True
        
    except Exception as e:
        print(f"❌ 获取数据库状态失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🔍 开始测试 MessageDBService...\n")
    
    # 测试数据库状态
    status_ok = test_database_status()
    
    # 测试获取消息
    messages_ok = test_get_messages()
    
    print("\n" + "="*50)
    if status_ok and messages_ok:
        print("✅ 所有测试通过！数据库服务工作正常。")
    else:
        print("❌ 部分测试失败，请检查错误信息。")
    print("="*50)