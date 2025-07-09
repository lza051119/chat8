from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.repositories.base_repository import BaseRepository
from app.db.models import Friend, User

class FriendRepository(BaseRepository[Friend]):
    async def get_friends_by_user_id(self, db: AsyncSession, user_id: int) -> list[User]:
        """
        根据用户ID获取其所有好友的用户对象列表。
        """
        result = await db.execute(
            select(User)
            .join(Friend, Friend.friend_id == User.id)
            .filter(Friend.user_id == user_id)
        )
        return result.scalars().all()

friend_repository = FriendRepository(Friend) 