#!/usr/bin/env python3

import sys
sys.path.append('/Users/tsuki/Desktop/大二下/chat8/backend')

from app.db.database import SessionLocal
from app.db.models import User

def check_users():
    db = SessionLocal()
    try:
        users = db.query(User).all()
        print("=== 数据库中的用户信息 ===")
        for user in users:
            print(f"ID: {user.id}")
            print(f"用户名: {user.username}")
            print(f"邮箱: {user.email}")
            print(f"密码哈希: {user.password_hash[:50]}...")
            print(f"创建时间: {user.created_at}")
            print("-" * 50)
    finally:
        db.close()

if __name__ == "__main__":
    check_users()