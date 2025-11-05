"""
Data models for the ChatGPT Web UI application.
"""
from .chat import Message, ChatRequest, ChatResponse, ConversationHistory, ErrorResponse
from .session import (
    SessionCreate, SessionUpdate, SessionResponse, SessionListResponse
)
from .message import (
    MessageCreate, MessageResponse, MessageListResponse
)

__all__ = [
    # Chat models (legacy/compatibility)
    "Message",
    "ChatRequest", 
    "ChatResponse",
    "ConversationHistory",
    "ErrorResponse",
    
    # Session models
    "SessionCreate",
    "SessionUpdate", 
    "SessionListResponse",
    "SessionResponse",
    
    # Message models
    "MessageCreate",
    "MessageListResponse", 
    "MessageResponse"
]