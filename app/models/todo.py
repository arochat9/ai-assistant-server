import enum
import uuid

from sqlalchemy import Column, DateTime, Enum, ForeignKey, String, Table, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

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


# Association table for many-to-many relationship between tasks and messages
task_message_association = Table(
    "task_message_association",
    Base.metadata,
    Column(
        "task_id", UUID(as_uuid=True), ForeignKey("tasks.task_id"), primary_key=True
    ),
    Column("message_id", String, ForeignKey("messages.message_id"), primary_key=True),
)


class Task(Base):
    __tablename__ = "tasks"

    task_id = Column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True
    )
    task_name = Column(String, nullable=False)  # Short name for task
    task_context = Column(Text, nullable=True)  # Longer version of task
    status = Column(Enum(TaskStatus), default=TaskStatus.OPEN)
    task_or_event = Column(Enum(TaskOrEvent), nullable=False)

    # Event times
    event_start_time = Column(
        DateTime(timezone=True), nullable=True
    )  # Start time for events
    event_end_time = Column(
        DateTime(timezone=True), nullable=True
    )  # End time for events

    # Task times
    task_due_time = Column(DateTime(timezone=True), nullable=True)  # Due time for tasks
    task_type = Column(Enum(TaskType), nullable=True)  # Type of task

    # Completion tracking
    completed_at = Column(DateTime(timezone=True), nullable=True)  # When completed

    # Source tracking
    source_message_id = Column(String, ForeignKey("messages.message_id"), nullable=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    source_message = relationship("Message", backref="generated_tasks")
    messages = relationship(
        "Message",
        secondary=task_message_association,
        back_populates="tasks",
        lazy="dynamic",
    )
