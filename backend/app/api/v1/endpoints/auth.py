from fastapi import APIRouter, Depends
from schemas.user import UserCreate, UserLogin, UserOut, ResponseModel
from services.user_service import register_user, authenticate_user, search_users
from core.security import get_current_user, create_access_token
from fastapi.security import OAuth2PasswordRequestForm
from services import security_event_service

router = APIRouter()

@router.post('/auth/register')
def register(user: UserCreate):
    res = register_user(user)
    if res.get("success"):
        security_event_service.log_event(res["data"]["user"].id, "register", f"用户注册: {user.username}")
    return res

@router.post('/auth/login')
def login(user: UserLogin):
    res = authenticate_user(user)
    if res.get("success"):
        security_event_service.log_event(res["data"]["user"].id, "login", f"用户登录: {user.username}")
    return res

@router.get('/auth/me', response_model=UserOut)
def get_me(current_user: UserOut = Depends(get_current_user)):
    return current_user

@router.post('/auth/logout')
def logout():
    # JWT无状态，前端只需丢弃token即可
    return {"success": True, "message": "退出登录成功"}

@router.post('/auth/refresh')
def refresh_token(current_user: UserOut = Depends(get_current_user)):
    token = create_access_token({"sub": current_user.username})
    return {"success": True, "data": {"token": token}}

@router.get('/users/search')
def user_search(q: str, page: int = 1, limit: int = 20, current_user: UserOut = Depends(get_current_user)):
    return {"success": True, "data": search_users(q, page, limit)}