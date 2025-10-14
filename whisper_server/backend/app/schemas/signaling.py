from pydantic import BaseModel

class OfferRequest(BaseModel):
    targetUserId: int
    offer: dict

class AnswerRequest(BaseModel):
    targetUserId: int
    offer: dict 