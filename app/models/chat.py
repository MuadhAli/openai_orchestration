"""
Pydantic models for chat requests and responses.
"""
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, validator


class Message(BaseModel):
    """Represents a single message in a chat conversation."""
    role: str = Field(..., description="The role of the message sender (user or assistant)")
    content: str = Field(..., min_length=1, description="The content of the message")
    timestamp: datetime = Field(default_factory=datetime.now, description="When the message was created")
    
    @validator('role')
    def validate_role(cls, v):
        """Validate that role is either 'user' or 'assistant'."""
        if v not in ['user', 'assistant']:
            raise ValueError('Role must be either "user" or "assistant"')
        return v
    
    @validator('content')
    def validate_content(cls, v):
        """Validate that content is not empty or just whitespace."""
        if not v or not v.strip():
            raise ValueError('Message content cannot be empty')
        return v.strip()


class ChatRequest(BaseModel):
    """Request model for sending a chat message."""
    message: str = Field(..., min_length=1, max_length=4000, description="The user's message")
    conversation_id: Optional[str] = Field(None, description="Optional conversation ID for context")
    
    @validator('message')
    def validate_message(cls, v):
        """Validate that message is not empty or just whitespace."""
        if not v or not v.strip():
            raise ValueError('Message cannot be empty')
        return v.strip()


class ChatResponse(BaseModel):
    """Response model for chat API endpoints."""
    message: str = Field(..., description="The AI assistant's response message")
    conversation_id: str = Field(..., description="The conversation ID for this chat session")
    success: bool = Field(True, description="Whether the request was successful")
    error: Optional[str] = Field(None, description="Error message if the request failed")
    timestamp: datetime = Field(default_factory=datetime.now, description="When the response was generated")
    
    @validator('message')
    def validate_message(cls, v):
        """Validate that response message is not empty."""
        if not v or not v.strip():
            raise ValueError('Response message cannot be empty')
        return v.strip()


class ConversationHistory(BaseModel):
    """Model for managing conversation history."""
    conversation_id: str = Field(..., description="Unique identifier for the conversation")
    messages: List[Message] = Field(default_factory=list, description="List of messages in the conversation")
    created_at: datetime = Field(default_factory=datetime.now, description="When the conversation was created")
    updated_at: datetime = Field(default_factory=datetime.now, description="When the conversation was last updated")
    
    def add_message(self, role: str, content: str) -> None:
        """Add a new message to the conversation."""
        message = Message(role=role, content=content)
        self.messages.append(message)
        self.updated_at = datetime.now()
    
    def get_openai_messages(self) -> List[dict]:
        """Convert messages to OpenAI API format."""
        return [{"role": msg.role, "content": msg.content} for msg in self.messages]


class ErrorResponse(BaseModel):
    """Standard error response model."""
    success: bool = Field(False, description="Always False for error responses")
    error: str = Field(..., description="Error message describing what went wrong")
    error_code: Optional[str] = Field(None, description="Optional error code for programmatic handling")
    timestamp: datetime = Field(default_factory=datetime.now, description="When the error occurred")