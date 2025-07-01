from fastapi import APIRouter, Depends
from core.security import get_current_user
from schemas.user import UserOut
from services import presence_service, friend_service
from typing import List

router = APIRouter()

@router.post('/presence/status')
def set_status(status: str, current_user: UserOut = Depends(get_current_user)):
    presence_service.set_status(int(current_user.id), status)
    return {"success": True, "message": "状态更新成功"}

@router.get('/presence/contacts')
def get_contacts_status(user_ids: str = None, current_user: UserOut = Depends(get_current_user)):
    if not user_ids:
        from db.database import SessionLocal
        db = SessionLocal()
        try:
            friends = friend_service.get_friends(db, int(current_user.id), 1, 1000)
            id_list = [f['id'] for f in friends]
        finally:
            db.close()
    else:
        id_list = [int(uid) for uid in user_ids.split(',') if uid]
    return {"success": True, "data": presence_service.get_contacts_status(id_list)}

@router.post('/presence/heartbeat')
def heartbeat(current_user: UserOut = Depends(get_current_user)):
    return {"success": True, "data": presence_service.heartbeat(int(current_user.id))} 