from db.models import User
from db.database import SessionLocal
from datetime import datetime

def set_status(user_id: int, status: str):
    db = SessionLocal()
    user = db.query(User).filter(User.id == user_id).first()
    if user:
        user.status = status
        if status == 'online':
            user.last_seen = datetime.utcnow()
        db.commit()
    db.close()
    return True

def get_contacts_status(user_ids: list):
    db = SessionLocal()
    users = db.query(User).filter(User.id.in_(user_ids)).all()
    result = [
        {
            "userId": str(u.id),
            "username": u.username,
            "status": getattr(u, "status", "offline"),
            "lastSeen": u.last_seen,
        } for u in users
    ]
    db.close()
    return result

def heartbeat(user_id: int):
    db = SessionLocal()
    user = db.query(User).filter(User.id == user_id).first()
    if user:
        user.last_seen = datetime.utcnow()
        db.commit()
    db.close()
    return {"nextHeartbeat": 30000} 