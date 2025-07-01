from db.database import SessionLocal
from db.models import SecurityEvent
from datetime import datetime

def log_event(user_id: int, event_type: str, detail: str = None):
    db = SessionLocal()
    event = SecurityEvent(user_id=user_id, event_type=event_type, detail=detail, timestamp=datetime.utcnow())
    db.add(event)
    db.commit()
    db.close()
    return True

def get_events(user_id: int, limit: int = 20):
    db = SessionLocal()
    events = db.query(SecurityEvent).filter(SecurityEvent.user_id == user_id).order_by(SecurityEvent.timestamp.desc()).limit(limit).all()
    result = [
        {
            "eventType": e.event_type,
            "detail": e.detail,
            "timestamp": e.timestamp
        } for e in events
    ]
    db.close()
    return result