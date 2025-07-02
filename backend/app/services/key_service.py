from sqlalchemy.orm import Session
from app.db import models
from datetime import datetime

def upload_public_key(db: Session, user_id: int, public_key: str, fingerprint: str):
    key = db.query(models.Key).filter_by(user_id=user_id).first()
    if key:
        key.public_key = public_key
        key.fingerprint = fingerprint
        key.updated_at = datetime.utcnow()
    else:
        key = models.Key(user_id=user_id, public_key=public_key, fingerprint=fingerprint, updated_at=datetime.utcnow())
        db.add(key)
    db.commit()
    db.refresh(key)
    return key

def get_public_key(db: Session, user_id: int):
    return db.query(models.Key).filter_by(user_id=user_id).first()

def get_all_public_keys(db: Session, user_ids: list):
    return db.query(models.Key).filter(models.Key.user_id.in_(user_ids)).all()

def verify_fingerprint(db: Session, user_id: int, fingerprint: str):
    key = db.query(models.Key).filter_by(user_id=user_id).first()
    if not key:
        return False, "公钥不存在"
    return key.fingerprint == fingerprint, None if key.fingerprint == fingerprint else "指纹不匹配"