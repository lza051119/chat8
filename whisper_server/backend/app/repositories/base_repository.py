from typing import Any, Generic, Type, TypeVar
from sqlalchemy.orm import Session
from sqlalchemy.future import select
from app.db.database import Base
from sqlalchemy.ext.asyncio import AsyncSession

ModelType = TypeVar("ModelType", bound=Base)

class BaseRepository(Generic[ModelType]):
    """
    所有数据仓库类的异步基类。
    """
    def __init__(self, model: Type[ModelType]):
        """
        初始化Repository。

        :param model: SQLAlchemy的数据模型类。
        """
        self.model = model

    async def get(self, db: AsyncSession, id: Any) -> ModelType | None:
        """
        根据ID获取一个对象。
        """
        result = await db.execute(select(self.model).filter(self.model.id == id))
        return result.scalars().first()

    async def get_all(self, db: AsyncSession, *, skip: int = 0, limit: int = 100) -> list[ModelType]:
        """
        获取所有对象（支持分页）。
        """
        result = await db.execute(select(self.model).offset(skip).limit(limit))
        return result.scalars().all()

    async def create(self, db: AsyncSession, *, obj_in: dict) -> ModelType:
        """
        创建一个新对象。
        """
        db_obj = self.model(**obj_in)
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    async def update(self, db: AsyncSession, *, db_obj: ModelType, obj_in: dict) -> ModelType:
        """
        更新一个已存在的对象。
        """
        for field, value in obj_in.items():
            setattr(db_obj, field, value)
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    async def remove(self, db: AsyncSession, *, id: int) -> ModelType | None:
        """
        删除一个对象。
        """
        obj = await self.get(db, id)
        if obj:
            await db.delete(obj)
            await db.commit()
        return obj 