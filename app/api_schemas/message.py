from datetime import datetime
from typing import Any, Dict, Optional

from pydantic import BaseModel

from app.models.message import MessageStatus


class MessageBase(BaseModel):
    text_content: str
    user_id: str
    chat_id: str

class MessageCreate(MessageBase):
    message_id: str  # Primary key, must be unique
    user_info_struct: Optional[Dict[str, Any]] = None
    is_spam: Optional[bool] = False
    replied_to_fk: Optional[str] = None

class MessageUpdate(BaseModel):
    text_content: Optional[str] = None
    status: Optional[MessageStatus] = None
    is_spam: Optional[bool] = None
    user_info_struct: Optional[Dict[str, Any]] = None

class MessageResponse(MessageBase):
    message_id: str
    status: MessageStatus
    user_info_struct: Optional[Dict[str, Any]] = None
    is_spam: bool
    replied_to_fk: Optional[str] = None
    text_character_count: int
    time_received: datetime

    class Config:
        from_attributes = True
