from sqlalchemy.orm import Session
from app.db.database import SessionLocal
from app.db.models import UserProfile
from app.schemas.user import UserProfileCreate, UserProfileUpdate
from typing import Optional
from datetime import datetime

class UserProfileService:
    """用户个人信息服务类"""
    
    @staticmethod
    def get_user_profile(user_id: int) -> Optional[UserProfile]:
        """获取用户个人信息"""
        db: Session = SessionLocal()
        try:
            return db.query(UserProfile).filter(UserProfile.user_id == user_id).first()
        finally:
            db.close()
    
    @staticmethod
    def create_user_profile(user_id: int, profile_data: UserProfileCreate) -> UserProfile:
        """创建用户个人信息"""
        db: Session = SessionLocal()
        try:
            # 检查是否已存在个人信息
            existing_profile = db.query(UserProfile).filter(UserProfile.user_id == user_id).first()
            if existing_profile:
                raise ValueError("用户个人信息已存在")
            
            db_profile = UserProfile(
                user_id=user_id,
                birthday=profile_data.birthday,
                age=profile_data.age,
                gender=profile_data.gender,
                hobbies=profile_data.hobbies,
                signature=profile_data.signature,
                display_name=profile_data.display_name
            )
            
            db.add(db_profile)
            db.commit()
            db.refresh(db_profile)
            return db_profile
        finally:
            db.close()
    
    @staticmethod
    def update_user_profile(user_id: int, profile_data: UserProfileUpdate) -> Optional[UserProfile]:
        """更新用户个人信息"""
        db: Session = SessionLocal()
        try:
            db_profile = db.query(UserProfile).filter(UserProfile.user_id == user_id).first()
            if not db_profile:
                # 如果不存在，则创建新的个人信息
                return UserProfileService.create_user_profile(user_id, UserProfileCreate(**profile_data.dict()))
            
            # 更新字段
            update_data = profile_data.dict(exclude_unset=True)
            for field, value in update_data.items():
                if hasattr(db_profile, field):
                    setattr(db_profile, field, value)
            
            db_profile.updated_at = datetime.utcnow()
            db.commit()
            db.refresh(db_profile)
            return db_profile
        finally:
            db.close()
    
    @staticmethod
    def delete_user_profile(user_id: int) -> bool:
        """删除用户个人信息"""
        db: Session = SessionLocal()
        try:
            db_profile = db.query(UserProfile).filter(UserProfile.user_id == user_id).first()
            if db_profile:
                db.delete(db_profile)
                db.commit()
                return True
            return False
        finally:
            db.close()