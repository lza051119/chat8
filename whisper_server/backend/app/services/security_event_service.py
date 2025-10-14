from sqlalchemy.orm import Session
from ..db.models import SecurityEvent
from datetime import datetime

def log_event(db: Session, user_id: int, event_type: str, detail: str = None):
    event = SecurityEvent(user_id=user_id, event_type=event_type, detail=detail, timestamp=datetime.utcnow())
    db.add(event)
    db.commit()
    return True

def get_events(db: Session, user_id: int, limit: int = 20):
    events = db.query(SecurityEvent).filter(SecurityEvent.user_id == user_id).order_by(SecurityEvent.timestamp.desc()).limit(limit).all()
    result = [
        {
            "eventType": e.event_type,
            "detail": e.detail,
            "timestamp": e.timestamp
        } for e in events
    ]
    return result