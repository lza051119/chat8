from fastapi import APIRouter, Depends
from app.core.security import get_current_user
from app.schemas.user import UserOut
from app.services import signaling_service
from app.schemas.signaling import OfferRequest, AnswerRequest
from pydantic import BaseModel

router = APIRouter()

class IceCandidateRequest(BaseModel):
    targetUserId: int
    candidate: dict

@router.post('/signaling/offer')
def send_offer(body: OfferRequest, current_user: UserOut = Depends(get_current_user)):
    signaling_service.save_signaling_message(int(current_user.id), body.targetUserId, 'offer', body.offer)
    return {"success": True, "message": "Offer发送成功"}

@router.post('/signaling/answer')
def send_answer(body: AnswerRequest, current_user: UserOut = Depends(get_current_user)):
    signaling_service.save_signaling_message(int(current_user.id), body.targetUserId, 'answer', body.offer)
    return {"success": True, "message": "Answer发送成功"}

@router.post('/signaling/ice-candidate')
def send_ice(body: IceCandidateRequest, current_user: UserOut = Depends(get_current_user)):
    signaling_service.save_signaling_message(int(current_user.id), body.targetUserId, 'ice-candidate', body.candidate)
    return {"success": True, "message": "ICE Candidate发送成功"}

@router.get('/signaling/pending')
def get_pending(current_user: UserOut = Depends(get_current_user)):
    return {"success": True, "data": signaling_service.get_pending_signaling(int(current_user.id))}