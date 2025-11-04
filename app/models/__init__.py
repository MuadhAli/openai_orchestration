"""
Data models for the ChatGPT Web UI application.
"""
from .chat import Message, ChatRequest, ChatResponse, ConversationHistory, ErrorResponse

__all__ = [
    "Message",
    "ChatRequest", 
    "ChatResponse",
    "ConversationHistory",
    "ErrorResponse"
]