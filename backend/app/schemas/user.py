from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class UserBase(BaseModel):
    username: str
    email: str
    avatar: Optional[str] = Field(None, alias="avatarUrl")

class UserCreate(UserBase):
    password: str

class UserOut(BaseModel):
    id: str = Field(..., alias="userId")
    username: str
    email: str
    avatar: Optional[str] = None
    created_at: datetime = Field(..., alias="createdAt")

    class Config:
        from_attributes = True
        populate_by_name = True

class UserLogin(BaseModel):
    username: str
    password: str

class TokenData(BaseModel):
    token: str
    user: UserOut

class ResponseModel(BaseModel):
    success: bool
    message: Optional[str] = None
    data: Optional[dict] = None
    error: Optional[str] = None 