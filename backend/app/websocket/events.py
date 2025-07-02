from fastapi import WebSocket
from fastapi.websockets import WebSocketDisconnect
from .manager import ConnectionManager
from db.database import SessionLocal
from db import models
from core.security import decode_access_token
from datetime import datetime
from services.unified_presence_service import unified_presence
import json
import asyncio
from sqlalchemy.orm import Session
from services.unified_presence_service import UnifiedPresenceService



async def websocket_endpoint(websocket: WebSocket, user_id: int, manager: ConnectionManager):
    await websocket.accept()
    manager.connect(user_id, websocket)
    
    # 使用统一状态管理服务处理用户连接
    await unified_presence.user_connected(user_id, websocket, manager)
    
    # 发送离线消息
    await send_offline_messages(user_id, websocket)
    
    try:
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)
            
            # 根据消息类型处理
            if message.get('type') == 'private_message':
                await handle_private_message(user_id, message, manager)
            elif message.get('type') == 'image_message':
                await handle_image_message(user_id, message, manager)
            elif message.get('type') == 'typing_start':
                await handle_typing_status(message, user_id, manager, True)
            elif message.get('type') == 'typing_stop':
                await handle_typing_status(message, user_id, manager, False)
            elif message.get('type') == 'screenshot_reminder':
                await handle_screenshot_reminder(message, user_id, manager)
            elif message.get('type') in ['webrtc_offer', 'webrtc_answer', 'webrtc_ice_candidate']:
                await handle_webrtc_signaling(message, user_id, manager)
                
    except WebSocketDisconnect:
        manager.disconnect(user_id)
        # 使用统一状态管理服务处理用户断开
        await unified_presence.user_disconnected(user_id, manager)

async def handle_private_message(from_id, msg, manager: ConnectionManager):
    to_id = msg.get("to_id")
    content = msg.get("content")
    message_type = msg.get("message_type", "text")
    print(f"[WS] 收到私聊消息 from: {from_id}, to: {to_id}, type: {message_type}, content: {content}")
    
    # 检查接收方是否在线
    recipient_online = manager.get(to_id) is not None
    print(f"[WS] 接收方 {to_id} 在线状态: {recipient_online}")
    
    # 保存消息到数据库（只有接收方不在线时才保存到服务器数据库）
    db = SessionLocal()
    try:
        from services import message_service
        saved_msg = message_service.send_message(
            db,
            from_id=from_id,
            to_id=to_id,
            content=content,
            message_type=message_type,
            file_path=msg.get("file_path"),
            file_name=msg.get("file_name"),
            encrypted=msg.get("encrypted", True),
            method=msg.get("method", "Server"),
            destroy_after=msg.get("destroy_after"),
            hidding_message=msg.get("hidding_message"),
            recipient_online=recipient_online
        )
        
        # 构建推送消息数据
        message_data = {
            "id": saved_msg.id if saved_msg else f"{from_id}_{to_id}_{int(datetime.now().timestamp())}",
            "from": from_id,
            "to": to_id,
            "content": content,
            "messageType": message_type,
            "timestamp": saved_msg.timestamp.isoformat() if saved_msg else datetime.utcnow().isoformat(),
            "encrypted": msg.get("encrypted", True),
            "method": msg.get("method", "Server")
        }
        
        # 添加可选字段
        if msg.get("file_path"):
            message_data["filePath"] = msg.get("file_path")
        if msg.get("file_name"):
            message_data["fileName"] = msg.get("file_name")
        if msg.get("destroy_after"):
            message_data["destroyAfter"] = msg.get("destroy_after")
        if msg.get("hidding_message"):
            message_data["hiddenMessage"] = msg.get("hidding_message")
        if msg.get("imageUrl"):
            message_data["imageUrl"] = msg.get("imageUrl")
        
        # 尝试推送给在线用户
        ws = manager.get(to_id)
        if ws:
            print(f"[WS] 推送消息给用户 {to_id}")
            await ws.send_text(json.dumps({
                "type": "message",
                "data": message_data
            }))
            
            # 消息发送成功，如果之前保存到了服务器数据库，现在删除它
            if saved_msg:
                message_service.delete_server_message(db, saved_msg.id)
                
            # 保存到接收方的本地数据库
            try:
                from services.message_db_service import MessageDBService
                MessageDBService.add_message(
                    user_id=to_id,
                    message_data=message_data
                )
                print(f"[WS] 消息已保存到接收方本地数据库: 接收者={to_id}")
            except Exception as e:
                print(f"[WS] 保存到接收方本地数据库失败: {str(e)}")
        else:
            print(f"[WS] 用户 {to_id} 不在线，消息已暂存到服务器数据库")
    finally:
        db.close()

async def handle_image_message(from_id, msg, manager: ConnectionManager):
    """专门处理图片消息的WebSocket传输"""
    to_id = msg.get("to_id")
    file_path = msg.get("file_path")
    file_name = msg.get("file_name")
    content = msg.get("content", f"发送了图片: {file_name}")
    
    print(f"[WS] 收到图片消息 from: {from_id}, to: {to_id}, file: {file_name}")
    
    # 验证必要字段
    if not file_path or not file_name:
        print(f"[WS] 图片消息缺少必要字段: file_path={file_path}, file_name={file_name}")
        return
    
    # 检查接收方是否在线
    recipient_online = manager.get(to_id) is not None
    print(f"[WS] 接收方 {to_id} 在线状态: {recipient_online}")
    
    # 保存消息到数据库（只有接收方不在线时才保存到服务器数据库）
    db = SessionLocal()
    try:
        from services import message_service
        saved_msg = message_service.send_message(
            db,
            from_id=from_id,
            to_id=to_id,
            content=content,
            message_type="image",
            file_path=file_path,
            file_name=file_name,
            encrypted=msg.get("encrypted", True),
            method=msg.get("method", "Server"),
            destroy_after=msg.get("destroy_after"),
            hidding_message=msg.get("hidding_message"),
            recipient_online=recipient_online
        )
        
        # 构建推送消息数据
        message_data = {
            "id": saved_msg.id if saved_msg else f"{from_id}_{to_id}_{int(datetime.now().timestamp())}",
            "from": from_id,
            "to": to_id,
            "content": content,
            "messageType": "image",
            "filePath": file_path,
            "fileName": file_name,
            "timestamp": saved_msg.timestamp.isoformat() if saved_msg else datetime.utcnow().isoformat(),
            "encrypted": msg.get("encrypted", True),
            "method": msg.get("method", "Server")
        }
        
        # 添加可选字段
        if msg.get("destroy_after"):
            message_data["destroyAfter"] = msg.get("destroy_after")
        if msg.get("hidding_message"):
            message_data["hiddenMessage"] = msg.get("hidding_message")
        
        # 尝试推送给在线用户
        ws = manager.get(to_id)
        if ws:
            print(f"[WS] 推送图片消息给用户 {to_id}")
            await ws.send_text(json.dumps({
                "type": "message",
                "data": message_data
            }))
            
            # 消息发送成功，如果之前保存到了服务器数据库，现在删除它
            if saved_msg:
                message_service.delete_server_message(db, saved_msg.id)
                
            # 保存到接收方的本地数据库
            try:
                from services.message_db_service import MessageDBService
                MessageDBService.add_message(
                    user_id=to_id,
                    message_data=message_data
                )
                print(f"[WS] 图片消息已保存到接收方本地数据库: 接收者={to_id}")
            except Exception as e:
                print(f"[WS] 保存图片消息到接收方本地数据库失败: {str(e)}")
        else:
            print(f"[WS] 用户 {to_id} 不在线，图片消息已暂存到服务器数据库")
            
    except Exception as e:
        print(f"[WS] 处理图片消息失败: {str(e)}")
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
        from services import message_service
        # 获取用户的离线消息
        offline_messages = message_service.get_offline_messages(db, user_id)
        
        if offline_messages:
            print(f"[WS] 发送 {len(offline_messages)} 条离线消息给用户 {user_id}")
            
            sent_message_ids = []
            
            for msg in offline_messages:
                message_data = {
                    "id": msg.id,
                    "from": msg.from_id,
                    "to": msg.to_id,
                    "content": msg.content,
                    "messageType": msg.message_type,
                    "timestamp": msg.timestamp.isoformat(),
                    "encrypted": msg.encrypted,
                    "method": msg.method
                }
                
                # 添加可选字段
                if msg.file_path:
                    message_data["filePath"] = msg.file_path
                if msg.file_name:
                    message_data["fileName"] = msg.file_name
                if msg.destroy_after:
                    message_data["destroyAfter"] = msg.destroy_after
                if msg.hidding_message:
                    message_data["hiddenMessage"] = msg.hidding_message
                
                try:
                    await websocket.send_text(json.dumps({
                        "type": "message",
                        "data": message_data
                    }))
                    
                    # 消息发送成功，记录ID用于后续删除
                    sent_message_ids.append(msg.id)
                    
                    # 保存到接收方的本地数据库
                    try:
                        from services.message_db_service import MessageDBService
                        MessageDBService.add_message(
                            user_id=user_id,
                            message_data=message_data
                        )
                        print(f"[WS] 离线消息已保存到接收方本地数据库: 消息ID={msg.id}")
                    except Exception as e:
                        print(f"[WS] 保存离线消息到本地数据库失败: {str(e)}")
                        
                except Exception as e:
                    print(f"[WS] 发送离线消息失败: 消息ID={msg.id}, 错误={str(e)}")
            
            # 删除已成功发送的离线消息
            for msg_id in sent_message_ids:
                message_service.delete_server_message(db, msg_id)
                
            print(f"[WS] 已删除 {len(sent_message_ids)} 条已发送的离线消息")
    except Exception as e:
        print(f"发送离线消息失败: {e}")
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

async def handle_webrtc_signaling(from_id, msg, manager: ConnectionManager):
    to_id = msg.get("to_id")
    ws = manager.get(to_id)
    if ws:
        # 构建转发给目标客户端的消息
        forward_msg = {
            "type": msg["type"],
            "data": {
                "from": from_id,
                # 根据消息类型设置正确的负载字段
            }
        }
        if msg["type"] == 'webrtc_offer':
            forward_msg['data']['offer'] = msg.get("payload")
        elif msg["type"] == 'webrtc_answer':
            forward_msg['data']['answer'] = msg.get("payload")
        elif msg["type"] == 'webrtc_ice_candidate':
            forward_msg['data']['candidate'] = msg.get("payload")
        
        await ws.send_text(json.dumps(forward_msg))

# 注意：notify_friends_status函数已被弃用
# 现在使用统一状态管理服务(unified_presence_service)中的_notify_friends_status_change方法
# 该方法提供了更一致和完整的状态通知功能