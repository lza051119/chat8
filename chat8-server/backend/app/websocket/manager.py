class ConnectionManager:
    def __init__(self):
        # 核心数据结构：一个字典，用来存储所有在线用户的连接。
        # 键 (key) 是 user_id，值 (value) 是该用户的 WebSocket 连接对象。
        self.active_connections = {}  # user_id: websocket

    # 当一个新用户连接时，将他和他的连接对象登记在册。
    def connect(self, user_id, websocket):
        self.active_connections[user_id] = websocket

    # 当一个用户断开连接时，将他从登记册中移除。
    def disconnect(self, user_id):
        if user_id in self.active_connections:
            del self.active_connections[user_id]

    # 根据 user_id 查找并返回一个用户的连接对象。
    def get(self, user_id):
        return self.active_connections.get(user_id)

    # 返回当前所有在线用户的 user_id 列表。
    def get_online_users(self):
        return list(self.active_connections.keys())

    # 向指定用户发送一条私人消息（如果他在线的话）。
    def send_personal_message(self, message, user_id):
        ws = self.get(user_id)
        if ws:
            return ws.send_text(message)

    # 向所有在线用户广播一条消息。
    async def broadcast(self, message):
        for ws in self.active_connections.values():
            await ws.send_text(message)