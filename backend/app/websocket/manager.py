class ConnectionManager:
    def __init__(self):
        self.active_connections = {}  # user_id: websocket

    def connect(self, user_id, websocket):
        self.active_connections[user_id] = websocket

    def disconnect(self, user_id):
        if user_id in self.active_connections:
            del self.active_connections[user_id]

    def get(self, user_id):
        return self.active_connections.get(user_id)

    def get_online_users(self):
        return list(self.active_connections.keys())

    def send_personal_message(self, message, user_id):
        ws = self.get(user_id)
        if ws:
            return ws.send_text(message)

    async def broadcast(self, message):
        for ws in self.active_connections.values():
            await ws.send_text(message) 