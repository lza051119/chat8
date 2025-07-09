from sqlalchemy.orm import Session, joinedload
from ..db import models
from datetime import datetime
from sqlalchemy import or_, select, update, delete
from sqlalchemy.ext.asyncio import AsyncSession
from ..repositories.friend_repository import friend_repository


async def get_friends(db: AsyncSession, user_id: int, page: int = 1, limit: int = 50):
    # 使用关联查询获取好友信息
    stmt = select(models.Friend).options(joinedload(models.Friend.friend_user)).filter(models.Friend.user_id == user_id)
    result = await db.execute(stmt)
    friends = result.scalars().all()
    
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
    
    total = len(friend_list) # 注意：这里没有高效的方法来获取分页前的总数
    
    return {
        "items": friend_list[(page-1)*limit : page*limit],
        "pagination": {
            "page": page,
            "limit": limit,
            "total": total,
            "totalPages": (total + limit - 1) // limit
        }
    }

async def add_friend(db: AsyncSession, user_id: int, friend_id: int):
    # 检查friend_id对应的用户是否存在
    result = await db.execute(select(models.User).filter(models.User.id == friend_id))
    friend_user = result.scalars().first()
    if not friend_user:
        return None
    
    # 检查是否已是好友
    result = await db.execute(select(models.Friend).filter_by(user_id=user_id, friend_id=friend_id))
    exists = result.scalars().first()
    if exists:
        return None
    
    # 检查是否试图添加自己为好友
    if user_id == friend_id:
        return None
        
    friend = models.Friend(user_id=user_id, friend_id=friend_id, created_at=datetime.utcnow())
    db.add(friend)
    await db.commit()
    await db.refresh(friend)
    return friend

async def remove_friend(db: AsyncSession, user_id: int, friend_id: int):
    # 删除双向好友关系
    deleted = False
    
    # 删除 user -> friend
    stmt1 = delete(models.Friend).where(models.Friend.user_id == user_id, models.Friend.friend_id == friend_id)
    result1 = await db.execute(stmt1)
    if result1.rowcount > 0:
        deleted = True
        
    # 删除 friend -> user
    stmt2 = delete(models.Friend).where(models.Friend.user_id == friend_id, models.Friend.friend_id == user_id)
    result2 = await db.execute(stmt2)
    if result2.rowcount > 0:
        deleted = True
    
    # 同时删除相关的好友申请记录
    stmt_req = delete(models.FriendRequest).where(
        or_(
            (models.FriendRequest.from_user_id == user_id) & (models.FriendRequest.to_user_id == friend_id),
            (models.FriendRequest.from_user_id == friend_id) & (models.FriendRequest.to_user_id == user_id)
        )
    )
    await db.execute(stmt_req)

    if deleted:
        await db.commit()
        return True
    return False

# 好友申请相关函数
async def send_friend_request(db: AsyncSession, from_user_id: int, to_user_id: int, message: str = None):
    """发送好友申请"""
    # 检查目标用户是否存在
    result = await db.execute(select(models.User).filter(models.User.id == to_user_id))
    target_user = result.scalars().first()
    if not target_user:
        return {"success": False, "message": "用户不存在"}
    
    # 检查是否试图添加自己
    if from_user_id == to_user_id:
        return {"success": False, "message": "不能添加自己为好友"}
    
    # 检查是否已是好友（双向检查）
    result = await db.execute(select(models.Friend).filter(
        or_(
            (models.Friend.user_id == from_user_id) & (models.Friend.friend_id == to_user_id),
            (models.Friend.user_id == to_user_id) & (models.Friend.friend_id == from_user_id)
        )
    ))
    existing_friend = result.scalars().first()
    if existing_friend:
        return {"success": False, "message": "已经是好友"}
    
    # 检查是否已有待处理的申请
    result = await db.execute(select(models.FriendRequest).filter(
        or_(
            (models.FriendRequest.from_user_id == from_user_id) & (models.FriendRequest.to_user_id == to_user_id),
            (models.FriendRequest.from_user_id == to_user_id) & (models.FriendRequest.to_user_id == from_user_id)
        ),
        models.FriendRequest.status == 'pending'
    ))
    existing_request = result.scalars().first()
    if existing_request:
        return {"success": False, "message": "已有待处理的好友申请"}
    
    # 清理之前已处理的申请记录
    stmt_del = delete(models.FriendRequest).where(
        or_(
            (models.FriendRequest.from_user_id == from_user_id) & (models.FriendRequest.to_user_id == to_user_id),
            (models.FriendRequest.from_user_id == to_user_id) & (models.FriendRequest.to_user_id == from_user_id)
        ),
        models.FriendRequest.status.in_(['accepted', 'rejected'])
    )
    await db.execute(stmt_del)
    
    # 创建好友申请
    friend_request = models.FriendRequest(
        from_user_id=from_user_id,
        to_user_id=to_user_id,
        message=message,
        status='pending'
    )
    db.add(friend_request)
    await db.commit()
    await db.refresh(friend_request)
    return {"success": True, "message": "好友申请已发送", "data": {"request_id": friend_request.id}}

async def get_friend_requests(db: AsyncSession, user_id: int, request_type: str = 'received'):
    """获取好友申请列表"""
    if request_type == 'received':
        stmt = select(models.FriendRequest).filter(
            models.FriendRequest.to_user_id == user_id,
            models.FriendRequest.status == 'pending'
        )
    elif request_type == 'sent':
        stmt = select(models.FriendRequest).filter(
            models.FriendRequest.from_user_id == user_id,
            models.FriendRequest.status == 'pending'
        )
    else:
        return []
    
    result = await db.execute(stmt.options(joinedload(models.FriendRequest.from_user)))
    requests = result.scalars().all()
    
    # 添加用户信息
    result_list = []
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
        result_list.append(req_dict)
    
    return result_list

async def handle_friend_request(db: AsyncSession, request_id: int, user_id: int, action: str):
    """处理好友申请"""
    # 获取申请记录
    result = await db.execute(select(models.FriendRequest).filter(
        models.FriendRequest.id == request_id,
        models.FriendRequest.to_user_id == user_id,
        models.FriendRequest.status == 'pending'
    ))
    friend_request = result.scalars().first()
    
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
        friend_request.status = 'rejected'
    else:
        return None
    
    friend_request.updated_at = datetime.utcnow()
    await db.commit()
    return friend_request

class FriendService:
    async def get_friends(self, db: AsyncSession, user_id: int):
        return await get_friends(db, user_id=user_id)

    async def send_friend_request(self, db: AsyncSession, from_user_id: int, to_user_id: int, message: str = None):
        return await send_friend_request(db, from_user_id, to_user_id, message)

    async def remove_friend(self, db: AsyncSession, user_id: int, friend_id: int):
        return await remove_friend(db, user_id, friend_id)

    async def get_friend_requests(self, db: AsyncSession, user_id: int, request_type: str = 'received'):
        return await get_friend_requests(db, user_id, request_type)
        
    async def handle_friend_request(self, db: AsyncSession, request_id: int, user_id: int, action: str):
        return await handle_friend_request(db, request_id, user_id, action)

friend_service = FriendService()