"""
API routes for RAG-enhanced chat functionality.
"""
from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from app.database.config import get_database_session
from app.services.rag_chat_service import RAGChatService
from app.models.message import MessageResponse

router = APIRouter(prefix="/api", tags=["chat"])


class ChatRequest(BaseModel):
    """Request model for chat messages."""
    message: str = Field(..., min_length=1, max_length=10000, description="User message")


class ChatResponse(BaseModel):
    """Response model for chat messages."""
    user_message: MessageResponse
    assistant_message: MessageResponse


def get_chat_service(db: Session = Depends(get_database_session)) -> RAGChatService:
    """Dependency to get RAG chat service."""
    return RAGChatService(db)


@router.post("/sessions/{session_id}/chat", response_model=ChatResponse)
async def send_chat_message(
    session_id: str,
    chat_request: ChatRequest,
    service: RAGChatService = Depends(get_chat_service)
):
    """Send a message and get AI response with RAG enhancement."""
    try:
        # Process the message and get response
        assistant_response = await service.process_chat_message(session_id, chat_request.message)
        
        # Get the user message (it was created in process_chat_message)
        chat_history = service.get_chat_history(session_id)
        
        # Find the user message (should be the second to last message)
        user_message_data = None
        for msg in reversed(chat_history):
            if msg["role"] == "user" and msg["content"] == chat_request.message:
                user_message_data = msg
                break
        
        if not user_message_data:
            raise HTTPException(status_code=500, detail="Failed to retrieve user message")
        
        # Convert to MessageResponse format
        user_message = MessageResponse(
            id=user_message_data["id"],
            session_id=session_id,
            content=user_message_data["content"],
            role=user_message_data["role"],
            timestamp=user_message_data["timestamp"]
        )
        
        return ChatResponse(
            user_message=user_message,
            assistant_message=assistant_response
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to process chat message: {str(e)}")


@router.get("/sessions/{session_id}/history")
async def get_chat_history(
    session_id: str,
    service: RAGChatService = Depends(get_chat_service)
):
    """Get chat history for a session."""
    try:
        history = service.get_chat_history(session_id)
        return {"messages": history}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get chat history: {str(e)}")


@router.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "RAG Chat API"}