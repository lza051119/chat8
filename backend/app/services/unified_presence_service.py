from typing import Dict, List, Optional, Set
from datetime import datetime, timedelta
from db.models import User
from db.database import SessionLocal
from websocket.manager import ConnectionManager
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
            # 更新用户状态为离线
            await self._update_user_status(user_id, 'offline', websocket_connected=False)
            
            # 通知好友用户离线
            await self._notify_friends_status_change(user_id, False, manager)
            
            print(f"[状态管理] 用户 {user_id} 已断开连接，状态已同步给好友")
    
    async def set_user_status(self, user_id: int, status: str, manager: ConnectionManager):
        """
        手动设置用户状态（通过API调用）
        """
        async with self._sync_lock:
            is_online = status == 'online'
            websocket_connected = manager.get(user_id) is not None
            
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
        websocket_connected = manager.get(user_id) is not None
        
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
    
    async def get_user_status(self, user_id: int, manager: ConnectionManager) -> Dict:
        """
        获取用户的完整状态信息
        """
        try:
            # 检查WebSocket连接状态
            websocket_connected = manager.get(user_id) is not None
            print(f"[DEBUG] 用户 {user_id} WebSocket连接状态: {websocket_connected}")
            print(f"[DEBUG] 连接管理器中的连接: {list(manager.active_connections.keys()) if hasattr(manager, 'active_connections') else 'N/A'}")
            
            # 从缓存获取状态
            cached_status = self.user_status_cache.get(user_id)
            
            if cached_status:
                # 检查心跳超时
                if cached_status['last_seen']:
                    time_diff = datetime.utcnow() - cached_status['last_seen']
                    is_online = websocket_connected or (time_diff.total_seconds() < self.heartbeat_timeout)
                else:
                    is_online = websocket_connected
            else:
                # 从数据库加载状态
                is_online = await self._load_user_status_from_db(user_id)
                is_online = is_online or websocket_connected
            
            # 获取用户名
            username = await self._get_username(user_id)
            
            # 获取P2P能力信息
            p2p_info = self.p2p_capabilities.get(user_id, {'supports_p2p': False, 'capabilities': []})
            supports_p2p = p2p_info.get('supports_p2p', False)
            print(f"[DEBUG] 用户 {user_id} P2P能力信息: {p2p_info}")
            print(f"[DEBUG] P2P能力缓存中的所有用户: {list(self.p2p_capabilities.keys())}")
            print(f"[DEBUG] 用户 {user_id} supports_p2p: {supports_p2p}")
            
            print(f"[DEBUG] 用户 {user_id} P2P能力检查: p2p_info={p2p_info}, supports_p2p={supports_p2p}")
            
            # 获取最后在线时间
            last_seen = cached_status.get('last_seen') if cached_status else None
            
            print(f"[DEBUG] 用户 {user_id} 状态信息: online={is_online}, supportsP2P={supports_p2p}, websocket={websocket_connected}")
            
            return {
                'isOnline': is_online,
                'online': is_online,
                'status': 'online' if is_online else 'offline',
                'lastSeen': last_seen.isoformat() if last_seen else None,
                'websocketConnected': websocket_connected,
                'p2pCapability': supports_p2p,
                'supportsP2P': supports_p2p,
                'username': username,
                'capabilities': p2p_info.get('capabilities', [])
            }
        except Exception as e:
            print(f"[状态管理] 获取用户状态异常: {e}")
            return {
                'isOnline': False,
                'online': False,
                'status': 'offline',
                'lastSeen': None,
                'websocketConnected': False,
                'p2pCapability': False,
                'supportsP2P': False,
                'username': f'User{user_id}',
                'capabilities': []
            }
    
    async def get_contacts_status(self, user_ids: List[int], manager: ConnectionManager) -> List[Dict]:
        """
        批量获取联系人状态
        """
        result = []
        
        for user_id in user_ids:
            status_info = await self.get_user_status(user_id, manager)
            
            # 从数据库获取用户名
            username = await self._get_username(user_id)
            
            result.append({
                'userId': str(user_id),
                'username': username,
                'status': 'online' if status_info['online'] else 'offline',
                'isOnline': status_info['online'],
                'timestamp': datetime.utcnow().isoformat(),
                'lastSeen': status_info['lastSeen'],
                'websocketConnected': status_info.get('websocketConnected', False),
                'p2pCapability': status_info['p2pCapability']
            })
        
        return result
    
    async def set_p2p_capability(self, user_id: int, supports_p2p: bool, capabilities: List[str]):
        """
        设置用户P2P能力
        """
        self.p2p_capabilities[user_id] = {
            'supports_p2p': supports_p2p,
            'capabilities': capabilities,
            'updated_at': datetime.utcnow()
        }
        
        print(f"[状态管理] 用户 {user_id} P2P能力已更新: {supports_p2p}")
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
        
        self.user_status_cache[user_id] = {
            'status': status,
            'last_seen': current_time,
            'websocket_connected': websocket_connected
        }
        
        # 同步到数据库
        await self._update_database_status(user_id, status)
    
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
            from db.models import Friend
            
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