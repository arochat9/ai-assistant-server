from sqlalchemy import Column, String, Text, DateTime, Boolean, Enum, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import UUID
import enum
import uuid

from app.core.database import Base

class TaskStatus(enum.Enum):
    OPEN = "open"
    CLOSED = "closed"
    BACKLOGGED = "backlogged"

class TaskOrEvent(enum.Enum):
    TASK = "task"
    EVENT = "event"

class TaskType(enum.Enum):
    FUN = "fun"
    TEXT_RESPONSE = "text_response"
    CHORE = "chore"
    ERRAND = "errand"

class Task(Base):
    __tablename__ = "tasks"
    
    task_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    task_name = Column(String, nullable=False)  # Short name for task
    task_context = Column(Text, nullable=True)  # Longer version of task
    status = Column(Enum(TaskStatus), default=TaskStatus.OPEN)
    task_or_event = Column(Enum(TaskOrEvent), nullable=False)
    
    # Event times
    event_start_time = Column(DateTime(timezone=True), nullable=True)  # Start time for events
    event_end_time = Column(DateTime(timezone=True), nullable=True)  # End time for events
    
    # Task times
    task_due_time = Column(DateTime(timezone=True), nullable=True)  # Due time for tasks
    task_type = Column(Enum(TaskType), nullable=True)  # Type of task
    
    # Completion tracking
    completed_at = Column(DateTime(timezone=True), nullable=True)  # When completed
    
    # Source tracking
    source_message_id = Column(String, ForeignKey("messages.message_id"), nullable=True)
    created_by_agent = Column(Boolean, default=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    source_message = relationship("Message", backref="generated_tasks")
