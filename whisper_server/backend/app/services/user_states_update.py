from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from ..websocket.manager import ConnectionManager
from ..repositories.user_repository import user_repository
from ..repositories.friend_repository import friend_repository
from ..db.database import get_db
from ..db.models import User
from datetime import datetime, timedelta
import json
import asyncio
import logging

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class UserPresenceService:
    """用户状态更新服务"""
    
    def __init__(self, connection_manager: ConnectionManager):
        self.connection_manager = connection_manager
        self.heartbeat_interval = 180  # 心跳检测间隔（秒）
        self.heartbeat_timeout = 120  # 心跳超时时间（秒）
        self.user_last_heartbeat = {}  # 用户最后心跳时间记录
        self.heartbeat_task = None
        
    async def user_login(self, db: AsyncSession, user_id: int):
        """用户登录处理"""
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
        """用户退出处理"""
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
        """更新用户心跳时间"""
        user = await user_repository.get(db, user_id)
        if not user:
            return {"success": False, "message": "用户不存在"}
        
        current_time = datetime.utcnow()
        self.user_last_heartbeat[user_id] = current_time
        
        user.status = 'online'
        user.last_seen = current_time
        await db.commit()
        
        logger.debug(f"[心跳] 用户 {user.username}({user_id}) 心跳时间和数据库状态已更新")
        return {"success": True, "message": "心跳更新成功"}
    
    async def check_heartbeat_timeouts(self, db: AsyncSession) -> dict:
        """检查心跳超时的用户"""
        current_time = datetime.utcnow()
        timeout_threshold = current_time - timedelta(seconds=self.heartbeat_timeout)
        
        # 获取所有标记为在线的用户
        stmt = select(User).where(User.status == 'online')
        result = await db.execute(stmt)
        online_users = result.scalars().all()
        
        timeout_users_ids = []
        
        for user in online_users:
            user_id = user.id
            has_connection = self.connection_manager.is_user_connected(user_id)
            last_heartbeat = self.user_last_heartbeat.get(user_id)
            heartbeat_timeout = (last_heartbeat is None or last_heartbeat < timeout_threshold)
            
            if not has_connection or heartbeat_timeout:
                timeout_users_ids.append(user_id)
                logger.info(f"[心跳检测] 用户 {user.username}({user_id}) 心跳超时或连接断开")
        
        # 处理超时用户
        processed_count = 0
        if timeout_users_ids:
            for user_id in timeout_users_ids:
                await self.user_logout(db, user_id)
            processed_count = len(timeout_users_ids)
        
        logger.info(f"[心跳检测] 检查了 {len(online_users)} 个在线用户，处理了 {processed_count} 个超时用户")
        
        return {
            "success": True,
            "message": "心跳检测完成",
            "checked_users": len(online_users),
            "timeout_users": len(timeout_users_ids),
            "processed_users": processed_count
        }
    
    async def start_heartbeat_monitor(self):
        """启动心跳监控任务"""
        if self.heartbeat_task and not self.heartbeat_task.done():
            logger.warning("[心跳监控] 心跳监控任务已在运行")
            return
            
        logger.info(f"[心跳监控] 启动心跳监控，检测间隔: {self.heartbeat_interval}秒")
        self.heartbeat_task = asyncio.create_task(self._heartbeat_monitor_loop())
    
    async def stop_heartbeat_monitor(self):
        """停止心跳监控任务"""
        if self.heartbeat_task:
            self.heartbeat_task.cancel()
            try:
                await self.heartbeat_task
            except asyncio.CancelledError:
                pass
            self.heartbeat_task = None
            logger.info("[心跳监控] 心跳监控任务已停止")
    
    async def _heartbeat_monitor_loop(self):
        """心跳监控循环"""
        while True:
            await asyncio.sleep(self.heartbeat_interval)
            try:
                async for db in get_db():
                    await self.check_heartbeat_timeouts(db)
            except Exception as e:
                logger.error(f"[心跳监控] 心跳监控循环异常: {e}")

    async def _send_to_user(self, user_id: int, message: str):
        """向指定用户发送消息"""
        try:
            websocket = self.connection_manager.get_connection(user_id)
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
        return len(self.connection_manager.get_online_user_ids())
    
    def get_heartbeat_users_count(self) -> int:
        """获取有心跳记录的用户数量"""
        return len(self.user_last_heartbeat)
    
    async def get_user_status(self, db: AsyncSession, user_id: int) -> dict:
        """获取用户状态信息"""
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
_user_presence_service_instance = None

def get_user_presence_service() -> UserPresenceService:
    if _user_presence_service_instance is None:
        raise RuntimeError("UserPresenceService尚未初始化")
    return _user_presence_service_instance

def initialize_user_presence_service(connection_manager: ConnectionManager) -> UserPresenceService:
    global _user_presence_service_instance
    if _user_presence_service_instance is None:
        _user_presence_service_instance = UserPresenceService(connection_manager)
    return _user_presence_service_instance

async def cleanup_user_presence_service():
    if _user_presence_service_instance:
        await _user_presence_service_instance.stop_heartbeat_monitor()
        logger.info("用户状态服务已成功清理")

async def notify_user_of_friend_status_change(db: AsyncSession, user_id: int, friend_id: int, status: str):
    """通知用户好友状态变更"""
    # 待实现
    pass

async def user_offline(db: AsyncSession, user_id: int):
    """处理用户强制下线或超时"""
    # 待实现
    pass