from datetime import datetime
from typing import Optional
from pydantic import BaseModel
from uuid import UUID

from app.models.todo import TaskStatus, TaskOrEvent, TaskType

class TaskBase(BaseModel):
    task_name: str
    task_context: Optional[str] = None
    task_or_event: TaskOrEvent

class TaskCreate(TaskBase):
    task_type: Optional[TaskType] = None
    event_start_time: Optional[datetime] = None
    event_end_time: Optional[datetime] = None
    task_due_time: Optional[datetime] = None
    source_message_id: Optional[str] = None

class TaskUpdate(BaseModel):
    task_name: Optional[str] = None
    task_context: Optional[str] = None
    status: Optional[TaskStatus] = None
    task_type: Optional[TaskType] = None
    event_start_time: Optional[datetime] = None
    event_end_time: Optional[datetime] = None
    task_due_time: Optional[datetime] = None
    completed_at: Optional[datetime] = None

class TaskResponse(TaskBase):
    task_id: UUID
    status: TaskStatus
    task_type: Optional[TaskType] = None
    event_start_time: Optional[datetime] = None
    event_end_time: Optional[datetime] = None
    task_due_time: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    source_message_id: Optional[str] = None
    created_by_agent: bool
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True
