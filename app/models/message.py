"""
Simple Pydantic models for message management.
"""
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, validator


class MessageCreate(BaseModel):
    """Model for creating a new message."""
    session_id: str = Field(..., description="Session ID this message belongs to")
    content: str = Field(..., min_length=1, max_length=10000, description="Message content")
    role: str = Field(..., description="Message role (user or assistant)")
    
    @validator('role')
    def validate_role(cls, v):
        """Validate that role is either 'user' or 'assistant'."""
        if v not in ['user', 'assistant']:
            raise ValueError('Role must be either "user" or "assistant"')
        return v
    
    @validator('content')
    def validate_content(cls, v):
        """Validate that content is not empty."""
        if not v or not v.strip():
            raise ValueError('Message content cannot be empty')
        return v.strip()


class MessageResponse(BaseModel):
    """Complete message model for responses."""
    id: str = Field(..., description="Unique message identifier")
    session_id: str = Field(..., description="Session ID this message belongs to")
    content: str = Field(..., description="Message content")
    role: str = Field(..., description="Message role (user or assistant)")
    timestamp: datetime = Field(..., description="When the message was created")
    
    class Config:
        """Pydantic configuration."""
        from_attributes = True


class MessageListResponse(BaseModel):
    """Response model for listing messages."""
    messages: List[MessageResponse] = Field(..., description="List of messages")
    
    class Config:
        """Pydantic configuration."""
        from_attributes = True