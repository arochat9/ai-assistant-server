from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict

from app.models.message import MessageStatus


class ChatMember(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    user_id: str
    name: Optional[str] = None
    is_sender: bool


class MessageBase(BaseModel):
    text_content: str
    chat_id: str


class MessageCreate(MessageBase):
    message_id: str  # Primary key, must be unique
    chat_members_struct: List[ChatMember]
    chat_display_name: Optional[str] = None
    is_spam: Optional[bool] = False
    replied_to_fk: Optional[str] = None


class MessageResponse(MessageBase):
    model_config = ConfigDict(from_attributes=True)

    message_id: str
    status: MessageStatus
    user_id: str  # Sender ID
    sender_name: Optional[str] = None  # Sender name
    chat_members_struct: List[ChatMember]
    is_spam: bool
    replied_to_fk: Optional[str] = None
    text_character_count: int
    time_received: datetime
