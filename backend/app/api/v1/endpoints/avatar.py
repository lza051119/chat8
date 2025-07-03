from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from fastapi.responses import FileResponse
from app.core.security import get_current_user
from app.schemas.user import UserOut, ResponseModel
from app.db.database import SessionLocal
from app.db.models import User as UserModel
import os
import uuid
from pathlib import Path

router = APIRouter()

# 使用绝对路径存储头像
UPLOAD_DIR = os.path.abspath("static/avatars")
os.makedirs(UPLOAD_DIR, exist_ok=True)

@router.post('/avatar/upload', response_model=ResponseModel)
def upload_avatar(file: UploadFile = File(...), current_user: UserOut = Depends(get_current_user)):
    """上传用户头像"""
    try:
        # 验证文件格式
        ext = os.path.splitext(file.filename)[-1].lower()
        if ext not in ['.jpg', '.jpeg', '.png', '.gif', '.webp']:
            raise HTTPException(status_code=400, detail="仅支持jpg/jpeg/png/gif/webp格式")
        
        # 验证文件大小 (5MB)
        file_content = file.file.read()
        if len(file_content) > 5 * 1024 * 1024:
            raise HTTPException(status_code=400, detail="文件大小不能超过5MB")
        
        # 生成唯一文件名
        unique_filename = f"user_{current_user.id}_{uuid.uuid4().hex[:8]}{ext}"
        file_path = os.path.join(UPLOAD_DIR, unique_filename)
        
        # 保存文件
        with open(file_path, "wb") as f:
            f.write(file_content)
        
        # 更新数据库 - 存储相对路径用于URL访问
        db = SessionLocal()
        try:
            user = db.query(UserModel).filter(UserModel.id == int(current_user.id)).first()
            if user:
                # 删除旧头像文件
                if user.avatar:
                    # 如果存储的是相对路径，需要转换为绝对路径来删除文件
                    if user.avatar.startswith('/api/v1/avatar/'):
                        old_filename = user.avatar.replace('/api/v1/avatar/', '')
                        old_file_path = os.path.join(UPLOAD_DIR, old_filename)
                    else:
                        old_file_path = user.avatar  # 兼容旧的绝对路径格式
                    
                    if os.path.exists(old_file_path):
                        try:
                            os.remove(old_file_path)
                        except:
                            pass  # 忽略删除失败
                
                # 存储相对URL路径，便于前端访问
                user.avatar = f"/api/v1/avatar/{unique_filename}"
                db.commit()
                db.refresh(user)
            else:
                raise HTTPException(status_code=404, detail="用户不存在")
        finally:
            db.close()
        
        return ResponseModel(
            success=True,
            message="头像上传成功",
            data={
                "avatarUrl": f"/api/v1/avatar/{unique_filename}",
                "filename": unique_filename
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"上传失败: {str(e)}")

@router.get('/avatar/{filename}')
def get_avatar(filename: str):
    """获取头像文件"""
    try:
        # 验证文件名安全性
        if '..' in filename or '/' in filename or '\\' in filename:
            raise HTTPException(status_code=400, detail="无效的文件名")
        
        file_path = os.path.join(UPLOAD_DIR, filename)
        
        if not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail="头像文件不存在")
        
        return FileResponse(
            path=file_path,
            media_type="image/*",
            headers={"Cache-Control": "public, max-age=3600"}
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取头像失败: {str(e)}")

@router.delete('/avatar', response_model=ResponseModel)
def delete_avatar(current_user: UserOut = Depends(get_current_user)):
    """删除用户头像"""
    try:
        db = SessionLocal()
        try:
            user = db.query(UserModel).filter(UserModel.id == int(current_user.id)).first()
            if user and user.avatar:
                # 删除文件
                if user.avatar.startswith('/api/v1/avatar/'):
                    filename = user.avatar.replace('/api/v1/avatar/', '')
                    file_path = os.path.join(UPLOAD_DIR, filename)
                else:
                    file_path = user.avatar  # 兼容旧的绝对路径格式
                
                if os.path.exists(file_path):
                    try:
                        os.remove(file_path)
                    except:
                        pass  # 忽略删除失败
                
                # 清空数据库记录
                user.avatar = None
                db.commit()
        finally:
            db.close()
        
        return ResponseModel(
            success=True,
            message="头像删除成功"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"删除头像失败: {str(e)}")