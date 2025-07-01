from sqlalchemy.orm import Session
from db.models import User
from core.security import hash_password, verify_password, create_access_token
from schemas.user import UserCreate, UserLogin, UserOut, TokenData
from db.database import SessionLocal
from fastapi import HTTPException
from datetime import datetime

def register_user(user: UserCreate):
    db: Session = SessionLocal()
    db_user = db.query(User).filter((User.username == user.username) | (User.email == user.email)).first()
    if db_user:
        db.close()
        raise HTTPException(status_code=400, detail="用户名或邮箱已存在")
    hashed_password = hash_password(user.password)
    db_user = User(username=user.username, password_hash=hashed_password, email=user.email, public_key=None)
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
    db.close()
    return {"success": True, "message": "注册成功", "data": {"user": user_out, "token": token}}

def authenticate_user(user: UserLogin):
    db: Session = SessionLocal()
    db_user = db.query(User).filter(User.username == user.username).first()
    if not db_user or not verify_password(user.password, str(db_user.password_hash)):
        db.close()
        raise HTTPException(status_code=401, detail="用户名或密码错误")
    user_out = UserOut(
        id=str(db_user.id),
        username=str(db_user.username),
        email=str(db_user.email),
        avatar=db_user.avatar,
        created_at=db_user.created_at
    )
    token = create_access_token({"sub": db_user.username})
    db.close()
    return {"success": True, "message": "登录成功", "data": {"user": user_out, "token": token}}

def search_users(query: str, page: int = 1, limit: int = 20):
    db: Session = SessionLocal()
    users_query = db.query(User).filter(
        (User.username.ilike(f"%{query}%")) | (User.email.ilike(f"%{query}%"))
    )
    total = users_query.count()
    users = users_query.offset((page-1)*limit).limit(limit).all()
    result = [
        {
            "id": u.id,
            "username": u.username,
            "email": u.email,
            "avatar": getattr(u, "avatar", None)
        } for u in users
    ]
    db.close()
    return {
        "items": result,
        "pagination": {
            "page": page,
            "limit": limit,
            "total": total,
            "totalPages": (total + limit - 1) // limit
        }
    }