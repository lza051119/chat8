from sqlalchemy.orm import Session
from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey
from app.db.database import SessionLocal
from app.db.models import User, Friend
from app.websocket.manager import ConnectionManager
from datetime import datetime, timedelta
import json
import asyncio
from typing import List, Optional
import logging

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class UserStatesUpdateService:
    """用户状态更新服务
    
    负责管理用户的在线/离线状态，包括：
    1. 用户登录时的状态更新和好友通知
    2. 用户退出时的状态更新和好友通知
    3. 定期心跳检测和离线用户处理
    """
    
    def __init__(self, connection_manager: ConnectionManager):
        self.connection_manager = connection_manager
        self.heartbeat_interval = 15  # 心跳检测间隔（秒）
        self.heartbeat_timeout = 120  # 心跳超时时间（秒）
        self.user_last_heartbeat = {}  # 用户最后心跳时间记录
        self.heartbeat_task = None
        
    def get_db(self) -> Session:
        """获取数据库会话"""
        return SessionLocal()
        
    async def user_login(self, user_id: int) -> dict:
        """用户登录处理
        
        1. 更新用户状态为online
        2. 获取用户的在线好友列表
        3. 向用户发送在线好友信息
        4. 向所有好友广播用户上线消息
        
        Args:
            user_id: 用户ID
            
        Returns:
            dict: 包含操作结果和在线好友列表
        """
        db = self.get_db()
        try:
            # 1. 更新用户状态为online
            user = db.query(User).filter(User.id == user_id).first()
            if not user:
                return {"success": False, "message": "用户不存在"}
                
            user.status = 'online'
            user.last_seen = datetime.utcnow()
            db.commit()
            
            # 记录用户心跳时间
            self.user_last_heartbeat[user_id] = datetime.utcnow()
            
            logger.info(f"[状态更新] 用户 {user.username}({user_id}) 已设置为在线状态")
            
            # 2. 获取用户的所有好友
            friends_query = db.query(Friend).filter(Friend.user_id == user_id)
            friends = friends_query.all()
            
            online_friends = []
            friend_ids = []
            
            for friend_relation in friends:
                friend = db.query(User).filter(User.id == friend_relation.friend_id).first()
                if friend:
                    friend_ids.append(friend.id)
                    # 检查好友是否在线（既在数据库中标记为online，又在WebSocket连接中）
                    if (friend.status == 'online' and 
                        self.connection_manager.get(friend.id) is not None):
                        online_friends.append({
                            "user_id": friend.id,
                            "username": friend.username,
                            "status": "online",
                            "last_seen": friend.last_seen.isoformat() if friend.last_seen else None
                        })
            
            logger.info(f"[状态更新] 用户 {user.username} 共有 {len(friend_ids)} 个好友，其中 {len(online_friends)} 个在线")
            
            # 3. 向用户发送在线好友信息
            if online_friends:
                friends_message = {
                    "type": "friends_status",
                    "data": {
                        "online_friends": online_friends
                    }
                }
                await self._send_to_user(user_id, json.dumps(friends_message))
                logger.info(f"[状态更新] 已向用户 {user.username} 发送 {len(online_friends)} 个在线好友信息")
            else:
                logger.info(f"[状态更新] 用户 {user.username} 没有在线好友")
            
            # 4. 向所有好友广播用户上线消息
            user_online_message = {
                "type": "user_status_change",
                "data": {
                    "user_id": user_id,
                    "username": user.username,
                    "status": "online",
                    "timestamp": datetime.utcnow().isoformat()
                }
            }
            
            online_friend_count = 0
            total_friends = len(friend_ids)
            logger.info(f"[状态更新] 开始向 {total_friends} 个好友广播用户 {user.username} 上线消息")
            
            for friend_id in friend_ids:
                friend_connection = self.connection_manager.get(friend_id)
                if friend_connection is not None:
                    try:
                        await self._send_to_user(friend_id, json.dumps(user_online_message))
                        online_friend_count += 1
                        logger.debug(f"[状态更新] 成功向好友 {friend_id} 发送上线消息")
                    except Exception as e:
                        logger.error(f"[状态更新] 向好友 {friend_id} 发送上线消息失败: {str(e)}")
                else:
                    logger.debug(f"[状态更新] 好友 {friend_id} 不在线，跳过广播")
            
            logger.info(f"[状态更新] 已向 {online_friend_count}/{total_friends} 个在线好友广播用户 {user.username} 上线消息")
            
            return {
                "success": True,
                "message": "用户状态更新成功",
                "online_friends": online_friends,
                "notified_friends": online_friend_count
            }
            
        except Exception as e:
            db.rollback()
            logger.error(f"[状态更新] 用户登录处理失败: {str(e)}")
            return {"success": False, "message": f"状态更新失败: {str(e)}"}
        finally:
            db.close()
    
    async def user_logout(self, user_id: int) -> dict:
        """用户退出处理
        
        1. 更新用户状态为offline
        2. 向所有在线好友广播用户离线消息
        
        Args:
            user_id: 用户ID
            
        Returns:
            dict: 包含操作结果
        """
        db = self.get_db()
        try:
            # 1. 更新用户状态为offline
            user = db.query(User).filter(User.id == user_id).first()
            if not user:
                return {"success": False, "message": "用户不存在"}
                
            user.status = 'offline'
            user.last_seen = datetime.utcnow()
            db.commit()
            
            # 移除心跳记录
            if user_id in self.user_last_heartbeat:
                del self.user_last_heartbeat[user_id]
            
            logger.info(f"[状态更新] 用户 {user.username}({user_id}) 已设置为离线状态")
            
            # 2. 获取用户的所有好友
            friends_query = db.query(Friend).filter(Friend.user_id == user_id)
            friends = friends_query.all()
            
            # 3. 向所有在线好友广播用户离线消息
            user_offline_message = {
                "type": "user_status_change",
                "data": {
                    "user_id": user_id,
                    "username": user.username,
                    "status": "offline",
                    "timestamp": datetime.utcnow().isoformat()
                }
            }
            
            notified_friend_count = 0
            total_friends = len(friends)
            logger.info(f"[状态更新] 开始向 {total_friends} 个好友广播用户 {user.username} 离线消息")
            
            for friend_relation in friends:
                friend_id = friend_relation.friend_id
                friend_connection = self.connection_manager.get(friend_id)
                if friend_connection is not None:
                    try:
                        await self._send_to_user(friend_id, json.dumps(user_offline_message))
                        notified_friend_count += 1
                        logger.debug(f"[状态更新] 成功向好友 {friend_id} 发送离线消息")
                    except Exception as e:
                        logger.error(f"[状态更新] 向好友 {friend_id} 发送离线消息失败: {str(e)}")
                else:
                    logger.debug(f"[状态更新] 好友 {friend_id} 不在线，跳过广播")
            
            logger.info(f"[状态更新] 已向 {notified_friend_count}/{total_friends} 个在线好友广播用户 {user.username} 离线消息")
            
            return {
                "success": True,
                "message": "用户离线状态更新成功",
                "notified_friends": notified_friend_count
            }
            
        except Exception as e:
            db.rollback()
            logger.error(f"[状态更新] 用户退出处理失败: {str(e)}")
            return {"success": False, "message": f"状态更新失败: {str(e)}"}
        finally:
            db.close()
    
    async def update_user_heartbeat(self, user_id: int) -> dict:
        """更新用户心跳时间
        
        Args:
            user_id: 用户ID
            
        Returns:
            dict: 包含操作结果
        """
        db = self.get_db()
        try:
            # 更新内存中的心跳时间
            current_time = datetime.utcnow()
            self.user_last_heartbeat[user_id] = current_time
            
            # 更新数据库中的用户状态
            user = db.query(User).filter(User.id == user_id).first()
            if user:
                # 确保用户状态为在线
                if user.status != 'online':
                    user.status = 'online'
                    logger.info(f"[心跳] 用户 {user.username}({user_id}) 状态已更新为在线")
                
                # 更新最后活跃时间
                user.last_seen = current_time
                db.commit()
                
                logger.debug(f"[心跳] 用户 {user.username}({user_id}) 心跳时间和数据库状态已更新")
            else:
                logger.warning(f"[心跳] 用户 {user_id} 不存在")
                return {"success": False, "message": "用户不存在"}
            
            return {"success": True, "message": "心跳更新成功"}
        except Exception as e:
            db.rollback()
            logger.error(f"[心跳] 更新用户 {user_id} 心跳失败: {str(e)}")
            return {"success": False, "message": f"心跳更新失败: {str(e)}"}
        finally:
            db.close()
    
    async def check_heartbeat_timeouts(self) -> dict:
        """检查心跳超时的用户
        
        检查所有在线用户的心跳状态，将超时的用户设置为离线
        
        Returns:
            dict: 包含检查结果
        """
        db = self.get_db()
        try:
            current_time = datetime.utcnow()
            timeout_threshold = current_time - timedelta(seconds=self.heartbeat_timeout)
            
            # 获取所有标记为在线的用户
            online_users = db.query(User).filter(User.status == 'online').all()
            
            timeout_users = []
            
            for user in online_users:
                user_id = user.id
                
                # 检查用户是否还有WebSocket连接
                has_connection = self.connection_manager.get(user_id) is not None
                
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
                result = await self.user_logout(user.id)
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
            
        except Exception as e:
            logger.error(f"[心跳检测] 检查心跳超时失败: {str(e)}")
            return {"success": False, "message": f"心跳检测失败: {str(e)}"}
        finally:
            db.close()
    
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
                await self.check_heartbeat_timeouts()
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
    
    async def get_user_status(self, user_id: int) -> dict:
        """获取用户状态信息
        
        Args:
            user_id: 用户ID
            
        Returns:
            dict: 用户状态信息
        """
        db = self.get_db()
        try:
            user = db.query(User).filter(User.id == user_id).first()
            if not user:
                return {"success": False, "message": "用户不存在"}
            
            has_connection = self.connection_manager.get(user_id) is not None
            last_heartbeat = self.user_last_heartbeat.get(user_id)
            
            return {
                "success": True,
                "data": {
                    "user_id": user_id,
                    "username": user.username,
                    "status": user.status,
                    "last_seen": user.last_seen.isoformat() if user.last_seen else None,
                    "has_connection": has_connection,
                    "last_heartbeat": last_heartbeat.isoformat() if last_heartbeat else None
                }
            }
        except Exception as e:
            logger.error(f"[状态查询] 获取用户 {user_id} 状态失败: {str(e)}")
            return {"success": False, "message": f"状态查询失败: {str(e)}"}
        finally:
            db.close()

# 全局服务实例
_user_states_service: Optional[UserStatesUpdateService] = None

def get_user_states_service() -> UserStatesUpdateService:
    """获取用户状态服务实例"""
    global _user_states_service
    if _user_states_service is None:
        raise RuntimeError("用户状态服务未初始化")
    return _user_states_service

def initialize_user_states_service(connection_manager: ConnectionManager) -> UserStatesUpdateService:
    """初始化用户状态服务"""
    global _user_states_service
    _user_states_service = UserStatesUpdateService(connection_manager)
    return _user_states_service

async def cleanup_user_states_service():
    """清理用户状态服务"""
    global _user_states_service
    if _user_states_service is not None:
        await _user_states_service.stop_heartbeat_monitor()
        _user_states_service = None