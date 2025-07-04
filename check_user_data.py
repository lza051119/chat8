#!/usr/bin/env python3

import sqlite3

def check_user_data():
    """检查数据库中的用户数据"""
    
    db_path = "/Users/tsuki/Desktop/chat8/backend/app/chat8.db"
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 检查最近的用户记录
        cursor.execute("SELECT id, username, public_key FROM users ORDER BY id DESC LIMIT 5")
        users = cursor.fetchall()
        
        print("最近的用户记录:")
        for user in users:
            user_id, username, public_key = user
            public_key_status = "存在" if public_key else "空"
            print(f"ID: {user_id}, Username: {username}, Public Key: {public_key_status}")
        
        # 检查user_keys表中的记录
        cursor.execute("SELECT user_id, public_key, key_version FROM user_keys ORDER BY id DESC LIMIT 5")
        keys = cursor.fetchall()
        
        print("\nuser_keys表中的记录:")
        for key_record in keys:
            user_id, public_key, key_version = key_record
            public_key_status = "存在" if public_key else "空"
            print(f"User ID: {user_id}, Public Key: {public_key_status}, Version: {key_version}")
        
        conn.close()
        
    except Exception as e:
        print(f"检查失败: {str(e)}")

if __name__ == "__main__":
    check_user_data()