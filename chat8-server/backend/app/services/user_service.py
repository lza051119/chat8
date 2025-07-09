from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session
from app.db.models import User
from app.core.security import hash_password, verify_password, create_access_token
from app.schemas.user import UserCreate, UserLogin, UserOut, TokenData
from app.db.database import SessionLocal
from fastapi import HTTPException
from datetime import datetime
from sqlalchemy import or_
from app.repositories.user_repository import user_repository

class UserService:
    async def register_user(self, db: AsyncSession, *, user_in: UserCreate) -> User:
        """
        用户注册业务逻辑。
        """
        existing_user = await user_repository.get_by_username(db, username=user_in.username)
        if existing_user:
            raise HTTPException(status_code=400, detail="用户名已存在")
        
        existing_user = await user_repository.get_by_email(db, email=user_in.email)
        if existing_user:
            raise HTTPException(status_code=400, detail="邮箱已被注册")

        return await user_repository.create(db, obj_in=user_in)

    async def authenticate_user(self, db: AsyncSession, *, user_in: UserLogin) -> User:
        """
        用户认证业务逻辑。
        """
        user = await user_repository.get_by_username(db, username=user_in.username)
        if not user:
            raise HTTPException(status_code=401, detail="用户名或密码错误")
        
        if not verify_password(user_in.password, user.password_hash):
            raise HTTPException(status_code=401, detail="用户名或密码错误")
        
        return user

    def search_users(self, db: Session, query: str, page: int = 1, limit: int = 20):
        """
        搜索用户业务逻辑。
        """
        # 只保留最核心的精确匹配查询，暂时移除所有其他 filter()
        user = db.query(User).filter(
            (User.username == query) | (User.email == query)
        ).first()

        if user:
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
            return {
                "items": [],
                "pagination": {"page": 1, "limit": 0, "total": 0, "totalPages": 0}
            }

user_service = UserService()
