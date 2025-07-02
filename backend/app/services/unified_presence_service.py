from typing import Dict, Set, Optional, List
from datetime import datetime, timedelta
from app.db.models import User
from app.db.database import SessionLocal
from app.websocket.manager import ConnectionManager
import asyncio
import json
from sqlalchemy.orm import Session

class UnifiedPresenceService:
    """
    统一的用户在线状态管理服务
    负责管理用户的在线状态、P2P能力、状态同步等功能
    """
    
    def __init__(self):
        # 用户在线状态缓存 {user_id: {'status': 'online/offline', 'last_seen': datetime, 'websocket_connected': bool}}
        self.user_status_cache: Dict[int, Dict] = {}
        
        # P2P能力缓存 {user_id: {'supports_p2p': bool, 'capabilities': list, 'updated_at': datetime}}
        self.p2p_capabilities: Dict[int, Dict] = {}
        
        # 用户好友关系缓存 {user_id: set(friend_ids)}
        self.friends_cache: Dict[int, Set[int]] = {}
        
        # 状态变化监听器 {user_id: [callback_functions]}
        self.status_listeners: Dict[int, List] = {}
        
        # 心跳超时时间（秒）
        self.heartbeat_timeout = 120  # 2分钟
        
        # 状态同步锁
        self._sync_lock = asyncio.Lock()
    
    async def user_connected(self, user_id: int, websocket, manager: ConnectionManager):
        """
        用户WebSocket连接建立时调用
        """
        async with self._sync_lock:
            # 更新用户状态为在线
            await self._update_user_status(user_id, 'online', websocket_connected=True)
            
            # 加载用户好友关系
            await self._load_user_friends(user_id)
            
            # 通知好友用户上线
            await self._notify_friends_status_change(user_id, True, manager)
            
            print(f"[状态管理] 用户 {user_id} 已连接，状态已同步给好友")
    
    async def user_disconnected(self, user_id: int, manager: ConnectionManager):
        """
        用户WebSocket连接断开时调用
        """
        async with self._sync_lock:
            # 检查用户是否还有其他活跃连接
            remaining_connections = manager.get_all_connections(user_id)
            websocket_connected = len(remaining_connections) > 0
            
            if websocket_connected:
                # 用户还有其他连接，保持在线状态
                print(f"[状态管理] 用户 {user_id} 断开一个连接，但还有 {len(remaining_connections)} 个连接保持活跃")
            else:
                # 用户所有连接都断开，设置为离线
                await self._update_user_status(user_id, 'offline', websocket_connected=False)
                
                # 通知好友用户离线
                await self._notify_friends_status_change(user_id, False, manager)
                
                print(f"[状态管理] 用户 {user_id} 所有连接已断开，状态已同步给好友")
    
    async def set_user_status(self, user_id: int, status: str, manager: ConnectionManager):
        """
        手动设置用户状态（通过API调用）
        """
        async with self._sync_lock:
            is_online = status == 'online'
            user_connections = manager.get_all_connections(user_id)
            websocket_connected = len(user_connections) > 0
            
            await self._update_user_status(user_id, status, websocket_connected=websocket_connected)
            
            # 加载用户好友关系（如果还没有加载）
            if user_id not in self.friends_cache:
                await self._load_user_friends(user_id)
            
            # 通知好友状态变化
            await self._notify_friends_status_change(user_id, is_online, manager)
            
            print(f"[状态管理] 用户 {user_id} 手动设置状态为 {status}，已同步给好友")
    
    async def heartbeat(self, user_id: int, manager: ConnectionManager):
        """
        用户心跳更新
        """
        current_time = datetime.utcnow()
        user_connections = manager.get_all_connections(user_id)
        websocket_connected = len(user_connections) > 0
        
        # 更新心跳时间和状态
        status = 'online' if websocket_connected else 'offline'
        
        if user_id in self.user_status_cache:
            self.user_status_cache[user_id]['last_seen'] = current_time
            self.user_status_cache[user_id]['websocket_connected'] = websocket_connected
            self.user_status_cache[user_id]['status'] = status
        else:
            # 如果缓存中没有，创建新的状态记录
            await self._update_user_status(user_id, status, websocket_connected=websocket_connected)
        
        # 更新数据库
        await self._update_database_status(user_id, status)
        
        # 如果状态发生变化，通知好友
        if user_id not in self.friends_cache:
            await self._load_user_friends(user_id)
        await self._notify_friends_status_change(user_id, websocket_connected, manager)
        
        return {"nextHeartbeat": 30000, "status": "success"}
    
    async def get_user_status(self, user_id: int, manager: ConnectionManager) -> dict:
        """
        获取用户状态
        """
        # 检查WebSocket连接状态
        connections = manager.get_all_connections(user_id)
        websocket_connected = len(connections) > 0
        
        # 从缓存获取状态
        cached_status = self.user_status_cache.get(user_id)
        
        if cached_status:
            # 更新WebSocket连接状态
            cached_status['websocket_connected'] = websocket_connected
            # 用户在线的条件：缓存状态为online且有WebSocket连接
            is_online = cached_status['status'] == 'online' and websocket_connected
        else:
            # 从数据库加载状态
            db_online = await self._load_user_status_from_db(user_id)
            # 用户在线的条件：数据库状态为online且有WebSocket连接
            is_online = db_online and websocket_connected
            
            # 更新缓存
            await self._update_user_status(user_id, 'online' if is_online else 'offline', websocket_connected)
            cached_status = self.user_status_cache[user_id]
        
        # 获取P2P能力
        p2p_info = self.p2p_capabilities.get(user_id, {})
        
        result = {
            'userId': user_id,
            'username': await self._get_username(user_id),
            'status': 'online' if is_online else 'offline',
            'isOnline': is_online,
            'lastSeen': cached_status['last_seen'].isoformat() if cached_status.get('last_seen') else None,
            'websocketConnected': websocket_connected,
            'p2pCapability': p2p_info.get('supports_p2p', False),
            'p2pCapabilities': p2p_info.get('capabilities', [])
        }
        
        print(f"[状态管理] 获取用户 {user_id} 状态: {result}")
        return result
    
    async def get_contacts_status(self, user_ids: List[int], manager: ConnectionManager) -> List[Dict]:
        """
        批量获取联系人状态
        """
        result = []
        
        for user_id in user_ids:
            try:
                status_info = await self.get_user_status(user_id, manager)
                result.append(status_info)
            except Exception as e:
                print(f"[状态管理] 获取用户 {user_id} 状态失败: {e}")
                # 添加默认状态信息
                result.append({
                    'userId': user_id,
                    'username': f'User{user_id}',
                    'status': 'offline',
                    'isOnline': False,
                    'lastSeen': None,
                    'websocketConnected': False,
                    'p2pCapability': False,
                    'p2pCapabilities': []
                })
        
        print(f"[状态管理] 批量获取 {len(user_ids)} 个联系人状态完成")
        return result
    
    async def set_p2p_capability(self, user_id: int, supports_p2p: bool, capabilities: List[str], manager: ConnectionManager = None):
        """
        设置用户P2P能力
        """
        self.p2p_capabilities[user_id] = {
            'supports_p2p': supports_p2p,
            'capabilities': capabilities,
            'updated_at': datetime.utcnow()
        }
        
        print(f"[状态管理] 用户 {user_id} P2P能力已更新: {supports_p2p}")
        
        # 如果用户在线且支持P2P，通知好友状态变化
        if manager and supports_p2p:
            user_connections = manager.get_all_connections(user_id)
            if len(user_connections) > 0:  # 用户在线
                # 加载用户好友关系（如果还没有加载）
                if user_id not in self.friends_cache:
                    await self._load_user_friends(user_id)
                
                # 通知好友P2P能力变化
                await self._notify_friends_status_change(user_id, True, manager)
                print(f"[状态管理] 用户 {user_id} P2P能力变化已通知好友")
        
        return True
    
    async def cleanup_expired_status(self):
        """
        清理过期的状态信息
        """
        current_time = datetime.utcnow()
        expired_users = []
        
        for user_id, status_info in self.user_status_cache.items():
            if status_info['last_seen']:
                time_diff = current_time - status_info['last_seen']
                if time_diff.total_seconds() > self.heartbeat_timeout and not status_info.get('websocket_connected', False):
                    expired_users.append(user_id)
        
        # 将过期用户设置为离线
        for user_id in expired_users:
            await self._update_user_status(user_id, 'offline', websocket_connected=False)
            print(f"[状态管理] 用户 {user_id} 因心跳超时被设置为离线")
    
    async def _update_user_status(self, user_id: int, status: str, websocket_connected: bool = False):
        """
        内部方法：更新用户状态
        """
        current_time = datetime.utcnow()
        
        # 保留现有的状态信息，只更新必要字段
        existing_status = self.user_status_cache.get(user_id, {})
        
        self.user_status_cache[user_id] = {
            'status': status,
            'last_seen': current_time,
            'websocket_connected': websocket_connected,
            # 保留其他现有信息
            **{k: v for k, v in existing_status.items() if k not in ['status', 'last_seen', 'websocket_connected']}
        }
        
        # 同步到数据库
        await self._update_database_status(user_id, status)
        
        print(f"[状态管理] 用户 {user_id} 状态已更新: {status}, WebSocket连接: {websocket_connected}")
    
    async def _update_database_status(self, user_id: int, status: str):
        """
        更新数据库中的用户状态
        """
        db = SessionLocal()
        try:
            user = db.query(User).filter(User.id == user_id).first()
            if user:
                user.status = status
                user.last_seen = datetime.utcnow()
                db.commit()
        finally:
            db.close()
    
    async def _load_user_friends(self, user_id: int):
        """
        加载用户的好友关系
        """
        if user_id in self.friends_cache:
            return
        
        db = SessionLocal()
        try:
            # 查询双向好友关系
            from app.db.models import Friend
            
            friends = db.query(Friend).filter(
                (Friend.user_id == user_id) | (Friend.friend_id == user_id)
            ).all()
            
            friend_ids = set()
            for friend in friends:
                if friend.user_id == user_id:
                    friend_ids.add(friend.friend_id)
                else:
                    friend_ids.add(friend.user_id)
            
            self.friends_cache[user_id] = friend_ids
            print(f"[状态管理] 已加载用户 {user_id} 的好友关系，共 {len(friend_ids)} 个好友")
            
        finally:
            db.close()
    
    async def _notify_friends_status_change(self, user_id: int, is_online: bool, manager: ConnectionManager):
        """
        通知好友用户状态变化
        """
        if user_id not in self.friends_cache:
            return
        
        friends = self.friends_cache[user_id]
        if not friends:
            return
        
        # 获取用户的完整状态信息
        user_status = self.user_status_cache.get(user_id, {})
        p2p_info = self.p2p_capabilities.get(user_id, {})
        
        # 构造状态变化消息
        status_message = {
            'type': 'presence',
            'userId': user_id,
            'status': 'online' if is_online else 'offline',
            'isOnline': is_online,
            'timestamp': datetime.utcnow().isoformat(),
            'websocketConnected': user_status.get('websocket_connected', False),
            'p2pCapability': p2p_info.get('supports_p2p', False)
        }
        
        # 发送给所有在线好友
        online_friends = 0
        for friend_id in friends:
            friend_ws = manager.get(friend_id)
            if friend_ws:
                try:
                    await friend_ws.send_text(json.dumps(status_message))
                    online_friends += 1
                except Exception as e:
                    print(f"[状态管理] 发送状态变化给好友 {friend_id} 失败: {e}")
        
        print(f"[状态管理] 用户 {user_id} 的状态变化已通知 {online_friends} 个在线好友")
    
    async def _load_user_status_from_db(self, user_id: int) -> bool:
        """
        从数据库加载用户状态
        """
        db = SessionLocal()
        try:
            user = db.query(User).filter(User.id == user_id).first()
            if user:
                return user.status == 'online'
            return False
        finally:
            db.close()
    
    async def _get_username(self, user_id: int) -> str:
        """
        获取用户名
        """
        db = SessionLocal()
        try:
            user = db.query(User).filter(User.id == user_id).first()
            return user.username if user else f"User{user_id}"
        finally:
            db.close()

    async def start_service(self):
        """
        启动状态管理服务
        """
        # 启动定期清理任务
        asyncio.create_task(self._cleanup_task())
        print("[状态管理] 统一状态管理服务已启动")
    
    async def stop_service(self):
        """
        停止状态管理服务
        """
        print("[状态管理] 统一状态管理服务已停止")
    
    async def _cleanup_task(self):
        """
        定期清理任务
        """
        while True:
            try:
                await self.cleanup_expired_status()
                await asyncio.sleep(60)  # 每分钟清理一次
            except Exception as e:
                print(f"[状态管理] 清理任务异常: {e}")
                await asyncio.sleep(60)

# 创建全局实例
unified_presence = UnifiedPresenceService()