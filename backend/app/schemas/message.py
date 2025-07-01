from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional

class MessageBase(BaseModel):
    to_id: int = Field(..., alias="to")
    content: str
    encrypted: bool = True
    method: str = 'Server'
    destroy_after: Optional[int] = Field(None, alias="destroyAfter")

class MessageCreate(MessageBase):
    pass

class Message(MessageBase):
    id: int = Field(..., alias="id")
    from_id: int = Field(..., alias="from")
    timestamp: datetime = Field(..., alias="timestamp")

    class Config:
        from_attributes = True
        populate_by_name = True