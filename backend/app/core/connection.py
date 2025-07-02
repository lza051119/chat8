from app.websocket.manager import ConnectionManager

# 创建 ConnectionManager 单例
connection_manager = ConnectionManager()

def get_connection_manager():
    """获取全局连接管理器实例"""
    return connection_manager