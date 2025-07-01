from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from db.database import SessionLocal
from schemas.friend import Friend, FriendCreate
from services import friend_service
from typing import List
from core.security import get_current_user
from schemas.user import UserOut

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
    # 用from_orm转换
    items = [Friend.from_orm(f) for f in result["items"]]
    result["items"] = items
    return {"success": True, "data": result}

@router.post("/contacts", response_model=Friend)
def add_contact(friend: FriendCreate, current_user: UserOut = Depends(get_current_user), db: Session = Depends(get_db)):
    res = friend_service.add_friend(db, int(current_user.id), friend.friendId)
    if not res:
        raise HTTPException(status_code=400, detail="已经是好友")
    return res

@router.delete("/contacts/{friend_id}")
def delete_contact(friend_id: int, current_user: UserOut = Depends(get_current_user), db: Session = Depends(get_db)):
    ok = friend_service.remove_friend(db, int(current_user.id), friend_id)
    if not ok:
        raise HTTPException(status_code=404, detail="好友不存在")
    return {"success": True, "message": "联系人删除成功"} 