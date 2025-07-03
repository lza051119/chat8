from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from app.core.security import get_current_user
from app.schemas.user import UserOut
from app.db.database import SessionLocal
from app.db.models import User as UserModel
import os

router = APIRouter()

UPLOAD_DIR = "static/avatars"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@router.post('/avatar/upload')
def upload_avatar(file: UploadFile = File(...), current_user: UserOut = Depends(get_current_user)):
    ext = os.path.splitext(file.filename)[-1].lower()
    if ext not in ['.jpg', '.jpeg', '.png', '.gif']:
        raise HTTPException(status_code=400, detail="仅支持jpg/png/gif格式")
    filename = f"user_{current_user.id}{ext}"
    file_path = os.path.join(UPLOAD_DIR, filename)
    with open(file_path, "wb") as f:
        f.write(file.file.read())
    # 更新数据库
    db = SessionLocal()
    user = db.query(User).filter(User.id == int(current_user.id)).first()
    if user:
        user.avatar = f"/static/avatars/{filename}"
        db.commit()
    db.close()
    return {"success": True, "avatarUrl": f"/static/avatars/{filename}"}