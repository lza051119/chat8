from pydantic import BaseModel, Field
from datetime import datetime

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