from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from ...deps import get_db
from ....services.message_service import message_service
from ....schemas import message as message_schema
from ....schemas.user import UserOut
from ....core.security import get_current_user
from ....websocket.manager import manager as websocket_manager
import json

router = APIRouter()

@router.post("/messages", response_model=message_schema.Message)
async def send_message(
    message_in: message_schema.MessageCreate,
    db: AsyncSession = Depends(get_db),
    current_user: UserOut = Depends(get_current_user),
):
    """
    发送一条新消息。
    """
    message = await message_service.create_message(db, message_in=message_in, from_user_id=current_user.id)
    
    # 通过WebSocket实时推送消息
    await websocket_manager.send_personal_message(
        json.dumps({"event": "new_message", "data": message_schema.Message.from_orm(message).model_dump()}),
        message.to_user_id
    )
    
    return message

@router.get("/messages/history/{friend_id}", response_model=list[message_schema.Message])
async def get_message_history(
    friend_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
    current_user: UserOut = Depends(get_current_user),
):
    """
    获取与指定好友的聊天记录。
    """
    history = await message_service.get_message_history(
        db, user_id=int(current_user.id), friend_id=friend_id, skip=skip, limit=limit
    )
    return history

@router.delete("/messages/{message_id}")
async def delete_message(message_id: int, current_user: UserOut = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    ok, err = await message_service.delete_message(db, int(current_user.id), message_id)
    if not ok:
        raise HTTPException(status_code=403 if err=="无权限删除该消息" else 404, detail=err)
    return {"success": True, "message": "消息删除成功"}