#!/usr/bin/env python3
import sys
sys.path.append('./backend')

from app.db.database import SessionLocal
from app.db.models import User

def check_user():
    db = SessionLocal()
    try:
        # 查询所有用户
        users = db.query(User).all()
        print(f"数据库中共有 {len(users)} 个用户:")
        for user in users:
            print(f"ID: {user.id}, 用户名: {user.username}, 邮箱: {user.email}")
        
        # 特别查询test@example.com
        test_user = db.query(User).filter(User.email == "test@example.com").first()
        if test_user:
            print(f"\n找到test@example.com用户: {test_user.username}")
        else:
            print("\n未找到test@example.com用户")
            
    except Exception as e:
        print(f"查询错误: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    check_user()