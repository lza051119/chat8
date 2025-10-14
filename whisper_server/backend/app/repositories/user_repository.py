from sqlalchemy.orm import Session
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.repositories.base_repository import BaseRepository
from app.db.models import User
from app.schemas.user import UserCreate
from app.core.security import hash_password

class UserRepository(BaseRepository[User]):
    """
    用户数据仓库，封装了所有与User模型相关的异步数据库操作。
    """
    async def get_by_username(self, db: AsyncSession, *, username: str) -> User | None:
        """
        根据用户名查找用户。
        """
        result = await db.execute(select(User).filter(User.username == username))
        return result.scalars().first()

    async def get_by_email(self, db: AsyncSession, *, email: str) -> User | None:
        """
        根据邮箱查找用户。
        """
        result = await db.execute(select(User).filter(User.email == email))
        return result.scalars().first()

    async def create(self, db: AsyncSession, *, obj_in: UserCreate) -> User:
        """
        创建一个新用户，并对密码进行哈希处理。
        """
        db_obj = User(
            username=obj_in.username,
            email=obj_in.email,
            password_hash=hash_password(obj_in.password)
        )
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

user_repository = UserRepository(User) 