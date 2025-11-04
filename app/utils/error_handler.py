"""
Error handling utilities for the ChatGPT Web UI application.
"""
import logging
from typing import Dict, Any, Optional
from fastapi import HTTPException
from openai import APIError, RateLimitError, APIConnectionError, AuthenticationError

from app.exceptions import (
    ChatAppException,
    APIKeyError,
    ConversationError,
    OpenAIAPIError,
    ValidationError,
    RateLimitError as AppRateLimitError,
    ConnectionError as AppConnectionError
)

logger = logging.getLogger(__name__)


class ErrorHandler:
    """Centralized error handling for the application."""
    
    @staticmethod
    def handle_openai_error(error: Exception) -> ChatAppException:
        """
        Convert OpenAI errors to application-specific errors.
        
        Args:
            error: The original OpenAI error
            
        Returns:
            ChatAppException: Application-specific error
        """
        if isinstance(error, AuthenticationError):
            logger.error(f"OpenAI authentication error: {str(error)}")
            return APIKeyError("Invalid OpenAI API key. Please check your configuration.")
        
        elif isinstance(error, RateLimitError):
            logger.warning(f"OpenAI rate limit error: {str(error)}")
            return AppRateLimitError("Rate limit exceeded. Please try again in a moment.")
        
        elif isinstance(error, APIConnectionError):
            logger.error(f"OpenAI connection error: {str(error)}")
            return AppConnectionError("Unable to connect to OpenAI API. Please check your internet connection.")
        
        elif isinstance(error, APIError):
            logger.error(f"OpenAI API error: {str(error)}")
            return OpenAIAPIError(f"OpenAI API error: {str(error)}")
        
        else:
            logger.error(f"Unexpected OpenAI error: {str(error)}")
            return OpenAIAPIError(f"Unexpected API error: {str(error)}")
    
    @staticmethod
    def to_http_exception(error: ChatAppException) -> HTTPException:
        """
        Convert application errors to HTTP exceptions.
        
        Args:
            error: Application-specific error
            
        Returns:
            HTTPException: FastAPI HTTP exception
        """
        status_code_map = {
            "API_KEY_ERROR": 503,
            "VALIDATION_ERROR": 400,
            "RATE_LIMIT_ERROR": 429,
            "CONNECTION_ERROR": 503,
            "OPENAI_API_ERROR": 502,
            "CONVERSATION_ERROR": 500
        }
        
        status_code = status_code_map.get(error.error_code, 500)
        
        return HTTPException(
            status_code=status_code,
            detail={
                "error": error.message,
                "error_code": error.error_code,
                "type": type(error).__name__
            }
        )
    
    @staticmethod
    def create_error_response(
        error: Exception,
        default_message: str = "An unexpected error occurred"
    ) -> Dict[str, Any]:
        """
        Create a standardized error response.
        
        Args:
            error: The error that occurred
            default_message: Default message if error message is not available
            
        Returns:
            Dict containing error information
        """
        if isinstance(error, ChatAppException):
            return {
                "success": False,
                "error": error.message,
                "error_code": error.error_code,
                "type": type(error).__name__
            }
        else:
            logger.error(f"Unexpected error: {str(error)}", exc_info=True)
            return {
                "success": False,
                "error": default_message,
                "error_code": "UNEXPECTED_ERROR",
                "type": "UnexpectedError"
            }
    
    @staticmethod
    def log_error(error: Exception, context: str = "") -> None:
        """
        Log an error with appropriate level and context.
        
        Args:
            error: The error to log
            context: Additional context information
        """
        context_str = f" [{context}]" if context else ""
        
        if isinstance(error, (APIKeyError, AppConnectionError)):
            logger.error(f"Critical error{context_str}: {str(error)}")
        elif isinstance(error, AppRateLimitError):
            logger.warning(f"Rate limit error{context_str}: {str(error)}")
        elif isinstance(error, ValidationError):
            logger.info(f"Validation error{context_str}: {str(error)}")
        else:
            logger.error(f"Error{context_str}: {str(error)}", exc_info=True)


def safe_execute(func, *args, **kwargs):
    """
    Safely execute a function and handle any errors.
    
    Args:
        func: Function to execute
        *args: Positional arguments for the function
        **kwargs: Keyword arguments for the function
        
    Returns:
        Tuple of (success: bool, result: Any, error: Optional[Exception])
    """
    try:
        result = func(*args, **kwargs)
        return True, result, None
    except Exception as e:
        ErrorHandler.log_error(e, f"safe_execute({func.__name__})")
        return False, None, e


async def safe_execute_async(func, *args, **kwargs):
    """
    Safely execute an async function and handle any errors.
    
    Args:
        func: Async function to execute
        *args: Positional arguments for the function
        **kwargs: Keyword arguments for the function
        
    Returns:
        Tuple of (success: bool, result: Any, error: Optional[Exception])
    """
    try:
        result = await func(*args, **kwargs)
        return True, result, None
    except Exception as e:
        ErrorHandler.log_error(e, f"safe_execute_async({func.__name__})")
        return False, None, e