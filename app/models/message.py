import enum

from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import Base


class MessageStatus(enum.Enum):
    UNPROCESSED = "unprocessed"
    READY_FOR_AGENT = "ready_for_agent"
    AGENT_PROCESSING = "agent_processing"
    PROCESSED = "processed"


class Message(Base):
    __tablename__ = "messages"

    message_id = Column(
        String, primary_key=True, index=True
    )  # Primary key, must be unique
    text_content = Column(Text, nullable=False)  # Actual text body
    time_received = Column(
        DateTime(timezone=True), server_default=func.now()
    )  # Time message was received
    user_id = Column(
        String, ForeignKey("users.user_id"), nullable=False
    )  # Sender ID (phone/email)
    sender_name = Column(String, nullable=True)  # Sender name
    chat_members_struct = Column(JSON, nullable=True)  # Denormalized sender info
    chat_id = Column(String, ForeignKey("chats.chat_id"), nullable=False)  # Chat ID
    is_spam = Column(Boolean, default=False, nullable=False)  # Spam flag
    replied_to_fk = Column(
        String, ForeignKey("messages.message_id"), nullable=True
    )  # Reply reference
    status = Column(
        Enum(MessageStatus), default=MessageStatus.UNPROCESSED, nullable=False
    )
    text_character_count = Column(Integer, nullable=False)  # Character count

    # Relationships
    user = relationship("User", back_populates="messages")
    chat = relationship("Chat", back_populates="messages")
    replied_to = relationship("Message", remote_side=[message_id], backref="replies")
