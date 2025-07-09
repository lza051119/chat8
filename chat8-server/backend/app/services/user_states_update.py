from sqlalchemy.ext.asyncio import AsyncSession
from app.websocket.manager import ConnectionManager
from app.repositories.user_repository import user_repository
from app.repositories.friend_repository import friend_repository
from datetime import datetime, timedelta
import json
import asyncio
import logging

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class UserPresenceService:
    """用户状态更新服务
    
    负责管理用户的在线/离线状态，包括：
    1. 用户登录时的状态更新和好友通知
    2. 用户退出时的状态更新和好友通知
    3. 定期心跳检测和离线用户处理
    """
    
    def __init__(self, connection_manager: ConnectionManager):
        self.connection_manager = connection_manager
        self.heartbeat_interval = 180  # 心跳检测间隔（秒）
        self.heartbeat_timeout = 120  # 心跳超时时间（秒）
        self.user_last_heartbeat = {}  # 用户最后心跳时间记录
        self.heartbeat_task = None
        
    async def user_login(self, db: AsyncSession, user_id: int):
        """用户登录处理
        
        1. 更新用户状态为online
        2. 获取用户的在线好友列表
        3. 向用户发送在线好友信息
        4. 向所有好友广播用户上线消息
        
        Args:
            db: 数据库会话
            user_id: 用户ID
            
        Returns:
            dict: 包含操作结果和在线好友列表
        """
        user = await user_repository.get(db, user_id)
        if not user:
            return
        
        user.status = 'online'
        user.last_seen = datetime.utcnow()
        await db.commit()
        
        self.user_last_heartbeat[user_id] = datetime.utcnow()
        logger.info(f"用户 {user.username} 状态更新为 online。")
        # TODO: Add logic to notify friends

    async def user_logout(self, db: AsyncSession, user_id: int):
        """用户退出处理
        
        1. 更新用户状态为offline
        2. 向所有在线好友广播用户离线消息
        
        Args:
            db: 数据库会话
            user_id: 用户ID
            
        Returns:
            dict: 包含操作结果
        """
        user = await user_repository.get(db, user_id)
        if not user:
            return

        user.status = 'offline'
        user.last_seen = datetime.utcnow()
        await db.commit()

        if user_id in self.user_last_heartbeat:
            del self.user_last_heartbeat[user_id]
        
        logger.info(f"用户 {user.username} 状态更新为 offline。")
        # TODO: Add logic to notify friends

    def is_user_online(self, user_id: int) -> bool:
        """检查用户是否在线"""
        return self.connection_manager.is_user_connected(user_id)
    
    async def update_user_heartbeat(self, db: AsyncSession, user_id: int) -> dict:
        """更新用户心跳时间
        
        Args:
            db: 数据库会话
            user_id: 用户ID
            
        Returns:
            dict: 包含操作结果
        """
        user = await user_repository.get(db, user_id)
        if not user:
            return {"success": False, "message": "用户不存在"}
        
        # 更新内存中的心跳时间
        current_time = datetime.utcnow()
        self.user_last_heartbeat[user_id] = current_time
        
        # 更新数据库中的用户状态
        user.status = 'online'
        user.last_seen = current_time
        await db.commit()
        
        logger.debug(f"[心跳] 用户 {user.username}({user_id}) 心跳时间和数据库状态已更新")
        return {"success": True, "message": "心跳更新成功"}
    
    async def check_heartbeat_timeouts(self, db: AsyncSession) -> dict:
        """检查心跳超时的用户
        
        检查所有在线用户的心跳状态，将超时的用户设置为离线
        
        Returns:
            dict: 包含检查结果
        """
        current_time = datetime.utcnow()
        timeout_threshold = current_time - timedelta(seconds=self.heartbeat_timeout)
        
        # 获取所有标记为在线的用户
        online_users = await user_repository.get_online_users(db)
        
        timeout_users = []
        
        for user in online_users:
            user_id = user.id
            
            # 检查用户是否还有WebSocket连接
            has_connection = self.connection_manager.is_user_connected(user_id)
            
            # 检查心跳时间
            last_heartbeat = self.user_last_heartbeat.get(user_id)
            heartbeat_timeout = (last_heartbeat is None or 
                               last_heartbeat < timeout_threshold)
            
            # 如果没有连接或心跳超时，则认为用户离线
            if not has_connection or heartbeat_timeout:
                timeout_users.append(user)
                logger.info(f"[心跳检测] 用户 {user.username}({user_id}) 心跳超时或连接断开")
        
        # 处理超时用户
        processed_count = 0
        for user in timeout_users:
            result = await self.user_logout(None, user.id)
            if result["success"]:
                processed_count += 1
        
        logger.info(f"[心跳检测] 检查了 {len(online_users)} 个在线用户，处理了 {processed_count} 个超时用户")
        
        return {
            "success": True,
            "message": "心跳检测完成",
            "checked_users": len(online_users),
            "timeout_users": len(timeout_users),
            "processed_users": processed_count
        }
    
    async def start_heartbeat_monitor(self):
        """启动心跳监控任务"""
        if self.heartbeat_task is not None:
            logger.warning("[心跳监控] 心跳监控任务已在运行")
            return
            
        logger.info(f"[心跳监控] 启动心跳监控，检测间隔: {self.heartbeat_interval}秒")
        self.heartbeat_task = asyncio.create_task(self._heartbeat_monitor_loop())
    
    async def stop_heartbeat_monitor(self):
        """停止心跳监控任务"""
        if self.heartbeat_task is not None:
            self.heartbeat_task.cancel()
            try:
                await self.heartbeat_task
            except asyncio.CancelledError:
                pass
            self.heartbeat_task = None
            logger.info("[心跳监控] 心跳监控任务已停止")
    
    async def _heartbeat_monitor_loop(self):
        """心跳监控循环"""
        try:
            while True:
                await asyncio.sleep(self.heartbeat_interval)
                await self.check_heartbeat_timeouts(None)
        except asyncio.CancelledError:
            logger.info("[心跳监控] 心跳监控循环已取消")
            raise
        except Exception as e:
            logger.error(f"[心跳监控] 心跳监控循环异常: {str(e)}")
    
    async def _send_to_user(self, user_id: int, message: str):
        """向指定用户发送消息
        
        Args:
            user_id: 用户ID
            message: 消息内容
        """
        try:
            websocket = self.connection_manager.get(user_id)
            if websocket:
                logger.debug(f"[消息发送] 准备向用户 {user_id} 发送消息: {message[:100]}...")
                await websocket.send_text(message)
                logger.debug(f"[消息发送] 成功向用户 {user_id} 发送消息")
            else:
                logger.debug(f"[消息发送] 用户 {user_id} 不在线，无法发送消息")
        except Exception as e:
            logger.error(f"[消息发送] 向用户 {user_id} 发送消息失败: {str(e)}")
    
    def get_online_users_count(self) -> int:
        """获取在线用户数量"""
        return len(self.connection_manager.get_online_users())
    
    def get_heartbeat_users_count(self) -> int:
        """获取有心跳记录的用户数量"""
        return len(self.user_last_heartbeat)
    
    async def get_user_status(self, db: AsyncSession, user_id: int) -> dict:
        """获取用户状态信息
        
        Args:
            db: 数据库会话
            user_id: 用户ID
            
        Returns:
            dict: 用户状态信息
        """
        user = await user_repository.get(db, user_id)
        if not user:
            return {"success": False, "message": "用户不存在"}
        
        has_connection = self.connection_manager.is_user_connected(user_id)
        last_heartbeat = self.user_last_heartbeat.get(user_id)
        
        return {
            "success": True,
            "data": {
                "userId": user_id,
                "username": user.username,
                "status": user.status,
                "lastSeen": user.last_seen.isoformat() if user.last_seen else None,
                "hasConnection": has_connection,
                "lastHeartbeat": last_heartbeat.isoformat() if last_heartbeat else None
            }
        }

# 全局服务实例
user_presence_service: UserPresenceService | None = None

def get_user_presence_service() -> UserPresenceService:
    """获取用户状态服务实例"""
    if user_presence_service is None:
        raise RuntimeError("用户状态服务未初始化")
    return user_presence_service

def initialize_user_presence_service(connection_manager: ConnectionManager) -> UserPresenceService:
    """初始化用户状态服务"""
    global user_presence_service
    user_presence_service = UserPresenceService(connection_manager)
    # user_presence_service.start_heartbeat_monitor() # 心跳监控暂时禁用
    return user_presence_service

async def cleanup_user_presence_service():
    """清理用户状态服务"""
    global user_presence_service
    if user_presence_service is not None:
        await user_presence_service.stop_heartbeat_monitor()
        user_presence_service = None

async def notify_user_of_friend_status_change(db: AsyncSession, user_id: int, friend_id: int, status: str):
    user = await user_repository.get(db, friend_id)
    if user:
        status_change_message = {
            "type": "user_status_change",
            "payload": {
                "userId": friend_id,
                "username": user.username,
                "status": status,
                "lastSeen": datetime.utcnow().isoformat() if status == "online" else user.last_seen.isoformat() if user.last_seen else None
            },
            "timestamp": datetime.utcnow().isoformat()
        }
        await manager.send_personal_message(status_change_message, user_id)
        logging.info(f"Notified user {user_id} about friend {friend_id}'s status change to {status}.")

async def user_offline(db: AsyncSession, user_id: int):
    """
    Handle user offline event.
    """
    logging.info(f"Processing user offline event for user_id: {user_id}")
    await update_user_status(db, user_id=user_id, status="offline")
    user = await user_repository.get(db, user_id)
    if user:
        user_offline_message = {
            "type": "user_status_change",
            "payload": {
                "userId": user_id,
                "username": user.username,
                "status": "offline",
                "lastSeen": user.last_seen.isoformat() if user.last_seen else datetime.utcnow().isoformat()
            },
            "timestamp": datetime.utcnow().isoformat()
        }
        await manager.broadcast_to_friends(user_id, user_offline_message)
        logging.info(f"User {user_id} is offline. Notified friends.")