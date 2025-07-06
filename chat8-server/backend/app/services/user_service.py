from sqlalchemy.orm import Session
from app.db.models import User
from app.core.security import hash_password, verify_password, create_access_token
from app.schemas.user import UserCreate, UserLogin, UserOut, TokenData
from app.db.database import SessionLocal
from fastapi import HTTPException
from datetime import datetime



def register_user(user: UserCreate):
    db: Session = SessionLocal()
    try:
        # 检查用户是否已存在
        db_user = db.query(User).filter((User.username == user.username) | (User.email == user.email)).first()
        if db_user:
            db.close()
            raise HTTPException(status_code=400, detail="用户名或邮箱已存在")
        
        # 创建用户
        hashed_password = hash_password(user.password)
        db_user = User(username=user.username, password_hash=hashed_password, email=user.email)
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        

        

        
        user_out = UserOut(
            id=str(db_user.id),
            username=str(db_user.username),
            email=str(db_user.email),
            avatar=db_user.avatar,
            created_at=db_user.created_at
        )
        token = create_access_token({"sub": db_user.username})
        
        response_data = {"user": user_out, "token": token}
        
        return {"success": True, "message": "注册成功", "data": response_data}
        
    except Exception as e:
        db.rollback()
        raise e
    finally:
        db.close()

def authenticate_user(user: UserLogin):
    db: Session = SessionLocal()
    db_user = db.query(User).filter(User.username == user.username).first()
    if not db_user or not verify_password(user.password, str(db_user.password_hash)):
        db.close()
        raise HTTPException(status_code=401, detail="用户名或密码错误")
    user_out = UserOut(
        id=db_user.id,
        username=str(db_user.username),
        email=str(db_user.email),
        avatar=db_user.avatar,
        created_at=db_user.created_at
    )
    token = create_access_token({"sub": db_user.username})
    db.close()
    return {"success": True, "message": "登录成功", "data": {"user": user_out, "token": token}}

def search_users(db: Session, query: str, page: int = 1, limit: int = 20):
    # 为了调试，我们先硬编码一个最简单的版本
    print(f"--- DEBUG: 正在数据库中精确搜索: '{query}' ---")
    
    # 只保留最核心的精确匹配查询，暂时移除所有其他 filter()
    user = db.query(User).filter(
        or_(User.username == query, User.email == query)
    ).first()
    
    db.close()

    if user:
        print(f"--- DEBUG: 在数据库中找到了用户! ID: {user.id}, Username: {user.username} ---")
        # 为了测试，我们只返回这个找到的用户
        return {
            "items": [{
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "avatar": getattr(user, "avatar", None)
            }],
            "pagination": {"page": 1, "limit": 1, "total": 1, "totalPages": 1}
        }
    else:
        print(f"--- DEBUG: 使用该精确查询，在数据库中没有找到任何用户。---")
        return {
            "items": [],
            "pagination": {"page": 1, "limit": 0, "total": 0, "totalPages": 0}
        }