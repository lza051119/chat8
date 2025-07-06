from fastapi import WebSocket
from fastapi.websockets import WebSocketDisconnect
from .manager import ConnectionManager
from app.db.database import SessionLocal
from app.db import models
from app.core.security import decode_access_token
from datetime import datetime
import json
import asyncio
import time
from sqlalchemy.orm import Session
from app.services.user_states_update import get_user_states_service



async def websocket_endpoint(websocket: WebSocket, user_id: int, manager: ConnectionManager):
    await websocket.accept()
    manager.connect(user_id, websocket)
    
    # 用户登录状态处理
    try:
        user_states_service = get_user_states_service()
        login_result = await user_states_service.user_login(user_id)
        if login_result["success"]:
            print(f"[WebSocket] 用户 {user_id} 登录状态处理成功")
        else:
            print(f"[WebSocket] 用户 {user_id} 登录状态处理失败: {login_result['message']}")
    except Exception as e:
        print(f"[WebSocket] 用户 {user_id} 登录状态处理异常: {str(e)}")
    
    # 发送离线消息
    await send_offline_messages(user_id, websocket)
    
    try:
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)
            
            # 根据消息类型处理
            if message.get('type') == 'private_message':
                await handle_private_message(user_id, message, manager)
            elif message.get('type') == 'typing_start':
                await handle_typing_status(message, user_id, manager, True)
            elif message.get('type') == 'typing_stop':
                await handle_typing_status(message, user_id, manager, False)
            elif message.get('type') == 'screenshot_reminder':
                await handle_screenshot_reminder(message, user_id, manager)
            elif message.get('type') in ['webrtc_offer', 'webrtc_answer', 'webrtc_ice_candidate']:
                await handle_webrtc_signaling(message, user_id, manager)
            elif message.get('type') in ['voice_call_offer', 'voice_call_answer', 'voice_call_ice_candidate', 'voice_call_rejected', 'voice_call_ended']:
                await handle_voice_call_signaling(message, user_id, manager)
            elif message.get('type') in ['video_call_offer', 'video_call_answer', 'video_call_ice_candidate', 'video_call_rejected', 'video_call_ended', 'video_call_toggle']:
                await handle_video_call_signaling(message, user_id, manager)
            elif message.get('type') == 'heartbeat':
                # 更新用户心跳时间
                try:
                    user_states_service = get_user_states_service()
                    await user_states_service.update_user_heartbeat(user_id)
                except Exception as e:
                    print(f"[WebSocket] 更新用户 {user_id} 心跳失败: {str(e)}")
                
                await websocket.send_text(json.dumps({
                    'type': 'heartbeat_response',
                    'timestamp': int(time.time() * 1000)
                }))
            elif message.get('type') == 'heartbeat_response':
                # 心跳回复处理
                try:
                    user_states_service = get_user_states_service()
                    await user_states_service.update_user_heartbeat(user_id)
                except Exception as e:
                    print(f"[WebSocket] 更新用户 {user_id} 心跳失败: {str(e)}")
                
    except WebSocketDisconnect:
        manager.disconnect(user_id)
        
        # 用户离线状态处理
        try:
            user_states_service = get_user_states_service()
            logout_result = await user_states_service.user_logout(user_id)
            if logout_result["success"]:
                print(f"[WebSocket] 用户 {user_id} 离线状态处理成功")
            else:
                print(f"[WebSocket] 用户 {user_id} 离线状态处理失败: {logout_result['message']}")
        except Exception as e:
            print(f"[WebSocket] 用户 {user_id} 离线状态处理异常: {str(e)}")

async def handle_private_message(from_id, msg, manager: ConnectionManager):
    to_id = msg.get("to_id")
    encrypted_content = msg.get("encrypted_content")
    message_type = msg.get("message_type", "text")
    
    # 检查接收方是否在线
    recipient_online = manager.get(to_id) is not None
    
    # 保存消息到数据库（只有接收方不在线时才保存）
    db = SessionLocal()
    try:
        from app.services import message_service
        saved_msg = message_service.send_message(
            db,
            from_id=from_id,
            to_id=to_id,
            encrypted_content=encrypted_content,
            message_type=message_type,
            recipient_online=recipient_online
        )
        
        # 构建推送消息数据 - 直接转发不透明的加密数据
        message_data = {
            "id": saved_msg.id if saved_msg else f"{from_id}_{to_id}_{int(datetime.now().timestamp())}",
            "from": from_id,
            "to": to_id,
            "encrypted_content": encrypted_content,
            "messageType": message_type,
            "timestamp": saved_msg.timestamp.isoformat() if saved_msg else datetime.utcnow().isoformat(),
            "delivered": saved_msg.delivered if saved_msg else True
        }
        

        
        # 尝试推送给在线用户
        ws = manager.get(to_id)
        if ws:
            # 推送消息给用户
            await ws.send_text(json.dumps({
                "type": "message",
                "data": message_data
            }))
            
            # 消息发送成功，如果之前保存到了服务器数据库，现在删除它
            if saved_msg:
                message_service.delete_server_message(db, saved_msg.id)
        else:
            # 用户不在线，消息已暂存到服务器数据库
            pass
    finally:
        db.close()





# update_user_status函数已删除 - 用户状态只在登录时设置为online

async def send_offline_messages(user_id: int, websocket: WebSocket):
    """发送用户离线期间收到的消息"""
    db = SessionLocal()
    try:
        from app.services import message_service
        # 获取用户的离线消息
        offline_messages = message_service.get_offline_messages(db, user_id)
        
        if offline_messages:
            sent_message_ids = []
            
            for msg in offline_messages:
                message_data = {
                    "id": msg.id,
                    "from": msg.from_id,
                    "to": msg.to_id,
                    "encrypted_content": msg.encrypted_content,
                    "messageType": msg.message_type,
                    "timestamp": msg.timestamp.isoformat(),
                    "delivered": msg.delivered
                }
                
                try:
                    await websocket.send_text(json.dumps({
                        "type": "message",
                        "data": message_data
                    }))
                    
                    # 消息发送成功，记录ID用于后续删除
                    sent_message_ids.append(msg.id)
                        
                except Exception as e:
                    # 发送离线消息失败
                    pass
            
            # 删除已成功发送的离线消息
            for msg_id in sent_message_ids:
                message_service.delete_server_message(db, msg_id)
    except Exception as e:
        # 发送离线消息失败
        pass
    finally:
        db.close()

async def handle_typing(from_id, msg, is_start, manager: ConnectionManager):
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

async def handle_screenshot_alert(from_id, msg, manager: ConnectionManager):
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

async def handle_webrtc_signaling(msg, from_id, manager: ConnectionManager):
    to_id = msg.get("to_id")
    ws = manager.get(to_id)
    if ws:
        # 构建转发给目标客户端的消息，使用前端期望的格式
        forward_msg = {
            "type": msg["type"],
            "from_id": from_id,
            "payload": msg.get("payload")
        }
        
        print(f"[WebRTC] 转发信令 {msg['type']} 从用户 {from_id} 到用户 {to_id}")
        await ws.send_text(json.dumps(forward_msg))
    else:
        print(f"[WebRTC] 目标用户 {to_id} 不在线，无法转发信令 {msg['type']}")

async def handle_voice_call_signaling(msg, from_id, manager: ConnectionManager):
    """处理语音通话信令消息"""
    to_id = msg.get("to_id")
    ws = manager.get(to_id)
    if ws:
        # 构建转发给目标客户端的消息，保持与前端期望的格式一致
        forward_msg = {
            "type": msg["type"],
            "from_id": from_id,
            "to_id": to_id
        }
        
        # 根据消息类型添加相应的数据
        if msg["type"] == "voice_call_offer":
            forward_msg["call_id"] = msg.get("call_id")
            forward_msg["payload"] = msg.get("payload")
            forward_msg["offer"] = msg.get("payload")  # 兼容性字段
            forward_msg["fromUserId"] = from_id
            forward_msg["toUserId"] = to_id
        elif msg["type"] == "voice_call_answer":
            forward_msg["payload"] = msg.get("payload")
            forward_msg["answer"] = msg.get("payload")  # 兼容性字段
        elif msg["type"] == "voice_call_ice_candidate":
            forward_msg["payload"] = msg.get("payload")
            forward_msg["candidate"] = msg.get("payload")  # 兼容性字段
        elif msg["type"] in ["voice_call_rejected", "voice_call_ended"]:
            forward_msg["reason"] = msg.get("reason", "")
            forward_msg["payload"] = msg.get("payload")
        
        print(f"[语音通话] 转发信令 {msg['type']} 从用户 {from_id} 到用户 {to_id}")
        print(f"[语音通话] 转发消息内容: {forward_msg}")
        await ws.send_text(json.dumps(forward_msg))
    else:
        print(f"[语音通话] 目标用户 {to_id} 不在线，无法转发信令 {msg['type']}")

async def handle_video_call_signaling(msg, from_id, manager: ConnectionManager):
    """处理视频通话信令消息"""
    to_id = msg.get("to_id")
    ws = manager.get(to_id)
    if ws:
        # 构建转发给目标客户端的消息，保持与前端期望的格式一致
        forward_msg = {
            "type": msg["type"],
            "from_id": from_id,
            "to_id": to_id
        }
        
        # 根据消息类型添加相应的数据
        if msg["type"] == "video_call_offer":
            forward_msg["call_id"] = msg.get("call_id")
            forward_msg["payload"] = msg.get("payload")
            forward_msg["offer"] = msg.get("payload")  # 兼容性字段
            forward_msg["fromUserId"] = from_id
            forward_msg["toUserId"] = to_id
        elif msg["type"] == "video_call_answer":
            forward_msg["payload"] = msg.get("payload")
            forward_msg["answer"] = msg.get("payload")  # 兼容性字段
        elif msg["type"] == "video_call_ice_candidate":
            forward_msg["payload"] = msg.get("payload")
            forward_msg["candidate"] = msg.get("payload")  # 兼容性字段
        elif msg["type"] in ["video_call_rejected", "video_call_ended"]:
            forward_msg["reason"] = msg.get("reason", "")
            forward_msg["payload"] = msg.get("payload")
        elif msg["type"] == "video_call_toggle":
            forward_msg["payload"] = msg.get("payload")
        
        print(f"[视频通话] 转发信令 {msg['type']} 从用户 {from_id} 到用户 {to_id}")
        print(f"[视频通话] 转发消息内容: {forward_msg}")
        await ws.send_text(json.dumps(forward_msg))
    else:
        print(f"[视频通话] 目标用户 {to_id} 不在线，无法转发信令 {msg['type']}")

# 状态管理服务已删除