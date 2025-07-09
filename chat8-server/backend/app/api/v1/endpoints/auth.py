from typing import Any
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from sqlalchemy.ext.asyncio import AsyncSession
import json

from .... import schemas
from ...deps import get_db
from ....services.user_service import user_service
from ....core.security import create_access_token, get_current_user
from ....websocket.manager import manager as websocket_manager
from ....services.user_states_update import UserPresenceService, get_user_presence_service
from ....schemas.user import UserCreate, UserLogin, UserOut, ResponseModel, ForgotPasswordRequest, VerifyCodeRequest, ResetPasswordRequest
from ....services.password_reset_service import PasswordResetService
from ....services import security_event_service

router = APIRouter()

async def force_logout_user(user_id: int, username: str, user_presence_service: UserPresenceService, db: AsyncSession):
    """
    在后台执行的强制下线任务
    """
    print(f"后台任务：开始强制下线用户 {username} (ID: {user_id})。")
    try:
        # 1. 发送强制下线通知
        await websocket_manager.send_personal_message(
            json.dumps({"event": "force_logout", "data": {"reason": "您已在其他设备登录"}}),
            user_id
        )
        # 2. 服务器主动断开旧的WebSocket连接
        if websocket_manager.is_user_connected(user_id):
            await websocket_manager.disconnect(user_id, 1000, "Forced logout")
        # 3. 将服务器上的状态标记为离线
        await user_presence_service.user_logout(db, user_id)
        print(f"后台任务：用户 {username} (ID: {user_id}) 的旧会话已成功终止。")
    except Exception as e:
        print(f"后台任务执行强制下线时出错: {e}")

@router.post("/auth/login", response_model=schemas.user.ResponseModel)
async def login(
    background_tasks: BackgroundTasks,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db),
    user_presence_service: UserPresenceService = Depends(get_user_presence_service),
) -> Any:
    """
    用户登录
    """
    user = await user_service.authenticate_user(
        db=db, user_in=schemas.user.UserLogin(username=form_data.username, password=form_data.password)
    )

    if user_presence_service.is_user_online(user.id):
        background_tasks.add_task(
            force_logout_user, user.id, user.username, user_presence_service, db
        )

    access_token = create_access_token(
        data={"sub": str(user.id), "username": user.username}
    )

    # 将 user ORM 模型转换为 Pydantic 模型，再转换为 dict
    user_out = schemas.user.UserOut.model_validate(user)

    return {
        "success": True,
        "message": "Login successful",
        "data": {
            "token": access_token,
            "user": user_out.model_dump(),
        },
    }

@router.post('/auth/register', response_model=schemas.user.ResponseModel)
async def register(user_in: schemas.user.UserCreate, db: AsyncSession = Depends(get_db)):
    user = await user_service.register_user(db=db, user_in=user_in)
    access_token = create_access_token(
        data={"sub": str(user.id), "username": user.username}
    )
    # 将 user ORM 模型转换为 Pydantic 模型，再转换为 dict
    user_out = schemas.user.UserOut.model_validate(user)
    return {
        "success": True, 
        "message": "注册成功", 
        "data": {
            "token": access_token,
            "user": user_out.model_dump()
        }
    }

@router.get('/auth/me', response_model=UserOut)
async def get_me(
    current_user: UserOut = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    # 从数据库获取最新的用户信息，确保头像等信息是最新的
    user = await user_service.get_user(db, user_id=int(current_user.id))
    if user:
        return user
    raise HTTPException(status_code=404, detail="User not found")

@router.post('/auth/logout')
def logout():
    # JWT无状态，前端只需丢弃token即可
    return {"success": True, "message": "退出登录成功"}

@router.post('/auth/refresh')
def refresh_token(current_user: UserOut = Depends(get_current_user)):
    token = create_access_token({"sub": current_user.username})
    return {"success": True, "data": {"token": token}}

@router.get('/users/search')
def user_search(q: str, page: int = 1, limit: int = 20, current_user: UserOut = Depends(get_current_user), db: Session = Depends(get_db)):
    return {"success": True, "data": user_service.search_users(db, q, page, limit)}

# 密码重置相关API
@router.post('/auth/forgot-password')
async def forgot_password(request: ForgotPasswordRequest, db: Session = Depends(get_db)):
    """发送密码重置验证码"""
    return await PasswordResetService.send_reset_code(db, request.email)

@router.post('/auth/verify-reset-code')
def verify_reset_code(request: VerifyCodeRequest, db: Session = Depends(get_db)):
    """验证重置验证码"""
    return PasswordResetService.verify_reset_code(db, request.email, request.code)

@router.post('/auth/reset-password')
def reset_password(request: ResetPasswordRequest, db: Session = Depends(get_db)):
    """重置密码"""
    return PasswordResetService.reset_password(db, request.email, request.code, request.new_password)