from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import or_, and_
from app.repositories.base_repository import BaseRepository
from app.db.models import Message

class MessageRepository(BaseRepository[Message]):
    async def get_history_with_user(
        self, 
        db: AsyncSession, 
        *, 
        user_id: int, 
        friend_id: int, 
        skip: int = 0, 
        limit: int = 100
    ) -> list[Message]:
        """
        获取两个用户之间的聊天记录。
        """
        result = await db.execute(
            select(Message)
            .filter(
                or_(
                    and_(Message.from_user_id == user_id, Message.to_user_id == friend_id),
                    and_(Message.from_user_id == friend_id, Message.to_user_id == user_id)
                )
            )
            .order_by(Message.timestamp.asc())
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()

message_repository = MessageRepository(Message) 