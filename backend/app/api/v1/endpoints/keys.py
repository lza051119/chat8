from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.database import SessionLocal
from app.schemas.key import Key, KeyCreate
from app.services import key_service
from typing import List
from app.core.security import get_current_user
from app.schemas.user import UserOut
from pydantic import BaseModel

router = APIRouter()

class FingerprintCheck(BaseModel):
    user_id: int
    fingerprint: str

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/keys/public", response_model=Key)
def upload_key(key: KeyCreate, fingerprint: str, current_user: UserOut = Depends(get_current_user), db: Session = Depends(get_db)):
    db_key = key_service.upload_public_key(db, int(current_user.id), key.public_key, fingerprint)
    return Key.model_validate(db_key)

@router.get("/keys/public/{user_id}", response_model=Key)
def get_key(user_id: int, current_user: UserOut = Depends(get_current_user), db: Session = Depends(get_db)):
    res = key_service.get_public_key(db, user_id)
    if not res:
        raise HTTPException(status_code=404, detail="公钥不存在")
    return Key.model_validate(res)

@router.get("/keys/public", response_model=List[Key])
def get_keys(user_ids: str = None, current_user: UserOut = Depends(get_current_user), db: Session = Depends(get_db)):
    if not user_ids:
        friends = friend_service.get_friends(db, int(current_user.id), 1, 1000)
        id_list = [f.id for f in friends['items']]
    else:
        id_list = [int(uid) for uid in user_ids.split(",") if uid]
    db_keys = key_service.get_all_public_keys(db, id_list)
    return [Key.model_validate(k) for k in db_keys]

@router.post("/keys/verify-fingerprint")
def verify_fingerprint(body: FingerprintCheck, current_user: UserOut = Depends(get_current_user), db: Session = Depends(get_db)):
    ok, err = key_service.verify_fingerprint(db, body.user_id, body.fingerprint)
    if not ok:
        raise HTTPException(status_code=400, detail=err)
    return {"success": True, "message": "指纹校验通过"}