from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy.ext.asyncio import AsyncSession
from ...deps import get_db
from ....core.security import get_current_user
from ....schemas.user import UserOut
from ....services import security_event_service

router = APIRouter()

@router.get('/security/events')
def get_security_events(limit: int = 20, current_user: UserOut = Depends(get_current_user), db: Session = Depends(get_db)):
    return {"success": True, "data": security_event_service.get_events(db, int(current_user.id), limit)}