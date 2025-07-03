import sqlite3
import os
import json
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
from contextlib import contextmanager

# 数据库存储目录
# 使用与原JSON文件相同的路径：app/local_storage/messages
import pathlib
app_dir = pathlib.Path(__file__).parent.parent
DB_STORAGE_DIR = os.path.join(app_dir, 'local_storage', 'messages')
os.makedirs(DB_STORAGE_DIR, exist_ok=True)

class MessageDBService:
    """消息数据库服务类"""
    
    @staticmethod
    def get_user_db_path(user_id: int) -> str:
        """获取用户数据库文件路径"""
        return os.path.join(DB_STORAGE_DIR, f'user_{user_id}_messages.db')
    
    @staticmethod
    @contextmanager
    def get_db_connection(user_id: int):
        """获取数据库连接的上下文管理器"""
        db_path = MessageDBService.get_user_db_path(user_id)
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row  # 使结果可以通过列名访问
        try:
            yield conn
        finally:
            conn.close()
    
    @staticmethod
    def init_user_database(user_id: int):
        """初始化用户数据库表结构"""
        with MessageDBService.get_db_connection(user_id) as conn:
            cursor = conn.cursor()
            
            # 创建消息表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    message_id TEXT UNIQUE,  -- 原始消息ID
                    from_user INTEGER NOT NULL,
                    to_user INTEGER NOT NULL,
                    content TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    received_time TEXT NOT NULL,  -- 消息接收时间
                    method TEXT DEFAULT 'Server',  -- 传输方式 (P2P/Server)
                    encrypted BOOLEAN DEFAULT FALSE,
                    message_type TEXT DEFAULT 'text',  -- 消息类型 (text/image)
                    file_path TEXT DEFAULT NULL,  -- 文件路径（图片消息）
                    file_name TEXT DEFAULT NULL,  -- 文件名（图片消息）
                    hidding_message TEXT DEFAULT NULL,  -- 隐藏消息内容（隐写术）
                    is_burn_after_read BOOLEAN DEFAULT FALSE,  -- 是否为阅读后销毁消息
                    readable_duration INTEGER DEFAULT NULL,  -- 可读时间（秒），NULL表示永久可读
                    is_read BOOLEAN DEFAULT FALSE,  -- 是否已读
                    read_time TEXT DEFAULT NULL,  -- 阅读时间
                    is_deleted BOOLEAN DEFAULT FALSE,  -- 是否已删除
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # 添加新字段（如果表已存在但缺少这些字段）
            try:
                cursor.execute('ALTER TABLE messages ADD COLUMN message_type TEXT DEFAULT "text"')
            except sqlite3.OperationalError:
                pass  # 字段已存在
            
            try:
                cursor.execute('ALTER TABLE messages ADD COLUMN file_path TEXT DEFAULT NULL')
            except sqlite3.OperationalError:
                pass  # 字段已存在
            
            try:
                cursor.execute('ALTER TABLE messages ADD COLUMN file_name TEXT DEFAULT NULL')
            except sqlite3.OperationalError:
                pass  # 字段已存在
            
            try:
                cursor.execute('ALTER TABLE messages ADD COLUMN hidding_message TEXT DEFAULT NULL')
            except sqlite3.OperationalError:
                pass  # 字段已存在
            
            # 迁移旧的 hidden_message 字段到 hidding_message
            try:
                # 检查是否存在旧字段
                cursor.execute("PRAGMA table_info(messages)")
                columns = [column[1] for column in cursor.fetchall()]
                if 'hidden_message' in columns and 'hidding_message' not in columns:
                    cursor.execute('ALTER TABLE messages RENAME COLUMN hidden_message TO hidding_message')
                elif 'hidden_message' in columns and 'hidding_message' in columns:
                    # 如果两个字段都存在，复制数据并删除旧字段
                    cursor.execute('UPDATE messages SET hidding_message = hidden_message WHERE hidden_message IS NOT NULL')
                    # SQLite不支持直接删除列，这里只是标记处理完成
            except sqlite3.OperationalError:
                pass  # 迁移失败，继续执行
            
            # 创建索引以提高查询性能
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_from_user ON messages(from_user)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_to_user ON messages(to_user)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_timestamp ON messages(timestamp)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_message_id ON messages(message_id)')
            
            conn.commit()
    
    @staticmethod
    def add_message(user_id: int, message_data: Dict) -> bool:
        """添加消息到数据库"""
        try:
            MessageDBService.init_user_database(user_id)
            
            with MessageDBService.get_db_connection(user_id) as conn:
                cursor = conn.cursor()
                
                # 生成唯一的消息ID
                message_id = message_data.get('id')
                if message_id is None:
                    message_id = f"{datetime.now().timestamp()}_{user_id}"
                
                # 准备基础字段
                base_values = (
                    message_id,
                    message_data.get('from'),
                    message_data.get('to'),
                    message_data.get('content'),
                    message_data.get('timestamp'),
                    datetime.now().isoformat(),
                    message_data.get('method', 'Server'),
                    message_data.get('encrypted', False),
                    message_data.get('message_type', 'text'),
                    message_data.get('file_path') if message_data.get('message_type') == 'image' else None,
                    message_data.get('file_name') if message_data.get('message_type') == 'image' else None,
                    message_data.get('hidding_message'),
                    message_data.get('is_burn_after_read', False),
                    message_data.get('readable_duration'),
                    datetime.now().isoformat()
                )
                
                cursor.execute('''
                    INSERT OR REPLACE INTO messages (
                        message_id, from_user, to_user, content, timestamp, 
                        received_time, method, encrypted, message_type, file_path, file_name,
                        hidding_message, is_burn_after_read, readable_duration, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', base_values)
                
                conn.commit()
                return True
                
        except Exception as e:
            print(f"添加消息失败: {e}")
            return False
    
    @staticmethod
    def get_messages_with_friend(
        user_id: int, 
        friend_id: int, 
        limit: int = 50, 
        offset: int = 0, 
        search: str = None
    ) -> Tuple[List[Dict], int, bool]:
        """获取与指定好友的聊天记录"""
        try:
            MessageDBService.init_user_database(user_id)
            
            with MessageDBService.get_db_connection(user_id) as conn:
                cursor = conn.cursor()
                
                # 构建查询条件
                where_conditions = [
                    "is_deleted = FALSE",
                    "((from_user = ? AND to_user = ?) OR (from_user = ? AND to_user = ?))"
                ]
                params = [user_id, friend_id, friend_id, user_id]
                
                # 添加搜索条件
                if search and search.strip():
                    where_conditions.append("content LIKE ?")
                    params.append(f"%{search.strip()}%")
                
                where_clause = " AND ".join(where_conditions)
                
                # 获取总数
                count_query = f"SELECT COUNT(*) FROM messages WHERE {where_clause}"
                cursor.execute(count_query, params)
                total_count = cursor.fetchone()[0]
                
                # 获取消息列表（按时间戳倒序）
                query = f'''
                    SELECT * FROM messages 
                    WHERE {where_clause}
                    ORDER BY timestamp DESC 
                    LIMIT ? OFFSET ?
                '''
                cursor.execute(query, params + [limit, offset])
                
                rows = cursor.fetchall()
                messages = []
                
                for row in rows:
                    # 安全地获取字段值，处理可能不存在的字段
                    def safe_get(row, key, default=None):
                        try:
                            return row[key]
                        except (KeyError, IndexError):
                            return default
                    
                    message = {
                        'id': row['message_id'],
                        'from': row['from_user'],
                        'to': row['to_user'],
                        'content': row['content'],
                        'timestamp': row['timestamp'],
                        'received_time': row['received_time'],
                        'method': row['method'],
                        'encrypted': bool(row['encrypted']),
                        'messageType': safe_get(row, 'message_type', 'text'),
                        'filePath': safe_get(row, 'file_path'),
                        'fileName': safe_get(row, 'file_name'),
                        'is_burn_after_read': bool(row['is_burn_after_read']),
                        'readable_duration': row['readable_duration'],
                        'is_read': bool(row['is_read']),
                        'read_time': row['read_time']
                    }
                    
                    # 检查阅读后销毁消息的可读性
                    if message['is_burn_after_read'] and message['is_read']:
                        if message['readable_duration'] and message['read_time']:
                            read_time = datetime.fromisoformat(message['read_time'])
                            expire_time = read_time + timedelta(seconds=message['readable_duration'])
                            if datetime.now() > expire_time:
                                # 消息已过期，不返回内容
                                message['content'] = "[消息已销毁]"
                    
                    messages.append(message)
                
                has_more = (offset + limit) < total_count
                
                return messages, total_count, has_more
                
        except Exception as e:
            print(f"获取消息失败: {e}")
            return [], 0, False
    
    @staticmethod
    def mark_message_as_read(user_id: int, message_id: str) -> bool:
        """标记消息为已读"""
        try:
            with MessageDBService.get_db_connection(user_id) as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    UPDATE messages 
                    SET is_read = TRUE, read_time = ?, updated_at = ?
                    WHERE message_id = ? AND to_user = ?
                ''', (
                    datetime.now().isoformat(),
                    datetime.now().isoformat(),
                    message_id,
                    user_id
                ))
                
                conn.commit()
                return cursor.rowcount > 0
                
        except Exception as e:
            print(f"标记消息已读失败: {e}")
            return False
    
    @staticmethod
    def delete_message(user_id: int, message_id: str) -> bool:
        """删除消息（软删除）"""
        try:
            with MessageDBService.get_db_connection(user_id) as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    UPDATE messages 
                    SET is_deleted = TRUE, updated_at = ?
                    WHERE message_id = ? AND (from_user = ? OR to_user = ?)
                ''', (
                    datetime.now().isoformat(),
                    message_id,
                    user_id,
                    user_id
                ))
                
                conn.commit()
                return cursor.rowcount > 0
                
        except Exception as e:
            print(f"删除消息失败: {e}")
            return False
    
    @staticmethod
    def clear_all_messages(user_id: int) -> bool:
        """清空用户的所有消息"""
        try:
            with MessageDBService.get_db_connection(user_id) as conn:
                cursor = conn.cursor()
                cursor.execute('DELETE FROM messages')
                conn.commit()
                return True
                
        except Exception as e:
            print(f"清空消息失败: {e}")
            return False
    
    @staticmethod
    def get_database_status(user_id: int) -> Dict:
        """获取数据库状态信息"""
        try:
            db_path = MessageDBService.get_user_db_path(user_id)
            
            if not os.path.exists(db_path):
                return {
                    "exists": False,
                    "message_count": 0,
                    "file_size": 0
                }
            
            with MessageDBService.get_db_connection(user_id) as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT COUNT(*) FROM messages WHERE is_deleted = FALSE')
                message_count = cursor.fetchone()[0]
                
                file_size = os.path.getsize(db_path)
                
                return {
                    "exists": True,
                    "message_count": message_count,
                    "file_size": file_size,
                    "file_path": db_path
                }
                
        except Exception as e:
            print(f"获取数据库状态失败: {e}")
            return {
                "exists": False,
                "message_count": 0,
                "file_size": 0,
                "error": str(e)
            }
    
    @staticmethod
    def migrate_from_json(user_id: int) -> bool:
        """从JSON文件迁移数据到数据库"""
        try:
            # 获取原JSON文件路径
            json_file_path = os.path.join(DB_STORAGE_DIR, f'user_{user_id}_messages.json')
            
            if not os.path.exists(json_file_path):
                # 用户的JSON文件不存在，跳过迁移
                return True
            
            # 读取JSON数据
            with open(json_file_path, 'r', encoding='utf-8') as f:
                json_messages = json.load(f)
            
            # 初始化数据库
            MessageDBService.init_user_database(user_id)
            
            # 迁移每条消息
            success_count = 0
            for msg in json_messages:
                if MessageDBService.add_message(user_id, msg):
                    success_count += 1
            
            # 用户迁移完成
            
            # 备份原JSON文件
            backup_path = json_file_path + '.backup'
            os.rename(json_file_path, backup_path)
            print(f"原JSON文件已备份到: {backup_path}")
            
            return True
            
        except Exception as e:
            print(f"迁移失败: {e}")
            return False