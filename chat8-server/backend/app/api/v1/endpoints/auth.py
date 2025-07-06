from fastapi import APIRouter, Depends
from app.schemas.user import UserCreate, UserLogin, UserOut, ResponseModel, ForgotPasswordRequest, VerifyCodeRequest, ResetPasswordRequest
from app.services.user_service import register_user, authenticate_user, search_users
from app.services.password_reset_service import PasswordResetService
from app.core.security import get_current_user, create_access_token
from fastapi.security import OAuth2PasswordRequestForm
from app.services import security_event_service

router = APIRouter()

@router.post('/auth/register')
def register(user: UserCreate):
    res = register_user(user)
    print("马上要开始验证了")
    if res.get("success"):
        security_event_service.log_event(res["data"]["user"].id, "register", f"用户注册: {user.username}")
    print("验证成功了")
    return res

@router.post('/auth/login')
def login(user: UserLogin):
    res = authenticate_user(user)
    if res.get("success"):
        security_event_service.log_event(res["data"]["user"].id, "login", f"用户登录: {user.username}")
    return res

@router.get('/auth/me', response_model=UserOut)
def get_me(current_user: UserOut = Depends(get_current_user)):
    # 从数据库获取最新的用户信息，确保头像等信息是最新的
    from app.db.database import SessionLocal
    from app.db.models import User
    
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.id == int(current_user.id)).first()
        if user:
            return UserOut(
                id=user.id,
                username=user.username,
                email=user.email,
                avatar=user.avatar,
                created_at=user.created_at
            )
        return current_user
    finally:
        db.close()

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

# 密码重置相关API
@router.post('/auth/forgot-password')
async def forgot_password(request: ForgotPasswordRequest):
    """发送密码重置验证码"""
    return await PasswordResetService.send_reset_code(request.email)

@router.post('/auth/verify-reset-code')
def verify_reset_code(request: VerifyCodeRequest):
    """验证重置验证码"""
    return PasswordResetService.verify_reset_code(request.email, request.code)

@router.post('/auth/reset-password')
def reset_password(request: ResetPasswordRequest):
    """重置密码"""
    return PasswordResetService.reset_password(request.email, request.code, request.new_password)