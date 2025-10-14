from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional

class MessageBase(BaseModel):
    to_id: int = Field(..., alias="to")
    encrypted_content: str = Field(..., alias="encryptedContent")  # 不透明的加密数据
    message_type: str = Field(default='text', alias="messageType")  # text, image, file, voice, video

class MessageCreate(MessageBase):
    pass

class Message(MessageBase):
    id: int = Field(..., alias="id")
    from_id: int = Field(..., alias="from")
    file_path: Optional[str] = Field(None, alias="filePath")
    file_name: Optional[str] = Field(None, alias="fileName")
    timestamp: datetime = Field(..., alias="timestamp")
    delivered: bool = Field(default=False, alias="delivered")

    class Config:
        from_attributes = True
        populate_by_name = True