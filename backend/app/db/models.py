from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey
# 兼容所有SQLAlchemy版本的declarative_base导入
try:
    from sqlalchemy.orm import declarative_base, relationship
except ImportError:
    from sqlalchemy.ext.declarative import declarative_base
    from sqlalchemy.orm import relationship
from datetime import datetime

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(32), unique=True, index=True, nullable=False)
    email = Column(String(128), unique=True, index=True, nullable=False)
    password_hash = Column(String(128), nullable=False)
    avatar = Column(String(256), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_seen = Column(DateTime, default=datetime.utcnow)
    public_key = Column(Text, nullable=True)
    status = Column(String(16), default='offline')
    friends = relationship('Friend', back_populates='user', cascade='all, delete-orphan', foreign_keys='Friend.user_id')

class Friend(Base):
    __tablename__ = 'friends'
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    friend_id = Column(Integer, ForeignKey('users.id'))
    created_at = Column(DateTime, default=datetime.utcnow)
    user = relationship('User', foreign_keys=[user_id], back_populates='friends')
    friend_user = relationship('User', foreign_keys=[friend_id])

class Message(Base):
    __tablename__ = 'messages'
    id = Column(Integer, primary_key=True, index=True)
    from_id = Column(Integer, ForeignKey('users.id'))
    to_id = Column(Integer, ForeignKey('users.id'))
    content = Column(Text, nullable=False)
    message_type = Column(String(16), default='text')  # text, image
    file_path = Column(String(512), nullable=True)  # 图片文件路径
    file_name = Column(String(256), nullable=True)  # 原始文件名
    encrypted = Column(Boolean, default=True)
    method = Column(String(16), default='Server')
    timestamp = Column(DateTime, default=datetime.utcnow)
    destroy_after = Column(Integer, nullable=True)  # 阅后即焚秒数
    hidding_message = Column(Text, nullable=True)  # 隐藏在图片中的消息

class Key(Base):
    __tablename__ = 'keys'
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id'), unique=True)
    public_key = Column(Text, nullable=False)
    fingerprint = Column(String(128), nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow)

class SignalingMessage(Base):
    __tablename__ = 'signaling_messages'
    id = Column(Integer, primary_key=True, index=True)
    from_user_id = Column(Integer, ForeignKey('users.id'))
    to_user_id = Column(Integer, ForeignKey('users.id'))
    msg_type = Column(String(32), nullable=False)
    data = Column(Text, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)
    is_handled = Column(Boolean, default=False)

class FriendRequest(Base):
    __tablename__ = 'friend_requests'
    id = Column(Integer, primary_key=True, index=True)
    from_user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    to_user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    status = Column(String(16), default='pending')  # pending, accepted, rejected
    message = Column(Text, nullable=True)  # 申请消息
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)
    
    # 关系
    from_user = relationship('User', foreign_keys=[from_user_id])
    to_user = relationship('User', foreign_keys=[to_user_id])

class SecurityEvent(Base):
    __tablename__ = 'security_events'
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    event_type = Column(String(64), nullable=False)
    detail = Column(Text, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow)

class UserKeys(Base):
    __tablename__ = 'user_keys'
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id'), unique=True, nullable=False)
    public_key = Column(Text, nullable=False)  # 用户公钥
    private_key_encrypted = Column(Text, nullable=False)  # 用户私钥（加密存储）
    key_version = Column(Integer, default=1)  # 密钥版本
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)
    
    # 关系
    user = relationship('User', foreign_keys=[user_id])

class UserProfile(Base):
    __tablename__ = 'user_profiles'
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id'), unique=True, nullable=False)
    birthday = Column(String(32), nullable=True)  # 生日
    age = Column(Integer, nullable=True)  # 年龄
    gender = Column(String(16), nullable=True)  # 性别
    hobbies = Column(Text, nullable=True)  # 爱好
    signature = Column(Text, nullable=True)  # 个性签名
    display_name = Column(String(64), nullable=True)  # 显示名称（用户名修改）
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)
    
    # 关系
    user = relationship('User', foreign_keys=[user_id])

class SessionKey(Base):
    __tablename__ = 'session_keys'
    id = Column(Integer, primary_key=True, index=True)
    user1_id = Column(Integer, ForeignKey('users.id'), nullable=False)  # 用户1 ID
    user2_id = Column(Integer, ForeignKey('users.id'), nullable=False)  # 用户2 ID
    session_key_encrypted = Column(Text, nullable=False)  # 对称会话密钥（用用户1公钥加密）
    session_key_encrypted_for_user2 = Column(Text, nullable=True)  # 对称会话密钥（用用户2公钥加密）
    key_version = Column(Integer, default=1)  # 密钥版本
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)
    
    # 关系
    user1 = relationship('User', foreign_keys=[user1_id])
    user2 = relationship('User', foreign_keys=[user2_id])