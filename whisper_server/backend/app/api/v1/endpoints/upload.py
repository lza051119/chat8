from fastapi import APIRouter, UploadFile, File, Form, Depends, HTTPException
from sqlalchemy.orm import Session
from ....db.database import SessionLocal
from ....schemas.message import MessageCreate, Message
from ....services import message_service
from ....core.security import get_current_user
from ....schemas.user import UserOut
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
# 从 /backend/app/api/v1/endpoints/upload.py 到 /backend/app/static
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
IMAGE_UPLOAD_DIR = os.path.join(BASE_DIR, "static", "images")
FILE_UPLOAD_DIR = os.path.join(BASE_DIR, "static", "files")
os.makedirs(IMAGE_UPLOAD_DIR, exist_ok=True)
os.makedirs(FILE_UPLOAD_DIR, exist_ok=True)
# 图片和文件存储目录

@router.post("/upload/image", response_model=Message)
async def upload_image(
    file: UploadFile = File(...),
    to_id: int = Form(...),
    encrypted_content: str = Form(...),
    message_type: str = Form(default="image"),
    current_user: UserOut = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return await upload_file_internal(
        file=file,
        to_id=to_id,
        encrypted_content=encrypted_content,
        message_type=message_type,
        current_user=current_user,
        db=db,
        file_type="image"
    )

@router.post("/upload/file", response_model=Message)
async def upload_file(
    file: UploadFile = File(...),
    to_id: int = Form(...),
    encrypted_content: str = Form(...),
    message_type: str = Form(default="file"),
    current_user: UserOut = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return await upload_file_internal(
        file=file,
        to_id=to_id,
        encrypted_content=encrypted_content,
        message_type=message_type,
        current_user=current_user,
        db=db,
        file_type=message_type
    )

async def upload_file_internal(
    file: UploadFile,
    to_id: int,
    encrypted_content: str,
    message_type: str,
    current_user: UserOut,
    db: Session,
    file_type: str
):
    # 验证文件是否存在
    if not file or not file.filename:
        raise HTTPException(status_code=400, detail="请选择要上传的文件")
    
    # 获取文件扩展名
    file_extension = os.path.splitext(file.filename)[1].lower()
    
    # 根据文件类型进行验证
    if file_type == "image":
        # 验证图片文件类型
        allowed_types = ['image/jpeg', 'image/jpg', 'image/png', 'image/gif', 'image/webp']
        if not file.content_type or file.content_type not in allowed_types:
            raise HTTPException(status_code=400, detail="只支持 JPEG、PNG、GIF、WebP 格式的图片文件")
        
        # 验证图片文件扩展名
        allowed_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.webp']
        if file_extension not in allowed_extensions:
            raise HTTPException(status_code=400, detail="文件扩展名不支持")
    else:
        # 通用文件类型验证
        # 禁止上传可执行文件和脚本文件
        forbidden_extensions = ['.exe', '.bat', '.cmd', '.sh', '.php', '.asp', '.aspx', '.js', '.vbs', '.ps1']
        if file_extension in forbidden_extensions:
            raise HTTPException(status_code=400, detail="不允许上传可执行文件或脚本文件")
        
        # 文件大小限制更严格
        max_size = 20 * 1024 * 1024  # 20MB
        if file.size and file.size > max_size:
            raise HTTPException(status_code=400, detail=f"文件大小不能超过{max_size // (1024*1024)}MB")
    
    # 读取文件内容并验证大小
    try:
        content_data = await file.read()
        file_size = len(content_data)
        
        # 根据文件类型设置大小限制
        if file_type == "image":
            max_size = 10 * 1024 * 1024  # 图片10MB
        else:
            max_size = 20 * 1024 * 1024  # 其他文件20MB
            
        if file_size > max_size:
            raise HTTPException(status_code=400, detail=f"文件大小不能超过{max_size // (1024*1024)}MB")
        
        # 验证文件不为空
        if file_size == 0:
            raise HTTPException(status_code=400, detail="文件内容为空")
            
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=500, detail=f"文件读取失败: {str(e)}")
    
    # 根据文件类型选择存储目录
    if file_type == "image":
        base_upload_dir = IMAGE_UPLOAD_DIR
    else:
        base_upload_dir = FILE_UPLOAD_DIR
    
    # 为当前用户创建专用目录
    user_upload_dir = os.path.join(base_upload_dir, str(current_user.id))
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
        # 保存文件消息到数据库（文件消息始终保存）
        message = message_service.send_message(
            db=db,
            from_id=int(current_user.id),
            to_id=to_id,
            encrypted_content=encrypted_content,
            message_type=message_type,
            file_path=relative_file_path,  # 保存包含用户ID的相对路径
            file_name=file.filename,
            recipient_online=False  # 确保文件消息始终保存到数据库
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
    import logging
    
    # 禁用此请求的访问日志
    uvicorn_logger = logging.getLogger("uvicorn.access")
    original_level = uvicorn_logger.level
    uvicorn_logger.setLevel(logging.WARNING)
    
    try:
        # 验证文件名格式（防止路径遍历攻击）
        # 支持两种格式：user_id/uuid.ext 或 uuid.ext
        if not re.match(r'^(?:\d+/)?[a-f0-9-]+\.(jpg|jpeg|png|gif|webp)$', filename, re.IGNORECASE):
            raise HTTPException(status_code=400, detail="无效的文件名格式")
        
        # 构建文件路径（支持用户ID子目录）
        if "/" in filename:
            # 新格式：user_id/filename
            file_path = os.path.join(IMAGE_UPLOAD_DIR, filename)
        else:
            # 兼容旧格式：直接在images目录下
            file_path = os.path.join(IMAGE_UPLOAD_DIR, filename)
        
        # 安全检查：确保文件路径在允许的目录内
        real_upload_dir = os.path.realpath(IMAGE_UPLOAD_DIR)
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
    finally:
        # 恢复日志级别
        uvicorn_logger.setLevel(original_level)

@router.get("/files/{filename:path}")
async def get_file(filename: str):
    """获取文件"""
    from fastapi.responses import FileResponse
    import re
    import logging
    
    # 禁用此请求的访问日志
    uvicorn_logger = logging.getLogger("uvicorn.access")
    original_level = uvicorn_logger.level
    uvicorn_logger.setLevel(logging.WARNING)
    
    try:
        # 验证文件名格式（防止路径遍历攻击）
        # 支持两种格式：user_id/uuid.ext 或 uuid.ext
        if not re.match(r'^(?:\d+/)?[a-f0-9-]+\.[a-zA-Z0-9]+$', filename, re.IGNORECASE):
            raise HTTPException(status_code=400, detail="无效的文件名格式")
        
        # 构建文件路径（支持用户ID子目录）
        if "/" in filename:
            # 新格式：user_id/filename
            file_path = os.path.join(FILE_UPLOAD_DIR, filename)
        else:
            # 兼容旧格式：直接在images目录下
            file_path = os.path.join(FILE_UPLOAD_DIR, filename)
        
        # 安全检查：确保文件路径在允许的目录内
        real_upload_dir = os.path.realpath(FILE_UPLOAD_DIR)
        real_file_path = os.path.realpath(file_path)
        if not real_file_path.startswith(real_upload_dir):
            raise HTTPException(status_code=403, detail="访问被拒绝")
        
        # 检查文件是否存在
        if not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail="文件不存在")
        
        # 检查是否为文件（不是目录）
        if not os.path.isfile(file_path):
            raise HTTPException(status_code=404, detail="文件不存在")
        
        # 获取文件的MIME类型
        import mimetypes
        content_type, _ = mimetypes.guess_type(file_path)
        if not content_type:
            content_type = 'application/octet-stream'  # 默认二进制类型
        
        # 获取原始文件名（从路径中提取）
        original_filename = os.path.basename(filename)
        
        # 返回文件
        return FileResponse(
            file_path,
            media_type=content_type,
            headers={
                "Cache-Control": "public, max-age=3600",  # 缓存1小时
                "Content-Disposition": f"attachment; filename={original_filename}"
            }
        )
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=500, detail="文件读取失败")
    finally:
        # 恢复日志级别
        uvicorn_logger.setLevel(original_level)