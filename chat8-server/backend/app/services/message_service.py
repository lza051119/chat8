from sqlalchemy.orm import Session
from app.db import models
from datetime import datetime, timedelta, timezone
from typing import List
from app.services.message_db_service import MessageDBService
from sqlalchemy.ext.asyncio import AsyncSession
from app.repositories.message_repository import message_repository
from app.schemas.message import MessageCreate
from app.db.models import Message

# 中国时区
CHINA_TZ = timezone(timedelta(hours=8))

def send_message(db: Session, from_id: int, to_id: int, encrypted_content: str, message_type: str = 'text', file_path: str = None, file_name: str = None, recipient_online: bool = False):
    # 服务器数据库只作为临时暂存，只有在接收方不在线时才保存
    china_now = datetime.now(CHINA_TZ)
    
    msg = None
    
    # 只有在接收方不在线时才保存到数据库
    if not recipient_online:
        msg = models.Message(
            from_id=from_id,
            to_id=to_id,
            encrypted_content=encrypted_content,
            message_type=message_type,
            file_path=file_path,
            file_name=file_name,
            timestamp=china_now,
            delivered=False
        )
        db.add(msg)
        db.commit()
        db.refresh(msg)
    
    return msg



def delete_server_message(db: Session, message_id: int):
    """删除服务器数据库中的消息（消息发送成功后调用）"""
    try:
        msg = db.query(models.Message).filter(models.Message.id == message_id).first()
        if msg:
            db.delete(msg)
            db.commit()
            # 服务器数据库中的消息已删除
            return True
        else:
            # 要删除的消息不存在
            return False
    except Exception as e:
        # 删除服务器消息失败
        return False

def get_offline_messages(db: Session, user_id: int):
    """获取用户的离线消息"""
    try:
        # 获取发送给该用户的所有未读消息（服务器数据库中的消息都是离线消息）
        offline_messages = db.query(models.Message).filter(
            models.Message.to_id == user_id
        ).order_by(models.Message.timestamp.asc()).all()
        

        
        # 获取到离线消息
        return offline_messages
    except Exception as e:
        # 获取离线消息失败
        return []

def get_message_history(db: Session, user_id: int, peer_id: int, page: int = 1, limit: int = 50):
    query = db.query(models.Message).filter(
        ((models.Message.from_id == user_id) & (models.Message.to_id == peer_id)) |
        ((models.Message.from_id == peer_id) & (models.Message.to_id == user_id))
    ).order_by(models.Message.timestamp.desc())
    
    total = query.count()
    messages = query.offset((page-1)*limit).limit(limit).all()
    
    # 转换消息格式，返回不透明的加密数据
    formatted_messages = []
    for msg in messages:
        formatted_msg = {
            "id": str(msg.id),
            "from": str(msg.from_id),
            "to": str(msg.to_id),
            "encrypted_content": msg.encrypted_content,
            "messageType": msg.message_type or 'text',
            "timestamp": msg.timestamp.isoformat(),
            "delivered": msg.delivered
        }
        formatted_messages.append(formatted_msg)
    
    return {
        "messages": formatted_messages,
        "pagination": {
            "page": page,
            "limit": limit,
            "total": total,
            "totalPages": (total + limit - 1) // limit
        }
    }

def delete_message(db: Session, user_id: int, message_id: int):
    msg = db.query(models.Message).filter(models.Message.id == message_id).first()
    if not msg:
        return False, "消息不存在"
    # 只有发送者或接收者可以删除
    if msg.from_id != user_id and msg.to_id != user_id:
        return False, "无权限删除该消息"
    db.delete(msg)
    db.commit()
    return True, None

class MessageService:
    async def create_message(self, db: AsyncSession, *, message_in: MessageCreate, from_user_id: int) -> Message:
        """
        创建一条新消息。
        """
        create_data = message_in.model_dump()
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

message_service = MessageService()