"""
Tests for Pydantic models.
"""
import pytest
from datetime import datetime
from pydantic import ValidationError

from app.models.chat import (
    Message,
    ChatRequest,
    ChatResponse,
    ConversationHistory,
    ErrorResponse
)


class TestMessage:
    """Test cases for Message model."""
    
    def test_message_creation_success(self):
        """Test successful message creation."""
        message = Message(role="user", content="Hello world")
        
        assert message.role == "user"
        assert message.content == "Hello world"
        assert isinstance(message.timestamp, datetime)
    
    def test_message_invalid_role(self):
        """Test message creation with invalid role."""
        with pytest.raises(ValidationError, match="Role must be either"):
            Message(role="invalid", content="Hello")
    
    def test_message_empty_content(self):
        """Test message creation with empty content."""
        with pytest.raises(ValidationError, match="Message content cannot be empty"):
            Message(role="user", content="")
    
    def test_message_whitespace_content(self):
        """Test message creation with whitespace-only content."""
        with pytest.raises(ValidationError, match="Message content cannot be empty"):
            Message(role="user", content="   ")
    
    def test_message_content_trimming(self):
        """Test that message content is trimmed."""
        message = Message(role="user", content="  Hello world  ")
        assert message.content == "Hello world"


class TestChatRequest:
    """Test cases for ChatRequest model."""
    
    def test_chat_request_success(self):
        """Test successful chat request creation."""
        request = ChatRequest(message="Hello")
        
        assert request.message == "Hello"
        assert request.conversation_id is None
    
    def test_chat_request_with_conversation_id(self):
        """Test chat request with conversation ID."""
        request = ChatRequest(
            message="Hello",
            conversation_id="test-conv-id"
        )
        
        assert request.message == "Hello"
        assert request.conversation_id == "test-conv-id"
    
    def test_chat_request_empty_message(self):
        """Test chat request with empty message."""
        with pytest.raises(ValidationError, match="Message cannot be empty"):
            ChatRequest(message="")
    
    def test_chat_request_whitespace_message(self):
        """Test chat request with whitespace-only message."""
        with pytest.raises(ValidationError, match="Message cannot be empty"):
            ChatRequest(message="   ")
    
    def test_chat_request_too_long_message(self):
        """Test chat request with message exceeding max length."""
        long_message = "x" * 4001
        with pytest.raises(ValidationError):
            ChatRequest(message=long_message)
    
    def test_chat_request_message_trimming(self):
        """Test that message is trimmed."""
        request = ChatRequest(message="  Hello world  ")
        assert request.message == "Hello world"


class TestChatResponse:
    """Test cases for ChatResponse model."""
    
    def test_chat_response_success(self):
        """Test successful chat response creation."""
        response = ChatResponse(
            message="Hello! How can I help?",
            conversation_id="test-conv-id"
        )
        
        assert response.message == "Hello! How can I help?"
        assert response.conversation_id == "test-conv-id"
        assert response.success is True
        assert response.error is None
        assert isinstance(response.timestamp, datetime)
    
    def test_chat_response_with_error(self):
        """Test chat response with error."""
        response = ChatResponse(
            message="",
            conversation_id="test-conv-id",
            success=False,
            error="API error occurred"
        )
        
        assert response.success is False
        assert response.error == "API error occurred"
    
    def test_chat_response_empty_message(self):
        """Test chat response with empty message."""
        with pytest.raises(ValidationError, match="Response message cannot be empty"):
            ChatResponse(
                message="",
                conversation_id="test-conv-id"
            )
    
    def test_chat_response_whitespace_message(self):
        """Test chat response with whitespace-only message."""
        with pytest.raises(ValidationError, match="Response message cannot be empty"):
            ChatResponse(
                message="   ",
                conversation_id="test-conv-id"
            )
    
    def test_chat_response_message_trimming(self):
        """Test that response message is trimmed."""
        response = ChatResponse(
            message="  Hello world  ",
            conversation_id="test-conv-id"
        )
        assert response.message == "Hello world"


class TestConversationHistory:
    """Test cases for ConversationHistory model."""
    
    def test_conversation_creation(self):
        """Test conversation history creation."""
        conv = ConversationHistory(conversation_id="test-id")
        
        assert conv.conversation_id == "test-id"
        assert len(conv.messages) == 0
        assert isinstance(conv.created_at, datetime)
        assert isinstance(conv.updated_at, datetime)
    
    def test_add_message(self):
        """Test adding messages to conversation."""
        conv = ConversationHistory(conversation_id="test-id")
        original_updated_at = conv.updated_at
        
        # Add a small delay to ensure timestamp difference
        import time
        time.sleep(0.001)
        
        conv.add_message("user", "Hello")
        
        assert len(conv.messages) == 1
        assert conv.messages[0].role == "user"
        assert conv.messages[0].content == "Hello"
        assert conv.updated_at > original_updated_at
    
    def test_add_multiple_messages(self):
        """Test adding multiple messages."""
        conv = ConversationHistory(conversation_id="test-id")
        
        conv.add_message("user", "Hello")
        conv.add_message("assistant", "Hi there!")
        conv.add_message("user", "How are you?")
        
        assert len(conv.messages) == 3
        assert conv.messages[0].role == "user"
        assert conv.messages[1].role == "assistant"
        assert conv.messages[2].role == "user"
    
    def test_get_openai_messages(self):
        """Test converting to OpenAI format."""
        conv = ConversationHistory(conversation_id="test-id")
        
        conv.add_message("user", "Hello")
        conv.add_message("assistant", "Hi there!")
        
        openai_messages = conv.get_openai_messages()
        
        assert len(openai_messages) == 2
        assert openai_messages[0] == {"role": "user", "content": "Hello"}
        assert openai_messages[1] == {"role": "assistant", "content": "Hi there!"}


class TestErrorResponse:
    """Test cases for ErrorResponse model."""
    
    def test_error_response_creation(self):
        """Test error response creation."""
        error = ErrorResponse(error="Something went wrong")
        
        assert error.success is False
        assert error.error == "Something went wrong"
        assert error.error_code is None
        assert isinstance(error.timestamp, datetime)
    
    def test_error_response_with_code(self):
        """Test error response with error code."""
        error = ErrorResponse(
            error="API key invalid",
            error_code="AUTH_ERROR"
        )
        
        assert error.success is False
        assert error.error == "API key invalid"
        assert error.error_code == "AUTH_ERROR"