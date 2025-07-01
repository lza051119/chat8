from sqlalchemy.orm import Session
from db import models
from datetime import datetime

def get_friends(db: Session, user_id: int, page: int = 1, limit: int = 50):
    query = db.query(models.Friend).filter(models.Friend.user_id == user_id)
    total = query.count()
    friends = query.offset((page-1)*limit).limit(limit).all()
    return {
        "items": friends,
        "pagination": {
            "page": page,
            "limit": limit,
            "total": total,
            "totalPages": (total + limit - 1) // limit
        }
    }

def add_friend(db: Session, user_id: int, friend_id: int):
    # 检查是否已是好友
    exists = db.query(models.Friend).filter_by(user_id=user_id, friend_id=friend_id).first()
    if exists:
        return None
    friend = models.Friend(user_id=user_id, friend_id=friend_id, created_at=datetime.utcnow())
    db.add(friend)
    db.commit()
    db.refresh(friend)
    return friend

def remove_friend(db: Session, user_id: int, friend_id: int):
    friend = db.query(models.Friend).filter_by(user_id=user_id, friend_id=friend_id).first()
    if friend:
        db.delete(friend)
        db.commit()
        return True
    return False 