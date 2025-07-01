from fastapi import APIRouter, Depends
from core.security import get_current_user
from schemas.user import UserOut
from services import signaling_service

router = APIRouter()

@router.post('/signaling/offer')
def send_offer(targetUserId: int, offer: dict, current_user: UserOut = Depends(get_current_user)):
    signaling_service.save_signaling_message(int(current_user.id), targetUserId, 'offer', offer)
    return {"success": True, "message": "Offer发送成功"}

@router.post('/signaling/answer')
def send_answer(targetUserId: int, answer: dict, current_user: UserOut = Depends(get_current_user)):
    signaling_service.save_signaling_message(int(current_user.id), targetUserId, 'answer', answer)
    return {"success": True, "message": "Answer发送成功"}

@router.post('/signaling/ice-candidate')
def send_ice(targetUserId: int, candidate: dict, current_user: UserOut = Depends(get_current_user)):
    signaling_service.save_signaling_message(int(current_user.id), targetUserId, 'ice-candidate', candidate)
    return {"success": True, "message": "ICE Candidate发送成功"}

@router.get('/signaling/pending')
def get_pending(current_user: UserOut = Depends(get_current_user)):
    return {"success": True, "data": signaling_service.get_pending_signaling(int(current_user.id))} 