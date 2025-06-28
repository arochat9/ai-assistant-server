from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


class UserBase(BaseModel):
    user_id: str  # Phone number or email
    name: str


class UserCreate(UserBase):
    pass


class UserResponse(UserBase):
    model_config = ConfigDict(from_attributes=True)

    created_at: datetime
    updated_at: Optional[datetime] = None
