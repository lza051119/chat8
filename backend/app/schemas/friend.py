from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional

class FriendBase(BaseModel):
    friendId: int = Field(..., alias="friend_id")

class FriendCreate(BaseModel):
    friendId: int = Field(..., alias="friend_id")

    class Config:
        populate_by_name = True

class Friend(FriendBase):
    id: int = Field(..., alias="id")
    userId: int = Field(..., alias="user_id")
    createdAt: datetime = Field(..., alias="created_at")

    class Config:
        from_attributes = True
        populate_by_name = True

# 好友申请相关schema
class FriendRequestCreate(BaseModel):
    to_user_id: int
    message: Optional[str] = None

class FriendRequestResponse(BaseModel):
    request_id: int
    action: str  # "accept" or "reject"

class FriendRequestOut(BaseModel):
    id: int
    from_user_id: int
    to_user_id: int
    status: str
    message: Optional[str] = None
    created_at: datetime
    from_user_username: str
    from_user_avatar: Optional[str] = None

    class Config:
        from_attributes = True