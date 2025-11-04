"""
Unit tests for ChatService.
"""
import pytest
import os
from unittest.mock import Mock, patch, AsyncMock
from openai import AuthenticationError, RateLimitError, APIConnectionError

from app.services.chat_service import ChatService
from app.models.chat import ChatRequest, ChatResponse
from app.exceptions import APIKeyError, OpenAIAPIError


class TestChatService:
    """Test cases for ChatService."""
    
    @pytest.fixture
    def mock_env(self):
        """Mock environment variables."""
        with patch.dict(os.environ, {'OPENAI_API_KEY': 'sk-test-key-123'}):
            yield
    
    @pytest.fixture
    def chat_service(self, mock_env):
        """Create a ChatService instance for testing."""
        with patch('app.services.chat_service.OpenAI'):
            return ChatService()
    
    def test_init_success(self, mock_env):
        """Test successful ChatService initialization."""
        with patch('app.services.chat_service.OpenAI') as mock_openai:
            service = ChatService()
            assert service.api_key == 'sk-test-key-123'
            assert service.default_model == 'gpt-4o-mini'
            assert service.max_retries == 3
            mock_openai.assert_called_once()
    
    def test_init_missing_api_key(self):
        """Test ChatService initialization with missing API key."""
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(APIKeyError, match="OPENAI_API_KEY environment variable is required"):
                ChatService()
    
    def test_init_invalid_api_key_format(self):
        """Test ChatService initialization with invalid API key format."""
        with patch.dict(os.environ, {'OPENAI_API_KEY': 'invalid-key'}):
            with pytest.raises(APIKeyError, match="Invalid OpenAI API key format"):
                ChatService()
    
    def test_create_conversation(self, chat_service):
        """Test conversation creation."""
        conversation_id = chat_service.create_conversation()
        
        assert conversation_id is not None
        assert len(conversation_id) == 36  # UUID length
        assert conversation_id in chat_service.conversations
        assert chat_service.get_conversation_count() == 1
    
    def test_get_conversation(self, chat_service):
        """Test getting a conversation."""
        conversation_id = chat_service.create_conversation()
        conversation = chat_service.get_conversation(conversation_id)
        
        assert conversation is not None
        assert conversation.conversation_id == conversation_id
        
        # Test non-existent conversation
        non_existent = chat_service.get_conversation("non-existent-id")
        assert non_existent is None
    
    @pytest.mark.asyncio
    async def test_send_message_success(self, chat_service):
        """Test successful message sending."""
        # Mock the OpenAI API response
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = "Hello! How can I help you?"
        
        with patch.object(chat_service, '_call_openai_api_with_retry', return_value=mock_response):
            request = ChatRequest(message="Hello")
            response = await chat_service.send_message(request)
            
            assert response.success is True
            assert response.message == "Hello! How can I help you?"
            assert response.conversation_id is not None
            assert response.error is None
    
    @pytest.mark.asyncio
    async def test_send_message_empty_message(self, chat_service):
        """Test sending empty message."""
        request = ChatRequest(message="")
        response = await chat_service.send_message(request)
        
        assert response.success is False
        assert "Message cannot be empty" in response.error
    
    @pytest.mark.asyncio
    async def test_send_message_too_long(self, chat_service):
        """Test sending message that's too long."""
        long_message = "x" * 4001  # Exceeds 4000 character limit
        request = ChatRequest(message=long_message)
        response = await chat_service.send_message(request)
        
        assert response.success is False
        assert "Message too long" in response.error
    
    @pytest.mark.asyncio
    async def test_send_message_api_error(self, chat_service):
        """Test handling OpenAI API errors."""
        with patch.object(chat_service, '_call_openai_api_with_retry', side_effect=OpenAIAPIError("API Error")):
            request = ChatRequest(message="Hello")
            response = await chat_service.send_message(request)
            
            assert response.success is False
            assert "API Error" in response.error
    
    @pytest.mark.asyncio
    async def test_call_openai_api_success(self, chat_service):
        """Test successful OpenAI API call."""
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = "Test response"
        
        with patch.object(chat_service.client.chat.completions, 'create', return_value=mock_response):
            messages = [{"role": "user", "content": "Hello"}]
            response = await chat_service._call_openai_api(messages)
            
            assert response == mock_response
    
    @pytest.mark.asyncio
    async def test_call_openai_api_authentication_error(self, chat_service):
        """Test OpenAI API authentication error."""
        with patch.object(chat_service.client.chat.completions, 'create', side_effect=AuthenticationError("Invalid API key")):
            messages = [{"role": "user", "content": "Hello"}]
            
            with pytest.raises(AuthenticationError):
                await chat_service._call_openai_api(messages)
    
    @pytest.mark.asyncio
    async def test_call_openai_api_with_retry_rate_limit(self, chat_service):
        """Test retry logic with rate limit error."""
        chat_service.max_retries = 2
        chat_service.retry_delay = 0.01  # Fast retry for testing
        
        # Mock rate limit error then success
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = "Success after retry"
        
        with patch.object(chat_service, '_call_openai_api', side_effect=[
            RateLimitError("Rate limited"),
            mock_response
        ]):
            messages = [{"role": "user", "content": "Hello"}]
            response = await chat_service._call_openai_api_with_retry(messages)
            
            assert response == mock_response
    
    @pytest.mark.asyncio
    async def test_call_openai_api_with_retry_max_attempts(self, chat_service):
        """Test retry logic reaching max attempts."""
        chat_service.max_retries = 2
        chat_service.retry_delay = 0.01
        
        with patch.object(chat_service, '_call_openai_api', side_effect=RateLimitError("Rate limited")):
            messages = [{"role": "user", "content": "Hello"}]
            
            with pytest.raises(OpenAIAPIError, match="Failed to get response from OpenAI after 2 attempts"):
                await chat_service._call_openai_api_with_retry(messages)
    
    def test_clear_conversation(self, chat_service):
        """Test clearing conversation messages."""
        conversation_id = chat_service.create_conversation()
        conversation = chat_service.get_conversation(conversation_id)
        conversation.add_message("user", "Hello")
        conversation.add_message("assistant", "Hi there!")
        
        assert len(conversation.messages) == 2
        
        result = chat_service.clear_conversation(conversation_id)
        assert result is True
        assert len(conversation.messages) == 0
        
        # Test clearing non-existent conversation
        result = chat_service.clear_conversation("non-existent")
        assert result is False
    
    def test_delete_conversation(self, chat_service):
        """Test deleting a conversation."""
        conversation_id = chat_service.create_conversation()
        assert chat_service.get_conversation_count() == 1
        
        result = chat_service.delete_conversation(conversation_id)
        assert result is True
        assert chat_service.get_conversation_count() == 0
        assert chat_service.get_conversation(conversation_id) is None
        
        # Test deleting non-existent conversation
        result = chat_service.delete_conversation("non-existent")
        assert result is False
    
    def test_health_check_success(self, chat_service):
        """Test successful health check."""
        mock_response = Mock()
        
        with patch.object(chat_service.client.chat.completions, 'create', return_value=mock_response):
            health = chat_service.health_check()
            
            assert health["status"] == "healthy"
            assert health["api_connection"] == "ok"
            assert health["model"] == chat_service.default_model
            assert "active_conversations" in health
    
    def test_health_check_authentication_error(self, chat_service):
        """Test health check with authentication error."""
        with patch.object(chat_service.client.chat.completions, 'create', side_effect=AuthenticationError("Invalid key")):
            health = chat_service.health_check()
            
            assert health["status"] == "unhealthy"
            assert health["api_connection"] == "authentication_failed"
            assert health["error"] == "Invalid API key"
    
    def test_health_check_rate_limit(self, chat_service):
        """Test health check with rate limit."""
        with patch.object(chat_service.client.chat.completions, 'create', side_effect=RateLimitError("Rate limited")):
            health = chat_service.health_check()
            
            assert health["status"] == "degraded"
            assert health["api_connection"] == "rate_limited"
            assert health["error"] == "Rate limit exceeded"
    
    def test_health_check_connection_error(self, chat_service):
        """Test health check with connection error."""
        with patch.object(chat_service.client.chat.completions, 'create', side_effect=APIConnectionError("Connection failed")):
            health = chat_service.health_check()
            
            assert health["status"] == "unhealthy"
            assert health["api_connection"] == "connection_failed"
            assert health["error"] == "Cannot connect to OpenAI API"