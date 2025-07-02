from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.database import SessionLocal
from app.db import models
from app.schemas.friend import Friend, FriendCreate, FriendRequestCreate, FriendRequestResponse, FriendRequestOut
from app.services import friend_service
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

@router.get("/contacts")
def get_contacts(page: int = 1, limit: int = 50, current_user: UserOut = Depends(get_current_user), db: Session = Depends(get_db)):
    result = friend_service.get_friends(db, int(current_user.id), page, limit)
    # 直接返回用户信息数据，无需转换
    return {"success": True, "data": result}

@router.post("/contacts/request")
def send_friend_request(request: FriendRequestCreate, current_user: UserOut = Depends(get_current_user), db: Session = Depends(get_db)):
    """发送好友申请"""
    res = friend_service.send_friend_request(db, int(current_user.id), request.to_user_id, request.message)
    if not res:
        # 检查具体原因
        target_user = db.query(models.User).filter(models.User.id == request.to_user_id).first()
        if not target_user:
            raise HTTPException(status_code=404, detail="用户不存在")
        
        if int(current_user.id) == request.to_user_id:
            raise HTTPException(status_code=400, detail="不能添加自己为好友")
        
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
        
        raise HTTPException(status_code=400, detail="已有待处理的好友申请")
    
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