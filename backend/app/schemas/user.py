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
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }

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

class UserProfileBase(BaseModel):
    birthday: Optional[str] = None
    age: Optional[int] = None
    gender: Optional[str] = None
    hobbies: Optional[str] = None
    signature: Optional[str] = None
    display_name: Optional[str] = None

class UserProfileCreate(UserProfileBase):
    pass

class UserProfileUpdate(UserProfileBase):
    pass

class UserProfileOut(UserProfileBase):
    id: int
    user_id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class UserProfileWithUserInfo(UserProfileBase):
    """包含用户基本信息的个人资料"""
    id: int
    user_id: int
    username: str
    email: str
    avatar: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

# 密码重置相关模型
class ForgotPasswordRequest(BaseModel):
    email: str

class VerifyCodeRequest(BaseModel):
    email: str
    code: str

class ResetPasswordRequest(BaseModel):
    email: str
    code: str
    new_password: str