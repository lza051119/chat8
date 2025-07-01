from fastapi import WebSocket
from fastapi.websockets import WebSocketDisconnect
from .manager import ConnectionManager
from db.database import SessionLocal
from db import models
from core.security import decode_access_token
from datetime import datetime
import json

manager = ConnectionManager()

async def websocket_endpoint(websocket: WebSocket, user_id: int):
    await websocket.accept()
    manager.connect(user_id, websocket)
    
    # 更新用户上线状态
    await update_user_status(user_id, True)
    
    # 发送离线消息
    await send_offline_messages(user_id, websocket)
    
    # 通知好友上线
    await notify_friends_status(user_id, True)
    try:
        while True:
            data = await websocket.receive_text()
            msg = json.loads(data)
            if msg.get("type") == "private_message":
                await handle_private_message(user_id, msg)
            elif msg.get("type") == "typing_start":
                await handle_typing(user_id, msg, True)
            elif msg.get("type") == "typing_stop":
                await handle_typing(user_id, msg, False)
            elif msg.get("type") == "screenshot_alert":
                await handle_screenshot_alert(user_id, msg)
            elif msg.get("type") in ["webrtc_offer", "webrtc_answer", "webrtc_ice_candidate"]:
                await handle_webrtc_signaling(user_id, msg)
    except WebSocketDisconnect:
        manager.disconnect(user_id)
        # 更新用户离线状态
        await update_user_status(user_id, False)
        await notify_friends_status(user_id, False)

async def handle_private_message(from_id, msg):
    to_id = msg.get("to_id")
    content = msg.get("content")
    print(f"[WS] 收到私聊消息 from: {from_id}, to: {to_id}, content: {content}")
    
    # 保存消息到数据库
    db = SessionLocal()
    try:
        from services import message_service
        saved_msg = message_service.send_message(
            db,
            from_id=from_id,
            to_id=to_id,
            content=content,
            encrypted=msg.get("encrypted", True),
            method=msg.get("method", "Server"),
            destroy_after=msg.get("destroy_after")
        )
        
        # 尝试推送给在线用户
        ws = manager.get(to_id)
        if ws:
            print(f"[WS] 推送消息给用户 {to_id}")
            await ws.send_text(json.dumps({
                "type": "message",
                "data": {
                    "id": saved_msg.id,
                    "from": from_id,
                    "to": to_id,
                    "content": content,
                    "timestamp": saved_msg.timestamp.isoformat(),
                    "encrypted": msg.get("encrypted", True),
                    "method": msg.get("method", "Server"),
                    "destroy_after": msg.get("destroy_after")
                }
            }))
        else:
            print(f"[WS] 用户 {to_id} 不在线，消息已存储到数据库")
    finally:
        db.close()

async def update_user_status(user_id: int, is_online: bool):
    """更新用户在线状态和最后在线时间"""
    db = SessionLocal()
    try:
        user = db.query(models.User).filter(models.User.id == user_id).first()
        if user:
            user.status = 'online' if is_online else 'offline'
            user.last_seen = datetime.utcnow()
            db.commit()
    except Exception as e:
        print(f"更新用户状态失败: {e}")
    finally:
        db.close()

async def send_offline_messages(user_id: int, websocket: WebSocket):
    """发送用户离线期间收到的消息"""
    db = SessionLocal()
    try:
        # 获取用户最后一次在线时间
        user = db.query(models.User).filter(models.User.id == user_id).first()
        if not user:
            return
            
        last_seen = user.last_seen
        
        # 获取用户离线期间收到的消息
        offline_messages = db.query(models.Message).filter(
            models.Message.to_id == user_id,
            models.Message.timestamp > last_seen
        ).order_by(models.Message.timestamp.asc()).all()
        
        for msg in offline_messages:
            await websocket.send_text(json.dumps({
                "type": "message",
                "data": {
                    "id": msg.id,
                    "from": msg.from_id,
                    "to": msg.to_id,
                    "content": msg.content,
                    "timestamp": msg.timestamp.isoformat(),
                    "encrypted": msg.encrypted,
                    "method": msg.method,
                    "destroy_after": msg.destroy_after,
                    "offline": True  # 标记为离线消息
                }
            }))
            
        print(f"[WS] 已发送 {len(offline_messages)} 条离线消息给用户 {user_id}")
    except Exception as e:
        print(f"发送离线消息失败: {e}")
    finally:
        db.close()

async def handle_typing(from_id, msg, is_start):
    to_id = msg.get("to_id")
    ws = manager.get(to_id)
    if ws:
        await ws.send_text(json.dumps({
            "type": "typing",
            "data": {
                "from": from_id,
                "to": to_id,
                "isTyping": is_start
            }
        }))

async def handle_screenshot_alert(from_id, msg):
    to_id = msg.get("to_id")
    ws = manager.get(to_id)
    if ws:
        await ws.send_text(json.dumps({
            "type": "screenshot_alert",
            "data": {
                "from": from_id,
                "to": to_id
            }
        }))

async def handle_webrtc_signaling(from_id, msg):
    to_id = msg.get("to_id")
    ws = manager.get(to_id)
    if ws:
        await ws.send_text(json.dumps({
            "type": msg["type"],
            "data": {
                "from": from_id,
                "to": to_id,
                "payload": msg.get("payload")
            }
        }))

async def notify_friends_status(user_id, is_online):
    db = SessionLocal()
    try:
        friends = db.query(models.Friend).filter(models.Friend.user_id == user_id).all()
        for f in friends:
            ws = manager.get(f.friend_id)
            if ws:
                await ws.send_text(json.dumps({
                    "type": "presence",
                    "data": {
                        "userId": user_id,
                        "isOnline": is_online
                    }
                }))
    finally:
        db.close()