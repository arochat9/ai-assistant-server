from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class UserBase(BaseModel):
    user_id: str  # Phone number or email
    name: str


class UserCreate(UserBase):
    pass


class UserResponse(UserBase):
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True
