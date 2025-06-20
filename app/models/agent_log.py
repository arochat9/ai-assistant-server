from sqlalchemy import Column, Integer, String, Text, DateTime, JSON, Enum, ForeignKey
from sqlalchemy.sql import func
import enum

from app.core.database import Base

class AgentLogLevel(enum.Enum):
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"

class AgentLogType(enum.Enum):
    THOUGHT = "thought"
    ACTION = "action"
    OBSERVATION = "observation"
    DECISION = "decision"
    ERROR = "error"

class AgentLog(Base):
    __tablename__ = "agent_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String, nullable=False, index=True)  # Groups related agent actions
    log_type = Column(Enum(AgentLogType), nullable=False)
    level = Column(Enum(AgentLogLevel), default=AgentLogLevel.INFO)
    message = Column(Text, nullable=False)
    
    # Optional structured data
    extra_data = Column(JSON, nullable=True)
    
    # Source tracking
    source_message_id = Column(String, ForeignKey("messages.message_id"), nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    def __repr__(self):
        return f"<AgentLog(session_id={self.session_id}, type={self.log_type}, level={self.level})>"
