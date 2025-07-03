from sqlalchemy.orm import Session
from db import models
from datetime import datetime
from sqlalchemy import or_

def get_friends(db: Session, user_id: int, page: int = 1, limit: int = 50):
    # 使用关联查询获取好友信息
    from sqlalchemy.orm import joinedload
    query = db.query(models.Friend).options(joinedload(models.Friend.friend_user)).filter(models.Friend.user_id == user_id)
    total = query.count()
    friends = query.offset((page-1)*limit).limit(limit).all()
    
    # 构建好友列表
    friend_list = []
    for friend in friends:
        if friend.friend_user:
            friend_data = {
                'id': friend.friend_user.id,
                'username': friend.friend_user.username,
                'email': friend.friend_user.email,
                'avatar': friend.friend_user.avatar,
                'status': friend.friend_user.status,
                'last_seen': friend.friend_user.last_seen,
                'created_at': friend.created_at,
                'online': friend.friend_user.status == 'online'
            }
            friend_list.append(friend_data)
    
    return {
        "items": friend_list,
        "pagination": {
            "page": page,
            "limit": limit,
            "total": total,
            "totalPages": (total + limit - 1) // limit
        }
    }

def add_friend(db: Session, user_id: int, friend_id: int):
    # 检查friend_id对应的用户是否存在
    friend_user = db.query(models.User).filter(models.User.id == friend_id).first()
    if not friend_user:
        return None
    
    # 检查是否已是好友
    exists = db.query(models.Friend).filter_by(user_id=user_id, friend_id=friend_id).first()
    if exists:
        return None
    
    # 检查是否试图添加自己为好友
    if user_id == friend_id:
        return None
        
    friend = models.Friend(user_id=user_id, friend_id=friend_id, created_at=datetime.utcnow())
    db.add(friend)
    db.commit()
    db.refresh(friend)
    return friend

def remove_friend(db: Session, user_id: int, friend_id: int):
    # 删除双向好友关系
    friend1 = db.query(models.Friend).filter_by(user_id=user_id, friend_id=friend_id).first()
    friend2 = db.query(models.Friend).filter_by(user_id=friend_id, friend_id=user_id).first()
    
    deleted = False
    if friend1:
        db.delete(friend1)
        deleted = True
    if friend2:
        db.delete(friend2)
        deleted = True
    
    # 同时删除相关的好友申请记录（包括已处理的）
    friend_requests = db.query(models.FriendRequest).filter(
        or_(
            (models.FriendRequest.from_user_id == user_id) & (models.FriendRequest.to_user_id == friend_id),
            (models.FriendRequest.from_user_id == friend_id) & (models.FriendRequest.to_user_id == user_id)
        )
    ).all()
    
    for request in friend_requests:
        db.delete(request)
        deleted = True
    
    if deleted:
        db.commit()
        return True
    return False

# 好友申请相关函数
def send_friend_request(db: Session, from_user_id: int, to_user_id: int, message: str = None):
    """发送好友申请"""
    # 检查目标用户是否存在
    target_user = db.query(models.User).filter(models.User.id == to_user_id).first()
    if not target_user:
        return None
    
    # 检查是否试图添加自己
    if from_user_id == to_user_id:
        return None
    
    # 检查是否已是好友（双向检查）
    existing_friend = db.query(models.Friend).filter(
        or_(
            (models.Friend.user_id == from_user_id) & (models.Friend.friend_id == to_user_id),
            (models.Friend.user_id == to_user_id) & (models.Friend.friend_id == from_user_id)
        )
    ).first()
    if existing_friend:
        return None
    
    # 检查是否已有待处理的申请（只检查pending状态）
    existing_request = db.query(models.FriendRequest).filter(
        or_(
            (models.FriendRequest.from_user_id == from_user_id) & (models.FriendRequest.to_user_id == to_user_id),
            (models.FriendRequest.from_user_id == to_user_id) & (models.FriendRequest.to_user_id == from_user_id)
        ),
        models.FriendRequest.status == 'pending'
    ).first()
    if existing_request:
        return None
    
    # 清理之前已处理的申请记录（可选，允许重新申请）
    old_requests = db.query(models.FriendRequest).filter(
        or_(
            (models.FriendRequest.from_user_id == from_user_id) & (models.FriendRequest.to_user_id == to_user_id),
            (models.FriendRequest.from_user_id == to_user_id) & (models.FriendRequest.to_user_id == from_user_id)
        ),
        models.FriendRequest.status.in_(['accepted', 'rejected'])
    ).all()
    
    for old_request in old_requests:
        db.delete(old_request)
    
    # 创建好友申请
    friend_request = models.FriendRequest(
        from_user_id=from_user_id,
        to_user_id=to_user_id,
        message=message,
        status='pending'
    )
    db.add(friend_request)
    db.commit()
    db.refresh(friend_request)
    return friend_request

def get_friend_requests(db: Session, user_id: int, request_type: str = 'received'):
    """获取好友申请列表"""
    if request_type == 'received':
        # 获取收到的申请
        requests = db.query(models.FriendRequest).filter(
            models.FriendRequest.to_user_id == user_id,
            models.FriendRequest.status == 'pending'
        ).all()
    elif request_type == 'sent':
        # 获取发送的申请
        requests = db.query(models.FriendRequest).filter(
            models.FriendRequest.from_user_id == user_id,
            models.FriendRequest.status == 'pending'
        ).all()
    else:
        return []
    
    # 添加用户信息
    result = []
    for req in requests:
        req_dict = {
            'id': req.id,
            'from_user_id': req.from_user_id,
            'to_user_id': req.to_user_id,
            'status': req.status,
            'message': req.message,
            'created_at': req.created_at,
            'from_user_username': req.from_user.username,
            'from_user_avatar': req.from_user.avatar
        }
        result.append(req_dict)
    
    return result

def handle_friend_request(db: Session, request_id: int, user_id: int, action: str):
    """处理好友申请"""
    # 获取申请记录
    friend_request = db.query(models.FriendRequest).filter(
        models.FriendRequest.id == request_id,
        models.FriendRequest.to_user_id == user_id,
        models.FriendRequest.status == 'pending'
    ).first()
    
    if not friend_request:
        return None
    
    if action == 'accept':
        # 同意申请，创建双向好友关系
        friend1 = models.Friend(
            user_id=friend_request.from_user_id,
            friend_id=friend_request.to_user_id
        )
        friend2 = models.Friend(
            user_id=friend_request.to_user_id,
            friend_id=friend_request.from_user_id
        )
        db.add(friend1)
        db.add(friend2)
        friend_request.status = 'accepted'
    elif action == 'reject':
        # 拒绝申请
        friend_request.status = 'rejected'
    else:
        return None
    
    friend_request.updated_at = datetime.utcnow()
    db.commit()
    return friend_request