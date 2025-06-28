from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


class ChatBase(BaseModel):
    chat_id: str
    chat_display_name: Optional[str] = None


class ChatCreate(ChatBase):
    user_ids: list[str]  # Array of user IDs to add to chat


class ChatResponse(ChatBase):
    model_config = ConfigDict(from_attributes=True)

    created_at: datetime
    updated_at: Optional[datetime] = None
