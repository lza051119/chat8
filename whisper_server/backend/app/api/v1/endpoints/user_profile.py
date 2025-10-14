from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from ...deps import get_db
from ....schemas.user import UserProfileCreate, UserProfileUpdate, UserProfileOut, UserProfileWithUserInfo, ResponseModel, UserOut
from ....services.user_profile_service import UserProfileService
from ....core.security import get_current_user
from typing import Optional

router = APIRouter()

@router.get("/profile", response_model=UserProfileOut)
async def get_user_profile(
    current_user: UserOut = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取当前用户的个人信息"""
    try:
        user_id = int(current_user.id)
        profile = UserProfileService.get_user_profile(db, user_id)
        
        if not profile:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="用户个人信息不存在"
            )
        
        return profile
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取个人信息失败: {str(e)}"
        )

@router.get("/profile/{user_id}", response_model=UserProfileWithUserInfo)
async def get_user_profile_by_id(
    user_id: int,
    current_user: UserOut = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取指定用户的个人信息"""
    try:
        profile = UserProfileService.get_user_profile(db, user_id)
        
        if not profile:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="用户个人信息不存在"
            )
        
        return profile
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取个人信息失败: {str(e)}"
        )

@router.post("/profile", response_model=ResponseModel)
async def create_user_profile(
    profile_data: UserProfileCreate,
    current_user: UserOut = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """创建用户个人信息"""
    try:
        user_id = int(current_user.id)
        profile = UserProfileService.create_user_profile(db, user_id, profile_data)
        
        return ResponseModel(
            success=True,
            message="个人信息创建成功",
            data={"profile_id": profile.id}
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"创建个人信息失败: {str(e)}"
        )

@router.put("/profile", response_model=ResponseModel)
async def update_user_profile(
    profile_data: UserProfileUpdate,
    current_user: UserOut = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """更新用户个人信息"""
    try:
        user_id = int(current_user.id)
        profile = UserProfileService.update_user_profile(db, user_id, profile_data)
        
        return ResponseModel(
            success=True,
            message="个人信息更新成功",
            data={"profile_id": profile.id}
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"更新个人信息失败: {str(e)}"
        )

@router.delete("/profile", response_model=ResponseModel)
async def delete_user_profile(
    current_user: UserOut = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """删除用户个人信息"""
    try:
        user_id = int(current_user.id)
        success = UserProfileService.delete_user_profile(db, user_id)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="用户个人信息不存在"
            )
        
        return ResponseModel(
            success=True,
            message="个人信息删除成功"
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"删除个人信息失败: {str(e)}"
        )