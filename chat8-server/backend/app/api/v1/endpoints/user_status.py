from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from sqlalchemy.ext.asyncio import AsyncSession
from ...deps import get_db
from ....core.security import get_current_user
from ....services.user_states_update import get_user_presence_service
from pydantic import BaseModel
from typing import Optional
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

class HeartbeatRequest(BaseModel):
    """心跳请求模型"""
    timestamp: Optional[str] = None

class UserStatusResponse(BaseModel):
    """用户状态响应模型"""
    user_id: int
    username: str
    status: str
    last_seen: Optional[str]
    has_connection: bool
    last_heartbeat: Optional[str]

@router.post("/user-status/heartbeat")
async def send_heartbeat(
    heartbeat_data: HeartbeatRequest,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """发送心跳信号
    
    用于客户端主动发送心跳，更新用户在线状态
    """
    logger.info(f"[心跳API] 收到心跳请求，用户: {current_user.id}, 数据: {heartbeat_data}")
    try:
        user_id = int(current_user.id)
        user_states_service = get_user_presence_service()
        
        result = await user_states_service.update_user_heartbeat(db, user_id)
        
        if result["success"]:
            return JSONResponse(
                status_code=200,
                content={
                    "success": True,
                    "message": "心跳更新成功",
                    "timestamp": heartbeat_data.timestamp
                }
            )
        else:
            return JSONResponse(
                status_code=500,
                content={
                    "success": False,
                    "message": result["message"]
                }
            )
            
    except Exception as e:
        logger.error(f"[API] 心跳处理失败: {str(e)}")
        raise HTTPException(status_code=500, detail="心跳处理失败")

@router.get("/user-status/{user_id}")
async def get_user_status(
    user_id: int,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """获取指定用户的状态信息
    
    Args:
        user_id: 要查询的用户ID
    
    Returns:
        用户状态信息
    """
    try:
        user_states_service = get_user_presence_service()
        result = await user_states_service.get_user_status(db, user_id)
        
        if result["success"]:
            return JSONResponse(
                status_code=200,
                content={
                    "success": True,
                    "data": result["data"]
                }
            )
        else:
            return JSONResponse(
                status_code=404,
                content={
                    "success": False,
                    "message": result["message"]
                }
            )
            
    except Exception as e:
        logger.error(f"[API] 获取用户状态失败: {str(e)}")
        raise HTTPException(status_code=500, detail="获取用户状态失败")

@router.get("/user-status/me")
async def get_my_status(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """获取当前用户的状态信息"""
    try:
        user_id = current_user["user_id"]
        user_states_service = get_user_presence_service()
        result = await user_states_service.get_user_status(db, user_id)
        
        if result["success"]:
            return JSONResponse(
                status_code=200,
                content={
                    "success": True,
                    "data": result["data"]
                }
            )
        else:
            return JSONResponse(
                status_code=404,
                content={
                    "success": False,
                    "message": result["message"]
                }
            )
            
    except Exception as e:
        logger.error(f"[API] 获取当前用户状态失败: {str(e)}")
        raise HTTPException(status_code=500, detail="获取用户状态失败")

@router.get("/user-status/stats")
async def get_status_stats(
    current_user: dict = Depends(get_current_user)
):
    """获取状态服务统计信息
    
    仅供管理员或调试使用
    """
    try:
        user_states_service = get_user_presence_service()
        
        stats = {
            "online_users_count": user_states_service.get_online_users_count(),
            "heartbeat_users_count": user_states_service.get_heartbeat_users_count(),
            "heartbeat_interval": user_states_service.heartbeat_interval,
            "heartbeat_timeout": user_states_service.heartbeat_timeout
        }
        
        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "data": stats
            }
        )
        
    except Exception as e:
        logger.error(f"[API] 获取状态统计失败: {str(e)}")
        raise HTTPException(status_code=500, detail="获取状态统计失败")

@router.post("/user-status/force-logout/{user_id}")
async def force_user_logout(
    user_id: int,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """强制用户离线
    
    仅供管理员使用，强制将指定用户设置为离线状态
    
    Args:
        user_id: 要强制离线的用户ID
    """
    try:
        # 这里可以添加管理员权限检查
        # if not current_user.get("is_admin"):
        #     raise HTTPException(status_code=403, detail="权限不足")
        
        user_states_service = get_user_presence_service()
        result = await user_states_service.user_logout(db, user_id)
        
        if result["success"]:
            return JSONResponse(
                status_code=200,
                content={
                    "success": True,
                    "message": f"用户 {user_id} 已强制离线",
                    "notified_friends": result["notified_friends"]
                }
            )
        else:
            return JSONResponse(
                status_code=500,
                content={
                    "success": False,
                    "message": result["message"]
                }
            )
            
    except Exception as e:
        logger.error(f"[API] 强制用户离线失败: {str(e)}")
        raise HTTPException(status_code=500, detail="强制用户离线失败")

@router.post("/user-status/check-timeouts")
async def manual_check_timeouts(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """手动触发心跳超时检查
    
    仅供管理员或调试使用
    """
    try:
        # 这里可以添加管理员权限检查
        # if not current_user.get("is_admin"):
        #     raise HTTPException(status_code=403, detail="权限不足")
        
        user_states_service = get_user_presence_service()
        result = await user_states_service.check_heartbeat_timeouts(db)
        
        if result["success"]:
            return JSONResponse(
                status_code=200,
                content={
                    "success": True,
                    "message": "心跳超时检查完成",
                    "data": {
                        "checked_users": result["checked_users"],
                        "timeout_users": result["timeout_users"],
                        "processed_users": result["processed_users"]
                    }
                }
            )
        else:
            return JSONResponse(
                status_code=500,
                content={
                    "success": False,
                    "message": result["message"]
                }
            )
            
    except Exception as e:
        logger.error(f"[API] 手动心跳检查失败: {str(e)}")
        raise HTTPException(status_code=500, detail="心跳检查失败")