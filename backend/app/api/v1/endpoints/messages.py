from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.database import SessionLocal
from app.schemas.message import Message, MessageCreate
from app.services import message_service
from typing import List
from app.core.security import get_current_user
from app.schemas.user import UserOut

router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/messages", response_model=Message)
def send_message(msg: MessageCreate, current_user: UserOut = Depends(get_current_user), db: Session = Depends(get_db)):
    return message_service.send_message(
        db,
        from_id=int(current_user.id),
        to_id=msg.to_id,
        content=msg.content,
        encrypted=msg.encrypted,
        method=msg.method,
        destroy_after=msg.destroy_after,
        message_type=msg.message_type,
        file_path=msg.file_path,
        file_name=msg.file_name,
        hidding_message=msg.hidding_message
    )

@router.get("/messages/history/{peer_id}")
def get_history(peer_id: int, page: int = 1, limit: int = 50, current_user: UserOut = Depends(get_current_user), db: Session = Depends(get_db)):
    result = message_service.get_message_history(db, int(current_user.id), peer_id, page, limit)
    return result

@router.delete("/messages/{message_id}")
def delete_message(message_id: int, current_user: UserOut = Depends(get_current_user), db: Session = Depends(get_db)):
    ok, err = message_service.delete_message(db, int(current_user.id), message_id)
    if not ok:
        raise HTTPException(status_code=403 if err=="无权限删除该消息" else 404, detail=err)
    return {"success": True, "message": "消息删除成功"}