from fastapi import APIRouter, UploadFile, File, Form, Depends, HTTPException
from sqlalchemy.orm import Session
from db.database import SessionLocal
from schemas.message import MessageCreate, Message
from services import message_service
from core.security import get_current_user
from schemas.user import UserOut
import os
import uuid
from datetime import datetime
from typing import Optional

router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# 确保上传目录存在
# 使用绝对路径，基于当前文件位置
# 从 /backend/app/api/v1/endpoints/upload.py 到 /backend/app/static/images
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
UPLOAD_BASE_DIR = os.path.join(BASE_DIR, "static", "images")
os.makedirs(UPLOAD_BASE_DIR, exist_ok=True)
# 图片存储目录

@router.post("/upload/image", response_model=Message)
async def upload_image(
    file: UploadFile = File(...),
    to_id: int = Form(...),
    content: str = Form(default=""),
    encrypted: bool = Form(default=True),
    method: str = Form(default="Server"),
    destroy_after: Optional[int] = Form(default=None),
    hidding_message: Optional[str] = Form(default=None),
    current_user: UserOut = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # 验证文件是否存在
    if not file or not file.filename:
        raise HTTPException(status_code=400, detail="请选择要上传的文件")
    
    # 验证文件类型
    allowed_types = ['image/jpeg', 'image/jpg', 'image/png', 'image/gif', 'image/webp']
    if not file.content_type or file.content_type not in allowed_types:
        raise HTTPException(status_code=400, detail="只支持 JPEG、PNG、GIF、WebP 格式的图片文件")
    
    # 验证文件扩展名
    allowed_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.webp']
    file_extension = os.path.splitext(file.filename)[1].lower()
    if file_extension not in allowed_extensions:
        raise HTTPException(status_code=400, detail="文件扩展名不支持")
    
    # 读取文件内容并验证大小
    try:
        content_data = await file.read()
        file_size = len(content_data)
        
        # 验证文件大小 (10MB)
        max_size = 10 * 1024 * 1024
        if file_size > max_size:
            raise HTTPException(status_code=400, detail=f"文件大小不能超过{max_size // (1024*1024)}MB")
        
        # 验证文件不为空
        if file_size == 0:
            raise HTTPException(status_code=400, detail="文件内容为空")
            
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=500, detail=f"文件读取失败: {str(e)}")
    
    # 为当前用户创建专用目录
    user_upload_dir = os.path.join(UPLOAD_BASE_DIR, str(current_user.id))
    os.makedirs(user_upload_dir, exist_ok=True)
    
    # 生成唯一文件名
    unique_filename = f"{uuid.uuid4()}{file_extension}"
    file_path = os.path.join(user_upload_dir, unique_filename)
    
    # 用于数据库存储的相对路径（包含用户ID目录）
    relative_file_path = f"{current_user.id}/{unique_filename}"
    
    # 保存文件
    try:
        with open(file_path, "wb") as buffer:
            buffer.write(content_data)
        
        # 验证文件是否成功保存
        if not os.path.exists(file_path) or os.path.getsize(file_path) != file_size:
            raise Exception("文件保存验证失败")
            
    except Exception as e:
        # 清理可能创建的文件
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
            except:
                pass
        raise HTTPException(status_code=500, detail=f"文件保存失败: {str(e)}")
    
    # 保存消息到数据库
    try:
        # 保存图片消息到数据库（图片消息始终保存）
        message = message_service.send_message(
            db=db,
            from_id=int(current_user.id),
            to_id=to_id,
            content=content or f"发送了图片: {file.filename}",
            message_type="image",
            file_path=relative_file_path,  # 保存包含用户ID的相对路径
            file_name=file.filename,
            encrypted=encrypted,
            method=method,
            destroy_after=destroy_after,
            hidding_message=hidding_message,
            recipient_online=False  # 确保图片消息始终保存到数据库
        )
        
        # 图片上传成功
        return message
        
    except Exception as e:
        # 如果数据库保存失败，删除已上传的文件
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
            except:
                pass
        # 数据库保存失败，已删除文件
        raise HTTPException(status_code=500, detail=f"保存消息失败: {str(e)}")

@router.get("/images/{filename:path}")
async def get_image(filename: str):
    """获取图片文件"""
    from fastapi.responses import FileResponse
    import re
    
    # 验证文件名格式（防止路径遍历攻击）
    # 支持两种格式：user_id/uuid.ext 或 uuid.ext
    if not re.match(r'^(?:\d+/)?[a-f0-9-]+\.(jpg|jpeg|png|gif|webp)$', filename, re.IGNORECASE):
        raise HTTPException(status_code=400, detail="无效的文件名格式")
    
    # 构建文件路径（支持用户ID子目录）
    if "/" in filename:
        # 新格式：user_id/filename
        file_path = os.path.join(UPLOAD_BASE_DIR, filename)
    else:
        # 兼容旧格式：直接在images目录下
        file_path = os.path.join(UPLOAD_BASE_DIR, filename)
    
    # 安全检查：确保文件路径在允许的目录内
    real_upload_dir = os.path.realpath(UPLOAD_BASE_DIR)
    real_file_path = os.path.realpath(file_path)
    if not real_file_path.startswith(real_upload_dir):
        raise HTTPException(status_code=403, detail="访问被拒绝")
    
    # 检查文件是否存在
    if not os.path.exists(file_path):
        # 文件不存在
        raise HTTPException(status_code=404, detail="图片不存在")
    
    # 检查是否为文件（不是目录）
    if not os.path.isfile(file_path):
        raise HTTPException(status_code=404, detail="图片不存在")
    
    try:
        # 获取文件的MIME类型
        import mimetypes
        content_type, _ = mimetypes.guess_type(file_path)
        if not content_type or not content_type.startswith('image/'):
            content_type = 'image/jpeg'  # 默认类型
        
        # 返回图片
        return FileResponse(
            file_path,
            media_type=content_type,
            headers={
                "Cache-Control": "public, max-age=3600",  # 缓存1小时
                "Content-Disposition": f"inline; filename={filename}"
            }
        )
    except Exception as e:
        # 返回图片失败
        raise HTTPException(status_code=500, detail="图片读取失败")