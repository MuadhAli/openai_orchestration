"""
SQLAlchemy models for RAG chat system.
"""
import uuid
from datetime import datetime
from sqlalchemy import Column, String, Text, DateTime, ForeignKey, Enum, JSON, Index
from sqlalchemy.orm import relationship
import enum

from app.database.config import Base

class MessageRole(enum.Enum):
    """Enum for message roles."""
    USER = "user"
    ASSISTANT = "assistant"

class Session(Base):
    """SQLAlchemy model for chat sessions."""
    __tablename__ = "sessions"
    
    id = Column(String(36), primary_key=True)
    name = Column(String(255), nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.now)
    
    def __init__(self, **kwargs):
        if 'id' not in kwargs:
            kwargs['id'] = str(uuid.uuid4())
        super().__init__(**kwargs)
    
    # Relationship to messages
    messages = relationship("Message", back_populates="session", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Session(id='{self.id}', name='{self.name}')>"

class Message(Base):
    """SQLAlchemy model for chat messages."""
    __tablename__ = "messages"
    
    id = Column(String(36), primary_key=True)
    session_id = Column(String(36), ForeignKey("sessions.id", ondelete="CASCADE"), nullable=False)
    content = Column(Text, nullable=False)
    role = Column(Enum(MessageRole), nullable=False)
    timestamp = Column(DateTime, nullable=False, default=datetime.now)
    
    def __init__(self, **kwargs):
        if 'id' not in kwargs:
            kwargs['id'] = str(uuid.uuid4())
        super().__init__(**kwargs)
    
    # Relationship to session
    session = relationship("Session", back_populates="messages")
    
    # Index for efficient querying
    __table_args__ = (
        Index('idx_session_timestamp', 'session_id', 'timestamp'),
    )
    
    def __repr__(self):
        return f"<Message(id='{self.id}', session_id='{self.session_id}', role='{self.role.value}')>"

class MessageEmbedding(Base):
    """SQLAlchemy model for message embeddings for conversational RAG."""
    __tablename__ = "message_embeddings"
    
    id = Column(String(36), primary_key=True)
    message_id = Column(String(36), ForeignKey("messages.id", ondelete="CASCADE"), nullable=False)
    session_id = Column(String(36), ForeignKey("sessions.id", ondelete="CASCADE"), nullable=False)
    content = Column(Text, nullable=False)
    role = Column(Enum(MessageRole), nullable=False)
    embedding = Column(JSON, nullable=False)  # Store embedding as JSON array
    created_at = Column(DateTime, nullable=False, default=datetime.now)
    
    def __init__(self, **kwargs):
        if 'id' not in kwargs:
            kwargs['id'] = str(uuid.uuid4())
        super().__init__(**kwargs)
    
    # Relationships
    message = relationship("Message")
    session = relationship("Session")
    
    # Index for efficient similarity search
    __table_args__ = (
        Index('idx_role_created', 'role', 'created_at'),
        Index('idx_session_role', 'session_id', 'role'),
    )
    
    def __repr__(self):
        return f"<MessageEmbedding(id='{self.id}', message_id='{self.message_id}', role='{self.role.value}')>"