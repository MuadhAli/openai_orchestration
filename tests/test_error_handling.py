"""
Tests for error handling utilities.
"""
import pytest
from fastapi import HTTPException
from openai import AuthenticationError, RateLimitError, APIConnectionError, APIError

from app.exceptions import (
    ChatAppException,
    APIKeyError,
    ConversationError,
    OpenAIAPIError,
    ValidationError,
    RateLimitError as AppRateLimitError,
    ConnectionError as AppConnectionError
)
from app.utils.error_handler import ErrorHandler, safe_execute, safe_execute_async


class TestChatAppExceptions:
    """Test custom exception classes."""
    
    def test_chat_app_exception(self):
        """Test base ChatAppException."""
        exc = ChatAppException("Test error", "TEST_ERROR")
        
        assert str(exc) == "Test error"
        assert exc.message == "Test error"
        assert exc.error_code == "TEST_ERROR"
    
    def test_api_key_error(self):
        """Test APIKeyError."""
        exc = APIKeyError()
        
        assert "Invalid or missing OpenAI API key" in str(exc)
        assert exc.error_code == "API_KEY_ERROR"
    
    def test_conversation_error(self):
        """Test ConversationError."""
        exc = ConversationError("Failed to create conversation")
        
        assert str(exc) == "Failed to create conversation"
        assert exc.error_code == "CONVERSATION_ERROR"
    
    def test_openai_api_error(self):
        """Test OpenAIAPIError."""
        exc = OpenAIAPIError("API call failed")
        
        assert str(exc) == "API call failed"
        assert exc.error_code == "OPENAI_API_ERROR"


class TestErrorHandler:
    """Test ErrorHandler utility class."""
    
    def test_handle_authentication_error(self):
        """Test handling OpenAI AuthenticationError."""
        openai_error = AuthenticationError("Invalid API key")
        app_error = ErrorHandler.handle_openai_error(openai_error)
        
        assert isinstance(app_error, APIKeyError)
        assert "Invalid OpenAI API key" in str(app_error)
    
    def test_handle_rate_limit_error(self):
        """Test handling OpenAI RateLimitError."""
        openai_error = RateLimitError("Rate limit exceeded")
        app_error = ErrorHandler.handle_openai_error(openai_error)
        
        assert isinstance(app_error, AppRateLimitError)
        assert "Rate limit exceeded" in str(app_error)
    
    def test_handle_connection_error(self):
        """Test handling OpenAI APIConnectionError."""
        openai_error = APIConnectionError("Connection failed")
        app_error = ErrorHandler.handle_openai_error(openai_error)
        
        assert isinstance(app_error, AppConnectionError)
        assert "Unable to connect to OpenAI API" in str(app_error)
    
    def test_handle_api_error(self):
        """Test handling OpenAI APIError."""
        openai_error = APIError("API error")
        app_error = ErrorHandler.handle_openai_error(openai_error)
        
        assert isinstance(app_error, OpenAIAPIError)
        assert "OpenAI API error" in str(app_error)
    
    def test_handle_unexpected_error(self):
        """Test handling unexpected errors."""
        unexpected_error = ValueError("Unexpected error")
        app_error = ErrorHandler.handle_openai_error(unexpected_error)
        
        assert isinstance(app_error, OpenAIAPIError)
        assert "Unexpected API error" in str(app_error)
    
    def test_to_http_exception_api_key_error(self):
        """Test converting APIKeyError to HTTPException."""
        app_error = APIKeyError("Invalid API key")
        http_exc = ErrorHandler.to_http_exception(app_error)
        
        assert isinstance(http_exc, HTTPException)
        assert http_exc.status_code == 503
        assert http_exc.detail["error"] == "Invalid API key"
        assert http_exc.detail["error_code"] == "API_KEY_ERROR"
    
    def test_to_http_exception_validation_error(self):
        """Test converting ValidationError to HTTPException."""
        app_error = ValidationError("Invalid input")
        http_exc = ErrorHandler.to_http_exception(app_error)
        
        assert http_exc.status_code == 400
        assert http_exc.detail["error"] == "Invalid input"
    
    def test_to_http_exception_rate_limit_error(self):
        """Test converting RateLimitError to HTTPException."""
        app_error = AppRateLimitError("Rate limited")
        http_exc = ErrorHandler.to_http_exception(app_error)
        
        assert http_exc.status_code == 429
        assert http_exc.detail["error"] == "Rate limited"
    
    def test_to_http_exception_unknown_error(self):
        """Test converting unknown error to HTTPException."""
        app_error = ChatAppException("Unknown error", "UNKNOWN")
        http_exc = ErrorHandler.to_http_exception(app_error)
        
        assert http_exc.status_code == 500  # Default status code
    
    def test_create_error_response_chat_app_exception(self):
        """Test creating error response for ChatAppException."""
        app_error = APIKeyError("Invalid key")
        response = ErrorHandler.create_error_response(app_error)
        
        assert response["success"] is False
        assert response["error"] == "Invalid key"
        assert response["error_code"] == "API_KEY_ERROR"
        assert response["type"] == "APIKeyError"
    
    def test_create_error_response_unexpected_error(self):
        """Test creating error response for unexpected error."""
        unexpected_error = ValueError("Unexpected")
        response = ErrorHandler.create_error_response(unexpected_error, "Default message")
        
        assert response["success"] is False
        assert response["error"] == "Default message"
        assert response["error_code"] == "UNEXPECTED_ERROR"
        assert response["type"] == "UnexpectedError"


class TestSafeExecute:
    """Test safe execution utilities."""
    
    def test_safe_execute_success(self):
        """Test successful safe execution."""
        def test_func(x, y):
            return x + y
        
        success, result, error = safe_execute(test_func, 2, 3)
        
        assert success is True
        assert result == 5
        assert error is None
    
    def test_safe_execute_failure(self):
        """Test safe execution with error."""
        def test_func():
            raise ValueError("Test error")
        
        success, result, error = safe_execute(test_func)
        
        assert success is False
        assert result is None
        assert isinstance(error, ValueError)
        assert str(error) == "Test error"
    
    @pytest.mark.asyncio
    async def test_safe_execute_async_success(self):
        """Test successful async safe execution."""
        async def test_func(x, y):
            return x * y
        
        success, result, error = await safe_execute_async(test_func, 3, 4)
        
        assert success is True
        assert result == 12
        assert error is None
    
    @pytest.mark.asyncio
    async def test_safe_execute_async_failure(self):
        """Test async safe execution with error."""
        async def test_func():
            raise RuntimeError("Async error")
        
        success, result, error = await safe_execute_async(test_func)
        
        assert success is False
        assert result is None
        assert isinstance(error, RuntimeError)
        assert str(error) == "Async error"