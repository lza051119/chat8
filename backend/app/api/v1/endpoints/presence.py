from fastapi import APIRouter, Depends
from core.security import get_current_user
from schemas.user import UserOut
from services import presence_service, friend_service
from db.database import SessionLocal
from typing import List
from pydantic import BaseModel

router = APIRouter()

class StatusUpdate(BaseModel):
    status: str

class P2PCapability(BaseModel):
    supportsP2P: bool
    capabilities: List[str]

@router.post('/presence/status')
def set_status(body: StatusUpdate, current_user: UserOut = Depends(get_current_user)):
    presence_service.set_status(int(current_user.id), body.status)
    return {"success": True, "message": "状态更新成功"}

@router.get('/presence/contacts')
def get_contacts_status(user_ids: str = None, current_user: UserOut = Depends(get_current_user)):
    if not user_ids:
        db = SessionLocal()
        try:
            friends = friend_service.get_friends(db, int(current_user.id), 1, 1000)
            # friends['items'] 返回的是字典列表，使用字典键访问
            id_list = [f['id'] if isinstance(f, dict) else f.id for f in friends['items']]
        finally:
            db.close()
    else:
        id_list = [int(uid) for uid in user_ids.split(',') if uid]
    return {"success": True, "data": presence_service.get_contacts_status(id_list)}

@router.post('/presence/heartbeat')
def heartbeat(current_user: UserOut = Depends(get_current_user)):
    return {"success": True, "data": presence_service.heartbeat(int(current_user.id))}

@router.post('/users/p2p-capability')
def register_p2p_capability(body: P2PCapability, current_user: UserOut = Depends(get_current_user)):
    # 注册用户的P2P能力
    # 这里可以将P2P能力信息存储到数据库或缓存中
    presence_service.set_p2p_capability(int(current_user.id), body.supportsP2P, body.capabilities)
    return {"success": True, "message": "P2P能力注册成功"}

@router.get('/users/{user_id}/status')
def get_user_status(user_id: int, current_user: UserOut = Depends(get_current_user)):
    # 获取指定用户的在线状态和P2P能力
    status = presence_service.get_user_status(user_id)
    return {
        "online": status.get('online', False),
        "supportsP2P": status.get('supportsP2P', False),
        "lastSeen": status.get('lastSeen')
    }