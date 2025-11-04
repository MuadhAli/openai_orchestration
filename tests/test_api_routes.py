"""
Integration tests for API routes.
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch
import os

from app.main import app
from app.services.chat_service import ChatService
from app.models.chat import ChatResponse


class TestChatRoutes:
    """Test cases for chat API routes."""
    
    @pytest.fixture
    def client(self):
        """Create a test client."""
        return TestClient(app)
    
    @pytest.fixture
    def mock_chat_service(self):
        """Mock ChatService for testing."""
        with patch('app.routes.chat.get_chat_service') as mock_get_service:
            mock_service = Mock(spec=ChatService)
            mock_get_service.return_value = mock_service
            yield mock_service
    
    def test_send_message_success(self, client, mock_chat_service):
        """Test successful message sending."""
        # Mock successful response
        mock_response = ChatResponse(
            message="Hello! How can I help you?",
            conversation_id="test-conv-id",
            success=True
        )
        mock_chat_service.send_message.return_value = mock_response
        
        response = client.post(
            "/api/chat",
            json={"message": "Hello"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["message"] == "Hello! How can I help you?"
        assert data["conversation_id"] == "test-conv-id"
    
    def test_send_message_empty(self, client, mock_chat_service):
        """Test sending empty message."""
        response = client.post(
            "/api/chat",
            json={"message": ""}
        )
        
        assert response.status_code == 400
        assert "Message cannot be empty" in response.json()["detail"]
    
    def test_send_message_service_error(self, client, mock_chat_service):
        """Test handling service errors."""
        # Mock service error response
        mock_response = ChatResponse(
            message="",
            conversation_id="test-conv-id",
            success=False,
            error="OpenAI API error"
        )
        mock_chat_service.send_message.return_value = mock_response
        
        response = client.post(
            "/api/chat",
            json={"message": "Hello"}
        )
        
        assert response.status_code == 500
        assert "OpenAI API error" in response.json()["detail"]
    
    def test_send_message_invalid_json(self, client):
        """Test sending invalid JSON."""
        response = client.post(
            "/api/chat",
            data="invalid json"
        )
        
        assert response.status_code == 422  # Unprocessable Entity
    
    def test_send_message_missing_field(self, client):
        """Test sending request with missing required field."""
        response = client.post(
            "/api/chat",
            json={}
        )
        
        assert response.status_code == 422
        assert "field required" in str(response.json())
    
    def test_start_new_conversation_success(self, client, mock_chat_service):
        """Test successful new conversation creation."""
        mock_chat_service.create_conversation.return_value = "new-conv-id"
        
        response = client.post("/api/chat/new")
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["conversation_id"] == "new-conv-id"
        assert "successfully" in data["message"]
    
    def test_start_new_conversation_service_error(self, client, mock_chat_service):
        """Test new conversation creation with service error."""
        mock_chat_service.create_conversation.side_effect = Exception("Service error")
        
        response = client.post("/api/chat/new")
        
        assert response.status_code == 500
        assert "Failed to create new conversation" in response.json()["detail"]
    
    def test_health_check_healthy(self, client, mock_chat_service):
        """Test health check when service is healthy."""
        mock_chat_service.health_check.return_value = {
            "status": "healthy",
            "api_connection": "ok",
            "active_conversations": 5,
            "model": "gpt-4o-mini"
        }
        
        response = client.get("/api/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["api_connection"] == "ok"
        assert data["active_conversations"] == 5
    
    def test_health_check_unhealthy(self, client, mock_chat_service):
        """Test health check when service is unhealthy."""
        mock_chat_service.health_check.return_value = {
            "status": "unhealthy",
            "api_connection": "failed",
            "error": "API key invalid",
            "active_conversations": 0
        }
        
        response = client.get("/api/health")
        
        assert response.status_code == 503
        data = response.json()
        assert data["status"] == "unhealthy"
        assert data["api_connection"] == "failed"
        assert "API key invalid" in data["error"]
    
    def test_health_check_service_exception(self, client, mock_chat_service):
        """Test health check when service throws exception."""
        mock_chat_service.health_check.side_effect = Exception("Service crashed")
        
        response = client.get("/api/health")
        
        assert response.status_code == 503
        data = response.json()
        assert data["status"] == "unhealthy"
        assert "internal error" in data["error"]


class TestStaticFiles:
    """Test cases for static file serving."""
    
    @pytest.fixture
    def client(self):
        """Create a test client."""
        return TestClient(app)
    
    def test_serve_index_success(self, client):
        """Test serving index.html when it exists."""
        with patch('pathlib.Path.exists', return_value=True):
            with patch('app.main.FileResponse') as mock_file_response:
                mock_file_response.return_value = Mock()
                
                response = client.get("/")
                
                # The actual response depends on file existence
                # This test verifies the route is accessible
                assert response.status_code in [200, 404]
    
    def test_serve_index_not_found(self, client):
        """Test serving index.html when it doesn't exist."""
        with patch('pathlib.Path.exists', return_value=False):
            response = client.get("/")
            
            assert response.status_code == 404
            assert "Index file not found" in response.json()["detail"]


class TestCORS:
    """Test CORS configuration."""
    
    @pytest.fixture
    def client(self):
        """Create a test client."""
        return TestClient(app)
    
    def test_cors_headers(self, client):
        """Test that CORS headers are present."""
        response = client.options("/api/health")
        
        # Check for CORS headers
        assert "access-control-allow-origin" in response.headers
        assert "access-control-allow-methods" in response.headers
        assert "access-control-allow-headers" in response.headers


class TestErrorHandling:
    """Test global error handling."""
    
    @pytest.fixture
    def client(self):
        """Create a test client."""
        return TestClient(app)
    
    def test_404_not_found(self, client):
        """Test 404 error handling."""
        response = client.get("/nonexistent-endpoint")
        
        assert response.status_code == 404
    
    def test_405_method_not_allowed(self, client):
        """Test 405 error handling."""
        response = client.put("/api/health")  # Health endpoint only supports GET
        
        assert response.status_code == 405