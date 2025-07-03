from fastapi import APIRouter, Depends, HTTPException, status
from app.schemas.user import UserOut, ResponseModel
from app.services.user_keys_service import UserKeysService
from app.core.security import get_current_user
from pydantic import BaseModel
from typing import Optional

router = APIRouter()

class GetPrivateKeysRequest(BaseModel):
    password: str

class UpdateKeysRequest(BaseModel):
    password: str

@router.get("/keys", response_model=ResponseModel)
async def get_user_keys(
    current_user: UserOut = Depends(get_current_user)
):
    """获取用户公钥信息"""
    try:
        user_id = int(current_user.id)
        result = UserKeysService.get_user_keys(user_id)
        
        if not result.get('success'):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=result.get('message', '密钥不存在')
            )
        
        return ResponseModel(
            success=True,
            message="获取密钥成功",
            data=result['data']
        )
        
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="无效的用户ID"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取密钥失败: {str(e)}"
        )

@router.post("/keys/private", response_model=ResponseModel)
async def get_user_private_keys(
    request: GetPrivateKeysRequest,
    current_user: UserOut = Depends(get_current_user)
):
    """获取用户私钥信息（需要密码验证）"""
    try:
        user_id = int(current_user.id)
        result = UserKeysService.get_user_private_keys(user_id, request.password)
        
        if not result.get('success'):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=result.get('message', '密码错误或密钥不存在')
            )
        
        return ResponseModel(
            success=True,
            message="获取私钥成功",
            data=result['data']
        )
        
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="无效的用户ID"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取私钥失败: {str(e)}"
        )

@router.put("/keys", response_model=ResponseModel)
async def update_user_keys(
    request: UpdateKeysRequest,
    current_user: UserOut = Depends(get_current_user)
):
    """更新用户密钥"""
    try:
        user_id = int(current_user.id)
        result = UserKeysService.update_user_keys(user_id, request.password)
        
        if not result.get('success'):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result.get('message', '密钥更新失败')
            )
        
        return ResponseModel(
            success=True,
            message="密钥更新成功",
            data=result['data']
        )
        
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="无效的用户ID"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"密钥更新失败: {str(e)}"
        )

@router.delete("/keys", response_model=ResponseModel)
async def delete_user_keys(
    current_user: UserOut = Depends(get_current_user)
):
    """删除用户密钥"""
    try:
        user_id = int(current_user.id)
        result = UserKeysService.delete_user_keys(user_id)
        
        if not result.get('success'):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result.get('message', '密钥删除失败')
            )
        
        return ResponseModel(
            success=True,
            message="密钥删除成功",
            data=None
        )
        
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="无效的用户ID"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"密钥删除失败: {str(e)}"
        )

@router.get("/keys/{user_id}", response_model=ResponseModel)
async def get_other_user_keys(
    user_id: int,
    current_user: UserOut = Depends(get_current_user)
):
    """获取其他用户的公钥信息（用于加密通信）"""
    try:
        result = UserKeysService.get_user_keys(user_id)
        
        if not result.get('success'):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=result.get('message', '用户密钥不存在')
            )
        
        # 只返回公钥信息，不返回私钥相关内容
        public_data = {
            "user_id": result['data']['user_id'],
            "public_key": result['data']['public_key'],
            "identity_key_public": result['data']['identity_key_public'],
            "signed_prekey_public": result['data']['signed_prekey_public'],
            "signed_prekey_signature": result['data']['signed_prekey_signature'],
            "one_time_prekeys": result['data']['one_time_prekeys'],
            "key_version": result['data']['key_version'],
            "updated_at": result['data']['updated_at']
        }
        
        return ResponseModel(
            success=True,
            message="获取用户公钥成功",
            data=public_data
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取用户公钥失败: {str(e)}"
        )