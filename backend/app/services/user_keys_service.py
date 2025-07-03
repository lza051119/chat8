from sqlalchemy.orm import Session
from app.db.models import UserKeys
from app.db.database import SessionLocal
from fastapi import HTTPException
from datetime import datetime
import json
import os
import base64
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.fernet import Fernet

class UserKeysService:
    """用户密钥管理服务"""
    
    @staticmethod
    def _generate_encryption_key(password: str, salt: bytes) -> bytes:
        """基于密码生成加密密钥"""
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        return base64.urlsafe_b64encode(kdf.derive(password.encode()))
    
    @staticmethod
    def _encrypt_private_key(private_key_pem: str, password: str) -> tuple[str, str]:
        """加密私钥"""
        salt = os.urandom(16)
        key = UserKeysService._generate_encryption_key(password, salt)
        fernet = Fernet(key)
        encrypted_key = fernet.encrypt(private_key_pem.encode())
        return base64.b64encode(encrypted_key).decode(), base64.b64encode(salt).decode()
    
    @staticmethod
    def _decrypt_private_key(encrypted_key: str, salt: str, password: str) -> str:
        """解密私钥"""
        salt_bytes = base64.b64decode(salt.encode())
        key = UserKeysService._generate_encryption_key(password, salt_bytes)
        fernet = Fernet(key)
        encrypted_key_bytes = base64.b64decode(encrypted_key.encode())
        return fernet.decrypt(encrypted_key_bytes).decode()
    
    @staticmethod
    def generate_rsa_keypair() -> tuple[str, str]:
        """生成RSA密钥对"""
        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048,
        )
        
        # 序列化私钥
        private_pem = private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()
        ).decode()
        
        # 序列化公钥
        public_key = private_key.public_key()
        public_pem = public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        ).decode()
        
        return public_pem, private_pem
    
    @staticmethod
    def create_user_keys(user_id: int, password: str) -> dict:
        """为用户创建并存储密钥"""
        db: Session = SessionLocal()
        try:
            # 检查用户是否已有密钥
            existing_keys = db.query(UserKeys).filter(UserKeys.user_id == user_id).first()
            if existing_keys:
                db.close()
                raise HTTPException(status_code=400, detail="用户密钥已存在")
            
            # 生成RSA密钥对
            public_key, private_key = UserKeysService.generate_rsa_keypair()
            
            # 加密私钥
            encrypted_private_key, salt = UserKeysService._encrypt_private_key(private_key, password)
            
            # 生成Signal协议相关密钥（模拟）
            identity_public, identity_private = UserKeysService.generate_rsa_keypair()
            signed_prekey_public, signed_prekey_private = UserKeysService.generate_rsa_keypair()
            
            # 加密Signal私钥
            encrypted_identity_private, identity_salt = UserKeysService._encrypt_private_key(identity_private, password)
            encrypted_signed_prekey_private, signed_salt = UserKeysService._encrypt_private_key(signed_prekey_private, password)
            
            # 生成一次性预密钥（模拟）
            one_time_prekeys = []
            for i in range(10):  # 生成10个一次性预密钥
                otk_public, otk_private = UserKeysService.generate_rsa_keypair()
                encrypted_otk_private, otk_salt = UserKeysService._encrypt_private_key(otk_private, password)
                one_time_prekeys.append({
                    "id": i,
                    "public_key": otk_public,
                    "private_key": encrypted_otk_private,
                    "salt": otk_salt
                })
            
            # 创建密钥记录
            user_keys = UserKeys(
                user_id=user_id,
                public_key=public_key,
                private_key_encrypted=f"{encrypted_private_key}:{salt}",  # 格式：加密密钥:盐值
                identity_key=identity_public,  # 简化为只存储公钥
                signed_prekey=signed_prekey_public,  # 简化为只存储公钥
                onetime_prekeys=json.dumps(one_time_prekeys),
                key_version=1,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            
            db.add(user_keys)
            db.commit()
            db.refresh(user_keys)
            
            return {
                "success": True,
                "message": "密钥创建成功",
                "data": {
                    "user_id": user_id,
                    "public_key": public_key,
                    "identity_key": identity_public,
                    "signed_prekey": signed_prekey_public,
                    "one_time_prekeys_count": len(one_time_prekeys),
                    "key_version": user_keys.key_version,
                    "created_at": user_keys.created_at
                }
            }
            
        except Exception as e:
            db.rollback()
            raise HTTPException(status_code=500, detail=f"密钥创建失败: {str(e)}")
        finally:
            db.close()
    
    @staticmethod
    def get_user_keys(user_id: int) -> dict:
        """获取用户密钥信息（仅公钥部分）"""
        db: Session = SessionLocal()
        try:
            user_keys = db.query(UserKeys).filter(UserKeys.user_id == user_id).first()
            if not user_keys:
                return {
                    "success": False,
                    "message": "用户密钥不存在"
                }
            
            # 解析一次性预密钥
            one_time_prekeys = json.loads(user_keys.onetime_prekeys) if user_keys.onetime_prekeys else []
            public_one_time_prekeys = [{
                "id": otk["id"],
                "public_key": otk["public_key"]
            } for otk in one_time_prekeys]
            
            return {
                "success": True,
                "data": {
                    "user_id": user_id,
                    "public_key": user_keys.public_key,
                    "identity_key": user_keys.identity_key,
                    "signed_prekey": user_keys.signed_prekey,
                    "one_time_prekeys": public_one_time_prekeys,
                    "key_version": user_keys.key_version,
                    "updated_at": user_keys.updated_at
                }
            }
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"获取密钥失败: {str(e)}")
        finally:
            db.close()
    
    @staticmethod
    def get_user_private_keys(user_id: int, password: str) -> dict:
        """获取用户私钥（需要密码验证）"""
        db: Session = SessionLocal()
        try:
            user_keys = db.query(UserKeys).filter(UserKeys.user_id == user_id).first()
            if not user_keys:
                return {
                    "success": False,
                    "message": "用户密钥不存在"
                }
            
            # 解密私钥
            try:
                encrypted_private_key, salt = user_keys.private_key_encrypted.split(":")
                private_key = UserKeysService._decrypt_private_key(encrypted_private_key, salt, password)
                
                encrypted_identity_private, identity_salt = user_keys.identity_key_private.split(":")
                identity_private = UserKeysService._decrypt_private_key(encrypted_identity_private, identity_salt, password)
                
                encrypted_signed_prekey_private, signed_salt = user_keys.signed_prekey_private.split(":")
                signed_prekey_private = UserKeysService._decrypt_private_key(encrypted_signed_prekey_private, signed_salt, password)
                
                # 解密一次性预密钥
                one_time_prekeys = json.loads(user_keys.one_time_prekeys) if user_keys.one_time_prekeys else []
                decrypted_one_time_prekeys = []
                for otk in one_time_prekeys:
                    decrypted_otk_private = UserKeysService._decrypt_private_key(otk["private_key"], otk["salt"], password)
                    decrypted_one_time_prekeys.append({
                        "id": otk["id"],
                        "public_key": otk["public_key"],
                        "private_key": decrypted_otk_private
                    })
                
                return {
                    "success": True,
                    "data": {
                        "user_id": user_id,
                        "public_key": user_keys.public_key,
                        "private_key": private_key,
                        "identity_key_public": user_keys.identity_key_public,
                        "identity_key_private": identity_private,
                        "signed_prekey_public": user_keys.signed_prekey_public,
                        "signed_prekey_private": signed_prekey_private,
                        "signed_prekey_signature": user_keys.signed_prekey_signature,
                        "one_time_prekeys": decrypted_one_time_prekeys,
                        "key_version": user_keys.key_version
                    }
                }
                
            except Exception as decrypt_error:
                return {
                    "success": False,
                    "message": "密码错误或密钥解密失败"
                }
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"获取私钥失败: {str(e)}")
        finally:
            db.close()
    
    @staticmethod
    def update_user_keys(user_id: int, password: str) -> dict:
        """更新用户密钥"""
        db: Session = SessionLocal()
        try:
            user_keys = db.query(UserKeys).filter(UserKeys.user_id == user_id).first()
            if not user_keys:
                return {
                    "success": False,
                    "message": "用户密钥不存在"
                }
            
            # 生成新的密钥对
            public_key, private_key = UserKeysService.generate_rsa_keypair()
            encrypted_private_key, salt = UserKeysService._encrypt_private_key(private_key, password)
            
            # 更新密钥
            user_keys.public_key = public_key
            user_keys.private_key = f"{encrypted_private_key}:{salt}"
            user_keys.key_version += 1
            user_keys.updated_at = datetime.utcnow()
            
            db.commit()
            
            return {
                "success": True,
                "message": "密钥更新成功",
                "data": {
                    "user_id": user_id,
                    "public_key": public_key,
                    "key_version": user_keys.key_version,
                    "updated_at": user_keys.updated_at
                }
            }
            
        except Exception as e:
            db.rollback()
            raise HTTPException(status_code=500, detail=f"密钥更新失败: {str(e)}")
        finally:
            db.close()
    
    @staticmethod
    def delete_user_keys(user_id: int) -> dict:
        """删除用户密钥"""
        db: Session = SessionLocal()
        try:
            user_keys = db.query(UserKeys).filter(UserKeys.user_id == user_id).first()
            if not user_keys:
                return {
                    "success": False,
                    "message": "用户密钥不存在"
                }
            
            db.delete(user_keys)
            db.commit()
            
            return {
                "success": True,
                "message": "密钥删除成功"
            }
            
        except Exception as e:
            db.rollback()
            raise HTTPException(status_code=500, detail=f"密钥删除失败: {str(e)}")
        finally:
            db.close()