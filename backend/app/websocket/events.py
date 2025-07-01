from fastapi import WebSocket, WebSocketDisconnect
from .manager import ConnectionManager
from db.database import SessionLocal
from db import models
import json

manager = ConnectionManager()

async def websocket_endpoint(websocket: WebSocket, user_id: int):
    await websocket.accept()
    manager.connect(user_id, websocket)
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
        await notify_friends_status(user_id, False)

async def handle_private_message(from_id, msg):
    to_id = msg.get("to_id")
    content = msg.get("content")
    print(f"[WS] 收到私聊消息 from: {from_id}, to: {to_id}, content: {content}")
    ws = manager.get(to_id)
    if ws:
        print(f"[WS] 推送消息给用户 {to_id}")
        await ws.send_text(json.dumps({
            "type": "message",
            "data": {
                "from": from_id,
                "to": to_id,
                "content": content,
                "timestamp": None,  # 可补充真实时间
                "encrypted": msg.get("encrypted", True),
                "method": msg.get("method", "Server"),
                "destroy_after": msg.get("destroy_after")
            }
        }))
    else:
        print(f"[WS] 用户 {to_id} 不在线，无法推送")

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