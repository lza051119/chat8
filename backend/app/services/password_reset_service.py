from sqlalchemy.orm import Session
from app.db.database import SessionLocal
from app.db.models import User
from app.core.security import hash_password
from app.core.email_config import send_verification_email
from app.services.verification_service import VerificationCodeService
from fastapi import HTTPException
from typing import Dict, Any
from datetime import datetime

class PasswordResetService:
    """密码重置服务"""
    
    @staticmethod
    async def send_reset_code(email: str) -> Dict[str, Any]:
        """发送密码重置验证码"""
        db: Session = SessionLocal()
        try:
            # 检查用户是否存在
            user = db.query(User).filter(User.email == email).first()
            if not user:
                raise HTTPException(status_code=404, detail="该邮箱未注册")
            
            # 检查是否已有有效验证码
            if VerificationCodeService.has_valid_code(email):
                remaining_time = VerificationCodeService.get_remaining_time(email)
                raise HTTPException(
                    status_code=429, 
                    detail=f"验证码已发送，请等待 {remaining_time} 秒后重试"
                )
            
            # 生成验证码
            code = VerificationCodeService.generate_code()
            
            # 存储验证码
            VerificationCodeService.store_code(email, code)
            
            # 发送邮件
            await send_verification_email(email, code, user.username)
            
            return {
                "success": True,
                "message": "验证码已发送到您的邮箱",
                "data": {
                    "email": email,
                    "expire_minutes": 10
                }
            }
            
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"发送验证码失败: {str(e)}")
        finally:
            db.close()
    
    @staticmethod
    def verify_reset_code(email: str, code: str) -> Dict[str, Any]:
        """验证重置验证码"""
        db: Session = SessionLocal()
        try:
            # 检查用户是否存在
            user = db.query(User).filter(User.email == email).first()
            if not user:
                raise HTTPException(status_code=404, detail="该邮箱未注册")
            
            # 验证验证码（不删除，为后续重置密码保留）
            if not VerificationCodeService.verify_code_without_delete(email, code):
                raise HTTPException(status_code=400, detail="验证码错误或已过期")
            
            return {
                "success": True,
                "message": "验证码验证成功",
                "data": {
                    "email": email,
                    "verified": True
                }
            }
            
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"验证失败: {str(e)}")
        finally:
            db.close()
    
    @staticmethod
    def reset_password(email: str, code: str, new_password: str) -> Dict[str, Any]:
        """重置密码"""
        db: Session = SessionLocal()
        try:
            # 检查用户是否存在
            user = db.query(User).filter(User.email == email).first()
            if not user:
                raise HTTPException(status_code=404, detail="该邮箱未注册")
            
            # 验证验证码（不删除）
            if not VerificationCodeService.verify_code_without_delete(email, code):
                raise HTTPException(status_code=400, detail="验证码错误或已过期")
            
            # 更新密码（哈希处理）
            hashed_password = hash_password(new_password)
            user.password_hash = hashed_password
            db.commit()
            
            # 密码重置成功后删除验证码
            VerificationCodeService.clear_code(email)
            
            return {
                "success": True,
                "message": "密码重置成功",
                "data": {
                    "email": email,
                    "reset_time": datetime.now().isoformat()
                }
            }
            
        except HTTPException:
            raise
        except Exception as e:
            db.rollback()
            raise HTTPException(status_code=500, detail=f"密码重置失败: {str(e)}")
        finally:
            db.close()