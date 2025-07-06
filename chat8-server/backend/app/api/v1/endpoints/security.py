from fastapi import APIRouter, Depends
from app.core.security import get_current_user
from app.schemas.user import UserOut
from app.services import security_event_service

router = APIRouter()

@router.get('/security/events')
def get_security_events(limit: int = 20, current_user: UserOut = Depends(get_current_user)):
    return {"success": True, "data": security_event_service.get_events(int(current_user.id), limit)}