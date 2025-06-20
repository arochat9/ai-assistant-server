from sqlalchemy import Column, String, DateTime, ForeignKey, Table
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import Base

# Association table for many-to-many relationship between chats and users
chat_users = Table(
    'chat_users',
    Base.metadata,
    Column('chat_id', String, ForeignKey('chats.chat_id'), primary_key=True),
    Column('user_id', String, ForeignKey('users.user_id'), primary_key=True)
)

class Chat(Base):
    __tablename__ = "chats"
    
    chat_id = Column(String, primary_key=True, index=True)  # Chat ID passed in API calls
    chat_display_name = Column(String, nullable=True)  # Display name for the chat
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    users = relationship("User", secondary=chat_users, back_populates="chats")  # Array of users in chat
    messages = relationship("Message", back_populates="chat", order_by="Message.time_received")
