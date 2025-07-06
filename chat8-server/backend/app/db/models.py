from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey
# 兼容所有SQLAlchemy版本的declarative_base导入
try:
    from sqlalchemy.orm import declarative_base, relationship
except ImportError:
    from sqlalchemy.ext.declarative import declarative_base
    from sqlalchemy.orm import relationship
from datetime import datetime, timezone, timedelta

# 中国时区
CHINA_TZ = timezone(timedelta(hours=8))

def china_now():
    return datetime.now(CHINA_TZ)

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(32), unique=True, index=True, nullable=False)
    email = Column(String(128), unique=True, index=True, nullable=False)
    password_hash = Column(String(128), nullable=False)
    avatar = Column(String(256), nullable=True)
    created_at = Column(DateTime, default=china_now)
    last_seen = Column(DateTime, default=china_now)
    status = Column(String(16), default='offline')
    friends = relationship('Friend', back_populates='user', cascade='all, delete-orphan', foreign_keys='Friend.user_id')

class Friend(Base):
    __tablename__ = 'friends'
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    friend_id = Column(Integer, ForeignKey('users.id'))
    created_at = Column(DateTime, default=china_now)
    user = relationship('User', foreign_keys=[user_id], back_populates='friends')
    friend_user = relationship('User', foreign_keys=[friend_id])

class Message(Base):
    __tablename__ = 'messages'
    id = Column(Integer, primary_key=True, index=True)
    from_id = Column(Integer, ForeignKey('users.id'))
    to_id = Column(Integer, ForeignKey('users.id'))
    encrypted_content = Column(Text, nullable=False)  # 不透明的加密数据
    message_type = Column(String(16), default='text')  # text, image, file, voice, video
    file_path = Column(String(512), nullable=True)  # 文件路径（用于图片和文件消息）
    file_name = Column(String(256), nullable=True)  # 原始文件名
    timestamp = Column(DateTime, default=china_now)
    delivered = Column(Boolean, default=False)  # 投递状态

class SignalingMessage(Base):
    __tablename__ = 'signaling_messages'
    id = Column(Integer, primary_key=True, index=True)
    from_user_id = Column(Integer, ForeignKey('users.id'))
    to_user_id = Column(Integer, ForeignKey('users.id'))
    msg_type = Column(String(32), nullable=False)
    data = Column(Text, nullable=False)
    timestamp = Column(DateTime, default=china_now)
    is_handled = Column(Boolean, default=False)

class FriendRequest(Base):
    __tablename__ = 'friend_requests'
    id = Column(Integer, primary_key=True, index=True)
    from_user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    to_user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    status = Column(String(16), default='pending')  # pending, accepted, rejected
    message = Column(Text, nullable=True)  # 申请消息
    created_at = Column(DateTime, default=china_now)
    updated_at = Column(DateTime, default=china_now)
    
    # 关系
    from_user = relationship('User', foreign_keys=[from_user_id])
    to_user = relationship('User', foreign_keys=[to_user_id])

class SecurityEvent(Base):
    __tablename__ = 'security_events'
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    event_type = Column(String(64), nullable=False)
    detail = Column(Text, nullable=True)
    timestamp = Column(DateTime, default=china_now)

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
    created_at = Column(DateTime, default=china_now)
    updated_at = Column(DateTime, default=china_now)
    
    # 关系
    user = relationship('User', foreign_keys=[user_id])