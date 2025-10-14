import json
from fastapi import WebSocket

class ConnectionManager:
    def __init__(self):
        # 使用字典来存储活跃的连接，键为user_id，值为WebSocket连接对象
        self.active_connections: dict[int, WebSocket] = {}

    async def connect(self, user_id: int, websocket: WebSocket):
        """连接新的WebSocket客户端"""
        await websocket.accept()
        self.active_connections[user_id] = websocket
        print(f"[WebSocket] 用户 {user_id} 已连接。当前在线人数: {len(self.active_connections)}")

    def disconnect(self, user_id: int):
        """断开WebSocket客户端连接"""
        if user_id in self.active_connections:
            del self.active_connections[user_id]
            print(f"[WebSocket] 用户 {user_id} 已断开。当前在线人数: {len(self.active_connections)}")

    # 根据 user_id 查找并返回一个用户的连接对象。
    def get(self, user_id):
        return self.active_connections.get(user_id)

    # 返回当前所有在线用户的 user_id 列表。
    def get_online_users(self):
        return list(self.active_connections.keys())

    async def send_personal_message(self, message: str, user_id: int):
        ws = self.get(user_id)
        if ws:
            return ws.send_text(message)

    # 向所有在线用户广播一条消息。
    async def broadcast(self, message):
        for ws in self.active_connections.values():
            await ws.send_text(message)

    def get_connection(self, user_id: int) -> WebSocket | None:
        """安全地获取单个用户的WebSocket连接"""
        return self.active_connections.get(user_id)

    def is_user_connected(self, user_id: int) -> bool:
        """检查用户是否在线（是否有活跃的WebSocket连接）"""
        return user_id in self.active_connections

    def get_online_user_ids(self) -> list[int]:
        """获取所有在线用户的ID列表"""
        return list(self.active_connections.keys())

manager = ConnectionManager()