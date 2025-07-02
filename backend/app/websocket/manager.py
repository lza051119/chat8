class ConnectionManager:
    def __init__(self):
        self.active_connections = {}  # user_id: [websocket1, websocket2, ...]

    def connect(self, user_id, websocket):
        if user_id not in self.active_connections:
            self.active_connections[user_id] = []
        self.active_connections[user_id].append(websocket)
        print(f"[连接管理] 用户 {user_id} 新增连接，当前连接数: {len(self.active_connections[user_id])}")

    def disconnect(self, user_id, websocket=None):
        if user_id in self.active_connections:
            if websocket:
                # 移除特定的websocket连接
                try:
                    self.active_connections[user_id].remove(websocket)
                    print(f"[连接管理] 用户 {user_id} 移除一个连接，剩余连接数: {len(self.active_connections[user_id])}")
                except ValueError:
                    pass
                # 如果没有连接了，删除用户记录
                if not self.active_connections[user_id]:
                    del self.active_connections[user_id]
            else:
                # 移除用户的所有连接
                del self.active_connections[user_id]
                print(f"[连接管理] 用户 {user_id} 所有连接已移除")

    def get(self, user_id):
        connections = self.active_connections.get(user_id, [])
        return connections[0] if connections else None  # 返回第一个连接用于兼容性

    def get_all_connections(self, user_id):
        return self.active_connections.get(user_id, [])

    def get_online_users(self):
        return list(self.active_connections.keys())

    def send_personal_message(self, message, user_id):
        connections = self.get_all_connections(user_id)
        results = []
        for ws in connections:
            try:
                result = ws.send_text(message)
                results.append(result)
            except Exception as e:
                print(f"[连接管理] 发送消息到用户 {user_id} 的连接失败: {e}")
        return results

    async def send_personal_message_async(self, message, user_id):
        connections = self.get_all_connections(user_id)
        for ws in connections:
            try:
                await ws.send_text(message)
            except Exception as e:
                print(f"[连接管理] 异步发送消息到用户 {user_id} 的连接失败: {e}")

    async def broadcast(self, message):
        for connections in self.active_connections.values():
            for ws in connections:
                try:
                    await ws.send_text(message)
                except Exception as e:
                    print(f"[连接管理] 广播消息失败: {e}")