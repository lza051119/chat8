from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.core.security import get_current_user
from app.services.encryption_service import encryption_service
from app.db import models
from typing import Dict, Any

router = APIRouter()

@router.get("/public-key/{user_id}")
def get_user_public_key(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """获取指定用户的公钥"""
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    
    if not user.public_key:
        raise HTTPException(status_code=404, detail="用户未设置公钥")
    
    return {
        "success": True,
        "data": {
            "user_id": user_id,
            "public_key": user.public_key
        }
    }

@router.get("/prekey-bundle/{user_id}")
def get_user_prekey_bundle(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """获取指定用户的预密钥包"""
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    
    try:
        prekey_bundle = encryption_service.get_user_prekey_bundle(user_id)
        if not prekey_bundle.get('success'):
            raise HTTPException(status_code=404, detail="无法获取用户预密钥包")
        
        return {
            "success": True,
            "data": prekey_bundle['prekey_bundle']
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取预密钥包失败: {str(e)}")

@router.post("/establish-session")
def establish_encryption_session(
    target_user_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """与指定用户建立加密会话"""
    try:
        result = encryption_service.establish_session(current_user.id, target_user_id)
        if not result.get('success'):
            raise HTTPException(status_code=400, detail=f"建立会话失败: {result.get('error')}")
        
        return {
            "success": True,
            "message": "加密会话建立成功",
            "data": {
                "session_established": True
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"建立会话失败: {str(e)}")

@router.get("/my-keys")
def get_my_encryption_keys(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """获取当前用户的加密密钥信息"""
    try:
        keys_info = encryption_service.get_user_keys_info(current_user.id)
        if not keys_info.get('success'):
            raise HTTPException(status_code=404, detail="无法获取密钥信息")
        
        return {
            "success": True,
            "data": keys_info['keys_info']
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取密钥信息失败: {str(e)}")

@router.post("/regenerate-keys")
def regenerate_encryption_keys(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """重新生成用户的加密密钥"""
    try:
        result = encryption_service.setup_user_encryption(current_user.id)
        if not result.get('success'):
            raise HTTPException(status_code=500, detail=f"重新生成密钥失败: {result.get('error')}")
        
        return {
            "success": True,
            "message": "密钥重新生成成功",
            "data": {
                "public_key": result['public_key'],
                "registration_id": result['registration_id']
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"重新生成密钥失败: {str(e)}")