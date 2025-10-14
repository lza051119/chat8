from pydantic import BaseModel, Field
from datetime import datetime

class KeyBase(BaseModel):
    public_key: str = Field(..., alias="publicKey")

class KeyCreate(KeyBase):
    pass

class Key(KeyBase):
    id: int = Field(..., alias="id")
    user_id: int = Field(..., alias="userId")
    fingerprint: str = Field(..., alias="fingerprint")
    updated_at: datetime = Field(..., alias="updatedAt")

    class Config:
        from_attributes = True
        populate_by_name = True