from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from ...deps import get_db
from ....services.friend_service import friend_service
from ....core.security import get_current_user
from ....schemas.user import UserOut
from ....schemas.friend import FriendRequestCreate, FriendRequestResponse, PaginatedFriendsResponse
from ....db import models

router = APIRouter()

@router.get("/contacts", response_model=PaginatedFriendsResponse)
async def get_contacts(
    db: AsyncSession = Depends(get_db),
    current_user: UserOut = Depends(get_current_user),
    page: int = 1,
    limit: int = 50
):
    """
    获取当前用户的好友列表。
    """
    friends_data = await friend_service.get_friends(db, user_id=int(current_user.id), page=page, limit=limit)
    return friends_data

@router.post("/contacts/request")
async def send_friend_request(request: FriendRequestCreate, current_user: UserOut = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """发送好友申请"""
    res = await friend_service.send_friend_request(
        db, 
        from_user_id=int(current_user.id), 
        to_user_id=request.to_user_id, 
        message=request.message
    )
    if not res["success"]:
        raise HTTPException(status_code=400, detail=res["message"])
    return res

@router.delete("/contacts/{friend_id}")
async def delete_contact(friend_id: int, current_user: UserOut = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    ok = await friend_service.remove_friend(db, int(current_user.id), friend_id)
    if not ok:
        raise HTTPException(status_code=404, detail="好友不存在或删除失败")
    return {"success": True, "message": "联系人删除成功"}

@router.get("/requests")
async def get_friend_requests(request_type: str = "received", current_user: UserOut = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """获取好友申请列表"""
    requests = await friend_service.get_friend_requests(db, int(current_user.id), request_type)
    return {"success": True, "data": requests}

@router.post("/requests/handle")
async def handle_friend_request(response: FriendRequestResponse, current_user: UserOut = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """处理好友申请"""
    if response.action not in ["accept", "reject"]:
        raise HTTPException(status_code=400, detail="无效的操作")
    
    res = await friend_service.handle_friend_request(db, response.request_id, int(current_user.id), response.action)
    if not res:
        raise HTTPException(status_code=404, detail="申请不存在或已处理")
    
    message = "好友申请已同意" if response.action == "accept" else "好友申请已拒绝"
    return {"success": True, "message": message}