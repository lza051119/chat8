from sqlalchemy.orm import Session
from ..db import models
from datetime import datetime, timedelta, timezone
from typing import List, Tuple
from .message_db_service import MessageDBService
from sqlalchemy.ext.asyncio import AsyncSession
from ..repositories.message_repository import message_repository
from ..schemas.message import MessageCreate
from ..db.models import Message

# 中国时区
CHINA_TZ = timezone(timedelta(hours=8))

class MessageService:
    async def create_message(self, db: AsyncSession, *, message_in: MessageCreate, from_user_id: int) -> Message:
        """
        创建一条新消息。
        """
        create_data = message_in.model_dump()
        # Ensure 'to' field is used for to_user_id
        create_data['to_user_id'] = create_data.pop('to')
        create_data['from_user_id'] = from_user_id
        return await message_repository.create(db, obj_in=create_data)

    async def get_message_history(
        self, 
        db: AsyncSession, 
        *, 
        user_id: int, 
        friend_id: int,
        skip: int,
        limit: int
    ) -> list[Message]:
        """
        获取两个用户间的聊天记录。
        """
        return await message_repository.get_history_with_user(
            db, user_id=user_id, friend_id=friend_id, skip=skip, limit=limit
        )

    async def delete_message(self, db: AsyncSession, user_id: int, message_id: int) -> Tuple[bool, str]:
        """
        删除一条消息。
        """
        message = await message_repository.get(db, id=message_id)
        if not message:
            return False, "消息不存在"
        
        # 只有发送者或接收者可以删除
        if message.from_user_id != user_id and message.to_user_id != user_id:
            return False, "无权限删除该消息"
        
        await message_repository.remove(db, id=message_id)
        return True, "消息删除成功"

message_service = MessageService()