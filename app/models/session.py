"""
Pydantic models for session management.
"""
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, validator


class SessionCreate(BaseModel):
    """Model for creating a new session."""
    name: str = Field(..., min_length=1, max_length=255, description="Session name")
    
    @validator('name')
    def validate_name(cls, v):
        """Validate session name."""
        if not v or not v.strip():
            raise ValueError('Session name cannot be empty')
        return v.strip()


class SessionUpdate(BaseModel):
    """Model for updating an existing session."""
    name: Optional[str] = Field(None, min_length=1, max_length=255, description="New session name")
    
    @validator('name')
    def validate_name(cls, v):
        """Validate session name."""
        if v is None:
            return v
        if not v or not v.strip():
            raise ValueError('Session name cannot be empty')
        return v.strip()


class SessionResponse(BaseModel):
    """Complete session model for responses."""
    id: str = Field(..., description="Unique session identifier")
    name: str = Field(..., description="Session name")
    created_at: datetime = Field(..., description="When the session was created")
    
    class Config:
        """Pydantic configuration."""
        from_attributes = True


class SessionListResponse(BaseModel):
    """Response model for listing sessions."""
    sessions: List[SessionResponse] = Field(..., description="List of sessions")
    
    class Config:
        """Pydantic configuration."""
        from_attributes = True