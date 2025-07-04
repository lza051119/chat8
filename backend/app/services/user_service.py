from sqlalchemy.orm import Session
from app.db.models import User
from app.core.security import hash_password, verify_password, create_access_token
from app.schemas.user import UserCreate, UserLogin, UserOut, TokenData
from app.db.database import SessionLocal
from fastapi import HTTPException
from datetime import datetime
from app.services.encryption_service import encryption_service
from app.services.user_keys_service import UserKeysService

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
        db_user = User(username=user.username, password_hash=hashed_password, email=user.email, public_key=None)
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        
        # 为新用户创建密钥对
        keys_result = UserKeysService.create_user_keys(db_user.id, user.password)
        if not keys_result.get('success'):
            print(f"Warning: Failed to create keys for user {db_user.id}: {keys_result.get('message')}")
        
        # 为新用户设置端到端加密（保持原有逻辑）
        encryption_result = encryption_service.setup_user_encryption(db_user.id)
        if not encryption_result.get('success'):
            print(f"Warning: Failed to setup encryption for user {db_user.id}: {encryption_result.get('error')}")
        
        # 更新用户的public_key字段（使用新生成的密钥）
        if keys_result.get('success'):
            db_user.public_key = keys_result['data']['public_key']
            db.commit()
        
        user_out = UserOut(
            id=str(db_user.id),
            username=str(db_user.username),
            email=str(db_user.email),
            avatar=db_user.avatar,
            created_at=db_user.created_at
        )
        token = create_access_token({"sub": db_user.username})
        
        response_data = {"user": user_out, "token": token}
        
        # 添加密钥信息到响应（不包含私钥，私钥应该保密）
        if keys_result.get('success'):
            response_data["keys"] = {
                "public_key": keys_result['data']['public_key'],
                "key_version": keys_result['data']['key_version'],
                "has_private_key": True
            }
        
        # 添加原有加密信息
        if encryption_result.get('success'):
            response_data["encryption"] = {
                "public_key": encryption_result['public_key'],
                "registration_id": encryption_result['registration_id']
            }
        
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
        (User.username == query) | (User.email == query)
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