"""
Simple Pydantic models for document management.
"""
from datetime import datetime
from typing import List
from pydantic import BaseModel, Field, validator


class DocumentCreate(BaseModel):
    """Model for creating a new document."""
    filename: str = Field(..., min_length=1, max_length=255, description="Document filename")
    content: str = Field(..., min_length=1, description="Document content")
    
    @validator('filename')
    def validate_filename(cls, v):
        """Validate filename."""
        if not v or not v.strip():
            raise ValueError('Filename cannot be empty')
        return v.strip()
    
    @validator('content')
    def validate_content(cls, v):
        """Validate content."""
        if not v or not v.strip():
            raise ValueError('Content cannot be empty')
        return v.strip()


class DocumentResponse(BaseModel):
    """Complete document model for responses."""
    id: str = Field(..., description="Unique document identifier")
    filename: str = Field(..., description="Document filename")
    content: str = Field(..., description="Document content")
    created_at: datetime = Field(..., description="When the document was created")
    
    class Config:
        """Pydantic configuration."""
        from_attributes = True


class DocumentListResponse(BaseModel):
    """Response model for listing documents."""
    documents: List[DocumentResponse] = Field(..., description="List of documents")
    
    class Config:
        """Pydantic configuration."""
        from_attributes = True