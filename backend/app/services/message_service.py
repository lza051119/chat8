from sqlalchemy.orm import Session
from app.db import models
from datetime import datetime, timedelta
from typing import List
from app.services.message_db_service import MessageDBService
from app.services.encryption_service import encryption_service

def send_message(db: Session, from_id: int, to_id: int, content: str, encrypted: bool = True, method: str = 'E2E', destroy_after: int = None, message_type: str = 'text', file_path: str = None, file_name: str = None, hidding_message: str = None, recipient_online: bool = False):
    # 服务器数据库只作为临时暂存，只有在接收方不在线时才保存
    utc_now = datetime.utcnow()
    
    # 对于图片消息，确保内容不为空
    if message_type == 'image' and not content:
        content = f"发送了图片: {file_name or '未知文件'}"
    
    # 端到端加密处理
    encrypted_content = content
    if encrypted and method == 'E2E':
        try:
            encryption_result = encryption_service.encrypt_message(from_id, to_id, content)
            if encryption_result.get('success'):
                encrypted_content = encryption_result['encrypted_message']
            else:
                print(f"Warning: Failed to encrypt message: {encryption_result.get('error')}")
                # 如果加密失败，回退到明文传输
                encrypted = False
                method = 'Server'
        except Exception as e:
            print(f"Warning: Encryption error: {e}")
            encrypted = False
            method = 'Server'
    
    msg = None
    
    # 图片消息始终保存到服务器数据库（因为需要文件持久化存储）
    # 普通文本消息只有在接收方不在线时才保存
    if not recipient_online or message_type == 'image':
        msg = models.Message(
            from_id=from_id,
            to_id=to_id,
            content=encrypted_content,
            message_type=message_type,
            file_path=file_path,
            file_name=file_name,
            encrypted=encrypted,
            method=method,
            timestamp=utc_now,
            destroy_after=destroy_after,
            hidding_message=hidding_message
        )
        db.add(msg)
        db.commit()
        db.refresh(msg)
        
        if message_type == 'image':
            # 图片消息已保存到服务器数据库
            pass
        else:
            # 接收方不在线，消息已暂存到服务器数据库
            pass
    else:
        # 接收方在线，普通消息不保存到服务器数据库，直接转发
        pass
    
    # 始终保存到发送方的本地数据库
    try:
        message_data = {
            'id': str(msg.id) if msg else f"{from_id}_{to_id}_{int(utc_now.timestamp())}",
            'from': from_id,
            'to': to_id,
            'content': content,  # 本地存储明文
            'encrypted_content': encrypted_content if encrypted else None,  # 存储加密内容
            'message_type': message_type,
            'file_path': file_path if message_type == 'image' else None,
            'file_name': file_name if message_type == 'image' else None,
            'timestamp': utc_now.isoformat(),
            'method': method,
            'encrypted': encrypted
        }
        
        MessageDBService.add_message(
            user_id=from_id,
            message_data=message_data
        )
        # 消息已保存到发送方本地数据库
    except Exception as e:
        # 保存到发送方本地数据库失败
        pass
    
    return msg

def decrypt_message_content(user_id: int, from_id: int, encrypted_content: str) -> str:
    """解密消息内容"""
    try:
        decryption_result = encryption_service.decrypt_message(user_id, from_id, encrypted_content)
        if decryption_result.get('success'):
            return decryption_result['decrypted_message']
        else:
            print(f"Warning: Failed to decrypt message: {decryption_result.get('error')}")
            return "[解密失败的消息]"
    except Exception as e:
        print(f"Warning: Decryption error: {e}")
        return "[解密失败的消息]"

def delete_server_message(db: Session, message_id: int):
    """删除服务器数据库中的消息（消息发送成功后调用）"""
    try:
        msg = db.query(models.Message).filter(models.Message.id == message_id).first()
        if msg:
            db.delete(msg)
            db.commit()
            # 服务器数据库中的消息已删除
            return True
        else:
            # 要删除的消息不存在
            return False
    except Exception as e:
        # 删除服务器消息失败
        return False

def get_offline_messages(db: Session, user_id: int):
    """获取用户的离线消息"""
    try:
        # 获取发送给该用户的所有未读消息（服务器数据库中的消息都是离线消息）
        offline_messages = db.query(models.Message).filter(
            models.Message.to_id == user_id
        ).order_by(models.Message.timestamp.asc()).all()
        
        # 解密加密的消息
        for msg in offline_messages:
            if msg.encrypted and msg.method == 'E2E':
                try:
                    decrypted_content = decrypt_message_content(user_id, msg.from_id, msg.content)
                    msg.content = decrypted_content
                except Exception as e:
                    print(f"Warning: Failed to decrypt offline message {msg.id}: {e}")
        
        # 获取到离线消息
        return offline_messages
    except Exception as e:
        # 获取离线消息失败
        return []

def get_message_history(db: Session, user_id: int, peer_id: int, page: int = 1, limit: int = 50):
    now = datetime.utcnow()
    query = db.query(models.Message).filter(
        ((models.Message.from_id == user_id) & (models.Message.to_id == peer_id)) |
        ((models.Message.from_id == peer_id) & (models.Message.to_id == user_id))
    ).order_by(models.Message.timestamp.desc())
    # 阅后即焚：删除已过期消息
    expired_msgs = []
    for m in query:
        if m.destroy_after:
            expire_time = m.timestamp + timedelta(seconds=m.destroy_after)
            if now > expire_time:
                expired_msgs.append(m)
    for m in expired_msgs:
        db.delete(m)
    if expired_msgs:
        db.commit()
    # 重新查询未过期消息
    query = db.query(models.Message).filter(
        ((models.Message.from_id == user_id) & (models.Message.to_id == peer_id)) |
        ((models.Message.from_id == peer_id) & (models.Message.to_id == user_id))
    ).order_by(models.Message.timestamp.desc())
    total = query.count()
    messages = query.offset((page-1)*limit).limit(limit).all()
    
    # 转换消息格式以符合API规范
    formatted_messages = []
    for msg in messages:
        formatted_msg = {
            "id": str(msg.id),
            "from": str(msg.from_id),
            "to": str(msg.to_id),
            "content": msg.content,
            "messageType": msg.message_type or 'text',
            "timestamp": msg.timestamp.isoformat(),
            "encrypted": msg.encrypted,
            "method": msg.method
        }
        if msg.file_path:
            formatted_msg["filePath"] = msg.file_path
        if msg.file_name:
            formatted_msg["fileName"] = msg.file_name
        if msg.hidding_message:
            formatted_msg["hiddenMessage"] = msg.hidding_message
        if msg.destroy_after:
            formatted_msg["destroyAfter"] = msg.destroy_after
        formatted_messages.append(formatted_msg)
    
    return {
        "messages": formatted_messages,
        "pagination": {
            "page": page,
            "limit": limit,
            "total": total,
            "totalPages": (total + limit - 1) // limit
        }
    }

def delete_message(db: Session, user_id: int, message_id: int):
    msg = db.query(models.Message).filter(models.Message.id == message_id).first()
    if not msg:
        return False, "消息不存在"
    # 只有发送者或接收者可以删除
    if msg.from_id != user_id and msg.to_id != user_id:
        return False, "无权限删除该消息"
    db.delete(msg)
    db.commit()
    return True, None