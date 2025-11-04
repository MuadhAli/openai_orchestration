"""
Custom exceptions for the ChatGPT Web UI application.
"""
from typing import Optional


class ChatAppException(Exception):
    """Base exception for ChatGPT Web UI application."""
    
    def __init__(self, message: str, error_code: Optional[str] = None):
        self.message = message
        self.error_code = error_code
        super().__init__(self.message)


class APIKeyError(ChatAppException):
    """Raised when API key is invalid or missing."""
    
    def __init__(self, message: str = "Invalid or missing OpenAI API key"):
        super().__init__(message, "API_KEY_ERROR")


class ConversationError(ChatAppException):
    """Raised when conversation operations fail."""
    
    def __init__(self, message: str = "Conversation operation failed"):
        super().__init__(message, "CONVERSATION_ERROR")


class OpenAIAPIError(ChatAppException):
    """Raised when OpenAI API calls fail."""
    
    def __init__(self, message: str = "OpenAI API call failed"):
        super().__init__(message, "OPENAI_API_ERROR")


class ValidationError(ChatAppException):
    """Raised when input validation fails."""
    
    def __init__(self, message: str = "Input validation failed"):
        super().__init__(message, "VALIDATION_ERROR")


class RateLimitError(ChatAppException):
    """Raised when rate limits are exceeded."""
    
    def __init__(self, message: str = "Rate limit exceeded"):
        super().__init__(message, "RATE_LIMIT_ERROR")


class ConnectionError(ChatAppException):
    """Raised when connection to external services fails."""
    
    def __init__(self, message: str = "Connection failed"):
        super().__init__(message, "CONNECTION_ERROR")