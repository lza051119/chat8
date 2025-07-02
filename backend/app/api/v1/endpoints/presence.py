from fastapi import APIRouter, Depends
from websocket.manager import ConnectionManager
from core.security import get_current_user
from schemas.user import UserOut
from services import friend_service
from services.unified_presence_service import unified_presence
from db.database import SessionLocal
from typing import List
from pydantic import BaseModel

router = APIRouter()

# Create a global connection manager instance
_connection_manager = ConnectionManager()

def get_connection_manager():
    return _connection_manager

class StatusUpdate(BaseModel):
    status: str

class P2PCapability(BaseModel):
    supportsP2P: bool
    capabilities: List[str]

@router.post("/presence/status")
async def set_status(
    status: StatusUpdate,
    current_user: UserOut = Depends(get_current_user),
    manager: ConnectionManager = Depends(get_connection_manager)
):
    """设置用户状态"""
    await unified_presence.set_user_status(current_user.id, status.status, manager)
    return {"message": "Status updated successfully"}

@router.get('/presence/contacts')
async def get_contacts_status(
    current_user: UserOut = Depends(get_current_user),
    manager: ConnectionManager = Depends(get_connection_manager)
):
    """获取联系人状态"""
    user_id = int(current_user.id)
    
    # 获取好友列表
    db = SessionLocal()
    try:
        print(f"[DEBUG] 获取用户 {user_id} 的好友列表")
        friends_result = friend_service.get_friends(db, user_id)
        print(f"[DEBUG] friends_result: {friends_result}")
        
        # friend_service.get_friends 返回 {'items': [...], 'total': int, 'page': int, 'limit': int}
        if isinstance(friends_result, dict) and 'items' in friends_result:
            friends = friends_result['items']
        else:
            friends = friends_result if friends_result else []
        
        print(f"[DEBUG] 处理后的friends: {friends}")
        friend_ids = [friend['id'] for friend in friends if friend and 'id' in friend]
        print(f"[DEBUG] friend_ids: {friend_ids}")
        
        # 获取好友状态
        contacts_status = await unified_presence.get_contacts_status(friend_ids, manager)
        print(f"[DEBUG] contacts_status: {contacts_status}")
        
        return {"success": True, "data": contacts_status}
    except Exception as e:
        print(f"[ERROR] get_contacts_status 错误: {str(e)}")
        import traceback
        traceback.print_exc()
        return {"success": False, "error": str(e)}
    finally:
        db.close()

@router.post('/presence/heartbeat')
async def heartbeat(current_user: UserOut = Depends(get_current_user)):
    """心跳更新"""
    user_id = int(current_user.id)
    manager = get_connection_manager()
    await unified_presence.heartbeat(user_id, manager)
    return {"success": True, "message": "心跳更新成功"}

@router.post("/presence/register_p2p")
async def register_p2p_capability(capabilities: P2PCapability, current_user: UserOut = Depends(get_current_user)):
    """注册P2P能力"""
    user_id = int(current_user.id)
    print(f"[DEBUG] 用户 {user_id} 注册P2P能力: {capabilities.dict()}")
    
    result = await unified_presence.set_p2p_capability(
        user_id, 
        capabilities.supportsP2P, 
        capabilities.capabilities
    )
    
    # 验证注册结果
    manager = get_connection_manager()
    status_check = await unified_presence.get_user_status(user_id, manager)
    print(f"[DEBUG] P2P注册后状态验证: {status_check}")
    
    return {"success": True, "message": "P2P能力注册成功", "data": result}



@router.get('/users/{user_id}/status')
async def get_user_status(user_id: int, current_user: UserOut = Depends(get_current_user)):
    """获取用户状态"""
    manager = get_connection_manager()
    status = await unified_presence.get_user_status(user_id, manager)
    return {"success": True, "data": status}