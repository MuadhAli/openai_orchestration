"""
Unit tests for RAG service functionality.
"""
import pytest
from unittest.mock import Mock, MagicMock, patch
from datetime import datetime
from typing import List

from app.services.rag_service import (
    RAGService, RAGServiceError, RetrievedDocument, RAGContext,
    initialize_rag_service, get_rag_service, check_rag_service_health
)
from app.models.vector import VectorSearchQuery, VectorSearchResponse, SimilarityResult
from app.models.message import Message


class TestRAGService:
    """Test cases for RAGService class."""
    
    @pytest.fixture
    def mock_vector_repository(self):
        """Mock vector repository."""
        return Mock()
    
    @pytest.fixture
    def mock_embedding_service(self):
        """Mock embedding service."""
        return Mock()
    
    @pytest.fixture
    def rag_service(self, mock_vector_repository, mock_embedding_service):
        """RAG service instance with mocked dependencies."""
        return RAGService(
            vector_repository=mock_vector_repository,
            embedding_service=mock_embedding_service,
            default_top_k=3,
            default_similarity_threshold=0.7,
            relevance_threshold=0.6
        )
    
    @pytest.fixture
    def sample_search_results(self):
        """Sample search results for testing."""
        return [
            SimilarityResult(
                document_id="doc1",
                content="This is a test document about Python programming.",
                similarity_score=0.9,
                metadata={"topic": "programming", "language": "python"},
                distance=0.1
            ),
            SimilarityResult(
                document_id="doc2", 
                content="Machine learning algorithms are powerful tools.",
                similarity_score=0.8,
                metadata={"topic": "ml", "category": "algorithms"},
                distance=0.2
            ),
            SimilarityResult(
                document_id="doc3",
                content="Short doc",
                similarity_score=0.5,
                metadata={},
                distance=0.5
            )
        ]
    
    @pytest.fixture
    def sample_messages(self):
        """Sample chat messages for testing."""
        return [
            Message(
                id="msg1",
                session_id="session1",
                content="What is Python?",
                role="user",
                timestamp=datetime.now(),
                token_count=10,
                message_metadata={}
            ),
            Message(
                id="msg2",
                session_id="session1", 
                content="Python is a programming language.",
                role="assistant",
                timestamp=datetime.now(),
                token_count=15,
                message_metadata={}
            )
        ]
    
    def test_initialization(self, mock_vector_repository, mock_embedding_service):
        """Test RAG service initialization."""
        service = RAGService(
            vector_repository=mock_vector_repository,
            embedding_service=mock_embedding_service,
            default_top_k=5,
            default_similarity_threshold=0.8,
            relevance_threshold=0.7
        )
        
        assert service.vector_repository == mock_vector_repository
        assert service.embedding_service == mock_embedding_service
        assert service.default_top_k == 5
        assert service.default_similarity_threshold == 0.8
        assert service.relevance_threshold == 0.7
    
    def test_retrieve_context_success(self, rag_service, mock_vector_repository, sample_search_results):
        """Test successful context retrieval."""
        # Mock vector repository response
        mock_response = VectorSearchResponse(
            query="test query",
            results=sample_search_results,
            total_results=3,
            search_time_ms=100,
            used_fallback=False
        )
        mock_vector_repository.search_similar.return_value = mock_response
        
        # Test retrieval
        result = rag_service.retrieve_context("test query", top_k=3)
        
        # Verify results (should filter out doc3 due to low similarity)
        assert len(result) == 2  # doc3 filtered out (0.5 < 0.6 threshold)
        assert result[0].document_id == "doc1"
        assert result[0].similarity_score == 0.9
        assert result[1].document_id == "doc2"
        assert result[1].similarity_score == 0.8
        
        # Verify vector repository was called correctly
        mock_vector_repository.search_similar.assert_called_once()
        call_args = mock_vector_repository.search_similar.call_args[0][0]
        assert call_args.query_text == "test query"
        assert call_args.top_k == 3
    
    def test_retrieve_context_empty_query(self, rag_service):
        """Test retrieval with empty query."""
        result = rag_service.retrieve_context("")
        assert result == []
        
        result = rag_service.retrieve_context("   ")
        assert result == []
    
    def test_retrieve_context_with_defaults(self, rag_service, mock_vector_repository, sample_search_results):
        """Test retrieval using default parameters."""
        mock_response = VectorSearchResponse(
            query="test",
            results=sample_search_results,
            total_results=3,
            search_time_ms=50,
            used_fallback=False
        )
        mock_vector_repository.search_similar.return_value = mock_response
        
        result = rag_service.retrieve_context("test")
        
        # Should use default values
        call_args = mock_vector_repository.search_similar.call_args[0][0]
        assert call_args.top_k == 3  # default_top_k
        assert call_args.similarity_threshold == 0.7  # default_similarity_threshold
    
    def test_retrieve_context_repository_error(self, rag_service, mock_vector_repository):
        """Test handling of repository errors."""
        mock_vector_repository.search_similar.side_effect = Exception("Repository error")
        
        with pytest.raises(RAGServiceError, match="Context retrieval failed"):
            rag_service.retrieve_context("test query")
    
    def test_rank_documents(self, rag_service):
        """Test document ranking functionality."""
        docs = [
            RetrievedDocument(
                content="Python programming tutorial",
                similarity_score=0.8,
                metadata={"topic": "programming"},
                source="vector_search",
                document_id="doc1"
            ),
            RetrievedDocument(
                content="Short",  # Very short content
                similarity_score=0.9,
                metadata={},
                source="vector_search", 
                document_id="doc2"
            )
        ]
        
        ranked = rag_service.rank_documents(docs, "python programming")
        
        # Should be sorted by relevance score
        assert len(ranked) == 2
        # First doc should have higher score due to content length penalty on second doc
        assert ranked[0].document_id == "doc1"
    
    def test_filter_by_relevance(self, rag_service):
        """Test relevance filtering."""
        docs = [
            RetrievedDocument("content1", 0.8, {}, "source", "doc1"),
            RetrievedDocument("content2", 0.5, {}, "source", "doc2"),
            RetrievedDocument("content3", 0.7, {}, "source", "doc3")
        ]
        
        # Use default threshold (0.6)
        filtered = rag_service.filter_by_relevance(docs)
        assert len(filtered) == 2
        assert filtered[0].similarity_score == 0.8
        assert filtered[1].similarity_score == 0.7
        
        # Use custom threshold
        filtered = rag_service.filter_by_relevance(docs, min_relevance=0.75)
        assert len(filtered) == 1
        assert filtered[0].similarity_score == 0.8    

    def test_create_rag_context(self, rag_service, mock_vector_repository, sample_search_results, sample_messages):
        """Test RAG context creation."""
        # Mock vector repository response
        mock_response = VectorSearchResponse(
            query="test query",
            results=sample_search_results,
            total_results=3,
            search_time_ms=100,
            used_fallback=False
        )
        mock_vector_repository.search_similar.return_value = mock_response
        
        # Create RAG context
        context = rag_service.create_rag_context(
            session_id="session1",
            query="test query",
            chat_history=sample_messages,
            top_k=3
        )
        
        # Verify context
        assert context.session_id == "session1"
        assert context.query_used == "test query"
        assert len(context.chat_history) == 2
        assert len(context.retrieved_documents) == 2  # Filtered by relevance
        assert context.total_tokens > 0
        assert context.retrieval_time_ms > 0
    
    def test_calculate_relevance_score(self, rag_service):
        """Test relevance score calculation."""
        # Normal document
        doc1 = RetrievedDocument(
            content="This is a normal length document about Python programming.",
            similarity_score=0.8,
            metadata={"topic": "python"},
            source="vector_search",
            document_id="doc1"
        )
        
        score1 = rag_service._calculate_relevance_score(doc1, "python programming")
        assert score1 > 0.8  # Should be boosted due to metadata match
        
        # Very short document
        doc2 = RetrievedDocument(
            content="Short",
            similarity_score=0.8,
            metadata={},
            source="vector_search",
            document_id="doc2"
        )
        
        score2 = rag_service._calculate_relevance_score(doc2, "test")
        assert score2 < 0.8  # Should be penalized for being too short


class TestGlobalRAGService:
    """Test cases for global RAG service functions."""
    
    def test_initialize_rag_service(self):
        """Test global RAG service initialization."""
        mock_vector_repo = Mock()
        mock_embedding_service = Mock()
        
        result = initialize_rag_service(mock_vector_repo, mock_embedding_service)
        assert result is True
        
        # Should be able to get the service
        service = get_rag_service()
        assert service is not None
        assert service.vector_repository == mock_vector_repo
    
    def test_get_rag_service_not_initialized(self):
        """Test getting RAG service when not initialized."""
        # Reset global service
        import app.services.rag_service
        app.services.rag_service.rag_service = None
        
        with pytest.raises(RuntimeError, match="RAG service not initialized"):
            get_rag_service()
    
    @patch('app.services.rag_service.get_rag_service')
    def test_check_rag_service_health_success(self, mock_get_service):
        """Test successful health check."""
        mock_service = Mock()
        mock_service.retrieve_context.return_value = []
        mock_get_service.return_value = mock_service
        
        result = check_rag_service_health()
        assert result is True
        mock_service.retrieve_context.assert_called_once_with("health check", top_k=1)
    
    @patch('app.services.rag_service.get_rag_service')
    def test_check_rag_service_health_failure(self, mock_get_service):
        """Test health check failure."""
        mock_get_service.side_effect = Exception("Service error")
        
        result = check_rag_service_health()
        assert result is False