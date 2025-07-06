from app.db.database import SessionLocal
from app.db.models import SignalingMessage
from datetime import datetime
import json

def save_signaling_message(from_user_id: int, to_user_id: int, msg_type: str, data: dict):
    db = SessionLocal()
    msg = SignalingMessage(
        from_user_id=from_user_id,
        to_user_id=to_user_id,
        msg_type=msg_type,
        data=json.dumps(data),
        timestamp=datetime.utcnow(),
        is_handled=False
    )
    db.add(msg)
    db.commit()
    db.close()
    return True

def get_pending_signaling(user_id: int):
    db = SessionLocal()
    msgs = db.query(SignalingMessage).filter_by(to_user_id=user_id, is_handled=False).all()
    result = []
    for m in msgs:
        result.append({
            "id": m.id,
            "type": m.msg_type,
            "fromUserId": m.from_user_id,
            "data": json.loads(m.data),
            "timestamp": m.timestamp
        })
        m.is_handled = True
    db.commit()
    db.close()
    return result