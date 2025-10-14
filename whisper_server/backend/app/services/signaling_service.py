from sqlalchemy.orm import Session
from ..db.models import SignalingMessage
from datetime import datetime
import json

def save_signaling_message(db: Session, from_user_id: int, to_user_id: int, msg_type: str, data: dict):
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
    return True

def get_pending_signaling(db: Session, user_id: int):
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
    return result