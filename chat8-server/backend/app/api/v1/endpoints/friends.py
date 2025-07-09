from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.deps import get_db
from app.services.friend_service import friend_service
from app.core.security import get_current_user
from app.schemas.user import UserOut

router = APIRouter()

@router.get("/contacts", response_model=list[UserOut])
async def get_contacts(
    db: AsyncSession = Depends(get_db),
    current_user: UserOut = Depends(get_current_user),
):
    """
    获取当前用户的好友列表。
    """
    friends = await friend_service.get_friends(db, user_id=current_user.id)
    return friends

@router.post("/contacts/request")
def send_friend_request(request: FriendRequestCreate, current_user: UserOut = Depends(get_current_user), db: Session = Depends(get_db)):
    """发送好友申请"""
    print("调用到好友申请了，接下来开始判断能否发起请求")
    res = friend_service.send_friend_request(db, int(current_user.id), request.to_user_id, request.message)
    if not res:
        # 检查具体原因
        target_user = db.query(models.User).filter(models.User.id == request.to_user_id).first()
        if not target_user:
            raise HTTPException(status_code=404, detail="用户不存在")
            print("用户不存在")
        
        if int(current_user.id) == request.to_user_id:
            raise HTTPException(status_code=400, detail="不能添加自己为好友")
            print("不能加自己为好友")
        
        # 检查是否已是好友（双向检查）
        from sqlalchemy import or_
        existing_friend = db.query(models.Friend).filter(
            or_(
                (models.Friend.user_id == int(current_user.id)) & (models.Friend.friend_id == request.to_user_id),
                (models.Friend.user_id == request.to_user_id) & (models.Friend.friend_id == int(current_user.id))
            )
        ).first()
        if existing_friend:
            raise HTTPException(status_code=400, detail="已经是好友")
            print("已经是好友")
        
        raise HTTPException(status_code=400, detail="已有待处理的好友申请")
        print("有一方已经发了好友请求")
    print("成功发送")
    return {"success": True, "message": "好友申请已发送", "data": {"request_id": res.id}}

@router.delete("/contacts/{friend_id}")
def delete_contact(friend_id: int, current_user: UserOut = Depends(get_current_user), db: Session = Depends(get_db)):
    ok = friend_service.remove_friend(db, int(current_user.id), friend_id)
    if not ok:
        raise HTTPException(status_code=404, detail="好友不存在")
    return {"success": True, "message": "联系人删除成功"}

@router.get("/requests")
def get_friend_requests(request_type: str = "received", current_user: UserOut = Depends(get_current_user), db: Session = Depends(get_db)):
    """获取好友申请列表"""
    requests = friend_service.get_friend_requests(db, int(current_user.id), request_type)
    return {"success": True, "data": requests}

@router.post("/requests/handle")
def handle_friend_request(response: FriendRequestResponse, current_user: UserOut = Depends(get_current_user), db: Session = Depends(get_db)):
    """处理好友申请"""
    if response.action not in ["accept", "reject"]:
        raise HTTPException(status_code=400, detail="无效的操作")
    
    res = friend_service.handle_friend_request(db, response.request_id, int(current_user.id), response.action)
    if not res:
        raise HTTPException(status_code=404, detail="申请不存在或已处理")
    
    message = "好友申请已同意" if response.action == "accept" else "好友申请已拒绝"
    return {"success": True, "message": message}