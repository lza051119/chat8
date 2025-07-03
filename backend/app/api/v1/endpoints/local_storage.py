from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from db.database import SessionLocal
from core.security import get_current_user
from schemas.user import UserOut
from schemas.message import MessageCreate
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import json
import os
from datetime import datetime
from services.message_db_service import MessageDBService

router = APIRouter()  # 可读时间（秒）

class MessageQuery(BaseModel):
    friend_id: int
    current_user_id: int

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# 本地存储目录（保持兼容性）
LOCAL_STORAGE_DIR = os.path.join(os.getcwd(), 'local_storage', 'messages')
os.makedirs(LOCAL_STORAGE_DIR, exist_ok=True)

def get_user_messages_file(user_id: int) -> str:
    """获取用户消息文件路径（保持兼容性）"""
    return os.path.join(LOCAL_STORAGE_DIR, f'user_{user_id}_messages.json')

def load_user_messages(user_id: int) -> List[Dict]:
    """加载用户消息（已弃用，保持兼容性）"""
    file_path = get_user_messages_file(user_id)
    if not os.path.exists(file_path):
        return []
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"加载消息文件失败: {e}")
        return []

def save_user_messages(user_id: int, messages: List[Dict]) -> bool:
    """保存用户消息（已弃用，保持兼容性）"""
    file_path = get_user_messages_file(user_id)
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(messages, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        print(f"保存消息文件失败: {e}")
        return False

@router.post("/local-storage/messages")
async def add_message(message: MessageCreate, current_user: UserOut = Depends(get_current_user)):
    """添加新消息到本地存储"""
    try:
        # 准备消息数据
        message_data = {
            "id": getattr(message, 'id', None),
            "from": int(current_user.id),
            "to": message.to_id,
            "content": message.content,
            "timestamp": datetime.now().isoformat(),
            "method": message.method,
            "encrypted": message.encrypted,
            "message_type": message.message_type,  # 添加消息类型
            "hidding_message": message.hidding_message,  # 添加隐藏消息
            "is_burn_after_read": False,
            "readable_duration": message.destroy_after
        }
        
        # 只有图片消息才添加文件相关字段
        if message.message_type == 'image' and message.file_path:
            message_data["file_path"] = message.file_path
            message_data["file_name"] = message.file_name
        
        # 为发送者和接收者都保存消息
        users_to_update = [int(current_user.id), message.to_id]
        success_count = 0
        
        for user_id in users_to_update:
            if MessageDBService.add_message(user_id, message_data):
                success_count += 1
        
        if success_count > 0:
            return {"status": "success", "message": "消息已保存"}
        else:
            raise HTTPException(status_code=500, detail="消息保存失败")
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"保存消息失败: {str(e)}")

@router.get("/local-storage/messages")
async def get_messages(
    user_id: int = Query(..., description="用户ID"),
    friend_id: int = Query(..., description="好友ID"),
    limit: int = Query(50, description="每页消息数量"),
    offset: int = Query(0, description="偏移量"),
    search: str = Query(None, description="搜索关键词")
):
    """获取与指定好友的聊天记录"""
    try:
        # 使用数据库服务获取消息
        messages, total_count, has_more = MessageDBService.get_messages_with_friend(
            user_id=user_id,
            friend_id=friend_id,
            limit=limit,
            offset=offset,
            search=search
        )
        
        return {
            "messages": messages,
            "total_count": total_count,
            "has_more": has_more,
            "current_offset": offset,
            "limit": limit
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取消息失败: {str(e)}")

@router.get("/local-storage/messages/{friend_id}")
def get_messages_with_friend(
    friend_id: int, 
    limit: int = 50,
    offset: int = 0,
    search: str = None,
    current_user: UserOut = Depends(get_current_user)
):
    """获取与指定好友的聊天记录，支持分页和搜索"""
    try:
        user_id = int(current_user.id)
        
        # 使用数据库服务获取消息
        messages, total_count, has_more = MessageDBService.get_messages_with_friend(
            user_id=user_id,
            friend_id=friend_id,
            limit=limit,
            offset=offset,
            search=search
        )
        
        # 获取数据库文件路径
        db_path = MessageDBService.get_user_db_path(user_id)
        
        return {
            "success": True,
            "messages": messages,
            "count": len(messages),
            "total_count": total_count,
            "offset": offset,
            "limit": limit,
            "has_more": has_more,
            "storage_location": db_path
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取消息失败: {str(e)}")

@router.get("/local-storage/status")
async def get_storage_status(
    user_id: int = Query(..., description="用户ID")
):
    """获取本地存储状态"""
    try:
        # 获取数据库状态
        db_status = MessageDBService.get_database_status(user_id)
        
        # 检查是否还有JSON文件需要迁移
        json_file_path = get_user_messages_file(user_id)
        has_json_backup = os.path.exists(json_file_path)
        
        return {
            "database": db_status,
            "has_json_backup": has_json_backup,
            "json_file_path": json_file_path if has_json_backup else None
        }
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取存储状态失败: {str(e)}")

@router.post("/local-storage/messages/{message_id}/read")
async def mark_message_read(
    message_id: str,
    user_id: int = Query(..., description="用户ID")
):
    """标记消息为已读"""
    try:
        success = MessageDBService.mark_message_as_read(user_id, message_id)
        if success:
            return {"status": "success", "message": "消息已标记为已读"}
        else:
            raise HTTPException(status_code=404, detail="消息未找到")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"标记消息已读失败: {str(e)}")

@router.delete("/local-storage/messages/{message_id}")
async def delete_message(
    message_id: str,
    user_id: int = Query(..., description="用户ID")
):
    """删除消息"""
    try:
        success = MessageDBService.delete_message(user_id, message_id)
        if success:
            return {"status": "success", "message": "消息已删除"}
        else:
            raise HTTPException(status_code=404, detail="消息未找到")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"删除消息失败: {str(e)}")

@router.post("/local-storage/migrate")
async def migrate_from_json(
    user_id: int = Query(..., description="用户ID")
):
    """从JSON文件迁移数据到数据库"""
    try:
        success = MessageDBService.migrate_from_json(user_id)
        if success:
            return {"status": "success", "message": "数据迁移完成"}
        else:
            raise HTTPException(status_code=500, detail="数据迁移失败")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"数据迁移失败: {str(e)}")

@router.delete("/local-storage/messages")
async def clear_all_messages(
    user_id: int = Query(..., description="用户ID")
):
    """清空用户的所有消息"""
    try:
        success = MessageDBService.clear_all_messages(user_id)
        if success:
            return {"status": "success", "message": "所有消息已清空"}
        else:
            raise HTTPException(status_code=500, detail="清空消息失败")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"清空消息失败: {str(e)}")

# 旧的清空消息函数已被新的数据库版本替代