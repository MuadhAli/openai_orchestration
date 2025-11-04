"""
Chat API routes for handling chat messages and conversation management.
"""
import logging
from fastapi import APIRouter, HTTPException, Depends, Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from typing import Dict, Any
from pydantic import ValidationError

from app.models.chat import ChatRequest, ChatResponse, ErrorResponse
from app.services.chat_service import (
    ChatService, 
    ChatServiceError, 
    APIKeyError, 
    ConversationError, 
    OpenAIAPIError
)

# Configure logging
logger = logging.getLogger(__name__)

# Create router instance
router = APIRouter(prefix="/api", tags=["chat"])

# Global chat service instance
chat_service = None


def get_chat_service() -> ChatService:
    """Dependency to get the chat service instance."""
    global chat_service
    if chat_service is None:
        try:
            chat_service = ChatService()
        except APIKeyError as e:
            logger.error(f"Failed to initialize ChatService: {str(e)}")
            raise HTTPException(
                status_code=503,
                detail="Service unavailable: Invalid API configuration"
            )
        except Exception as e:
            logger.error(f"Unexpected error initializing ChatService: {str(e)}")
            raise HTTPException(
                status_code=503,
                detail="Service unava


@router.post("/chat", response_model=ChatResponse)
async def send_message(
    request: ChatRequest,
    service: ChatService = Depends(get_chat_service)
) -> ChatResponse:
    """
    Send a message to the AI assistant and get a response.
    
    Args:
        request: ChatRequest containing the user's message and optional conversation_id
        service: ChatService dependency for handling the chat logic
        
    Returns:
        ChatResponse with the AI's response or error information
        
    Raises:
        HTTPException: For validation errors or server errors
    """
    try:
        logger.info(f"Received chat message: {request.message[:50]}...")
        
        # Validate request
        if not request.message or not request.message.strip():
            raise HTTPException(
                status_code=400,
                detail="Message cannot be empty"
            )
        
        # Send message to chat service
        response = await service.send_message(request)
        
        # Check if the service returned an error
        if not response.success:
            logger.error(f"Chat service error: {response.error}")
            raise HTTPException(
                status_code=500,
                detail=response.error or "Failed to process message"
            )
        
        logger.info(f"Successfully processed message for conversation: {response.conversation_id}")
        return response
        
    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception as e:
        logger.error(f"Unexpected error in send_message: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Internal server error occurred while processing your message"
        )


@router.post("/chat/new")
async def start_new_conversation(
    service: ChatService = Depends(get_chat_service)
) -> Dict[str, Any]:
    """
    Start a new conversation by creating a new conversation ID.
    
    Args:
        service: ChatService dependency for handling the chat logic
        
    Returns:
        Dictionary containing the new conversation_id and success status
        
    Raises:
        HTTPException: For server errors
    """
    try:
        logger.info("Creating new conversation")
        
        # Create new conversation
        conversation_id = service.create_conversation()
        
        logger.info(f"Created new conversation: {conversation_id}")
        
        return {
            "success": True,
            "conversation_id": conversation_id,
            "message": "New conversation started successfully"
        }
        
    except Exception as e:
        logger.error(f"Error creating new conversation: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Failed to create new conversation"
        )


@router.get("/health")
async def health_check(
    service: ChatService = Depends(get_chat_service)
) -> Dict[str, Any]:
    """
    Perform a health check of the chat service and OpenAI API connection.
    
    Args:
        service: ChatService dependency for performing the health check
        
    Returns:
        Dictionary containing health status information
    """
    try:
        logger.info("Performing health check")
        
        # Get health status from chat service
        health_status = service.health_check()
        
        # Determine HTTP status code based on health
        if health_status.get("status") == "healthy":
            status_code = 200
            logger.info("Health check passed")
        else:
            status_code = 503  # Service Unavailable
            logger.warning(f"Health check failed: {health_status.get('error', 'Unknown error')}")
        
        return JSONResponse(
            status_code=status_code,
            content=health_status
        )
        
    except Exception as e:
        logger.error(f"Health check error: {str(e)}")
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "error": "Health check failed due to internal error",
                "details": str(e)
            }
        )