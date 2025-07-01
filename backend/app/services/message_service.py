from sqlalchemy.orm import Session
from db import models
from datetime import datetime, timedelta
from typing import List

def send_message(db: Session, from_id: int, to_id: int, content: str, encrypted: bool = True, method: str = 'Server', destroy_after: int = None):
    # 保存消息到数据库
    msg = models.Message(
        from_id=from_id,
        to_id=to_id,
        content=content,
        encrypted=encrypted,
        method=method,
        timestamp=datetime.utcnow(),
        destroy_after=destroy_after
    )
    db.add(msg)
    db.commit()
    db.refresh(msg)
    
    return msg



def get_message_history(db: Session, user_id: int, peer_id: int, page: int = 1, limit: int = 50):
    now = datetime.utcnow()
    query = db.query(models.Message).filter(
        ((models.Message.from_id == user_id) & (models.Message.to_id == peer_id)) |
        ((models.Message.from_id == peer_id) & (models.Message.to_id == user_id))
    ).order_by(models.Message.timestamp.desc())
    # 阅后即焚：删除已过期消息
    expired_msgs = []
    for m in query:
        if m.destroy_after:
            expire_time = m.timestamp + timedelta(seconds=m.destroy_after)
            if now > expire_time:
                expired_msgs.append(m)
    for m in expired_msgs:
        db.delete(m)
    if expired_msgs:
        db.commit()
    # 重新查询未过期消息
    query = db.query(models.Message).filter(
        ((models.Message.from_id == user_id) & (models.Message.to_id == peer_id)) |
        ((models.Message.from_id == peer_id) & (models.Message.to_id == user_id))
    ).order_by(models.Message.timestamp.desc())
    total = query.count()
    messages = query.offset((page-1)*limit).limit(limit).all()
    return {
        "messages": messages,
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