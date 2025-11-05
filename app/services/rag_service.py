"""
RAG (Retrieval-Augmented Generation) service for context-aware response generation.
"""
import logging
import time
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass

from app.services.embedding_service import EmbeddingService
from app.repositories.vector_repository import VectorRepository
from app.models.vector import VectorSearchQuery, SimilarityResult
from app.models.message import Message, ConversationContext

logger = logging.getLogger(__name__)


@dataclass
class RetrievedDocument:
    """Document retrieved from vector search with metadata."""
    content: str
    similarity_score: float
    metadata: Dict[str, Any]
    source: str
    document_id: str


@dataclass
class RAGContext:
    """Combined context from chat history and retrieved documents."""
    session_id: str
    chat_history: List[Message]
    retrieved_documents: List[RetrievedDocument]
    total_tokens: int
    retrieval_time_ms: int
    query_used: str


class RAGServiceError(Exception):
    """Base exception for RAG service operations."""
    pass


class RAGService:
    """Service for Retrieval-Augmented Generation operations."""
    
    def __init__(self, 
                 vector_repository: VectorRepository,
                 embedding_service: EmbeddingService,
                 default_top_k: int = 5,
                 default_similarity_threshold: float = 0.7,
                 relevance_threshold: float = 0.6):
        """
        Initialize RAG service.
        
        Args:
            vector_repository: Vector repository for document storage and search
            embedding_service: Service for generating embeddings
            default_top_k: Default number of documents to retrieve
            default_similarity_threshold: Default similarity threshold for retrieval
            relevance_threshold: Minimum relevance score for filtering results
        """
        self.vector_repository = vector_repository
        self.embedding_service = embedding_service
        self.default_top_k = default_top_k
        self.default_similarity_threshold = default_similarity_threshold
        self.relevance_threshold = relevance_threshold
        
        logger.info(f"RAGService initialized with top_k={default_top_k}, "
                   f"similarity_threshold={default_similarity_threshold}, "
                   f"relevance_threshold={relevance_threshold}") 
   
    def retrieve_context(self, 
                        query: str, 
                        top_k: Optional[int] = None,
                        similarity_threshold: Optional[float] = None,
                        metadata_filter: Optional[Dict[str, Any]] = None) -> List[RetrievedDocument]:
        """
        Retrieve relevant documents for a query using vector similarity search.
        
        Args:
            query: Query text to search for
            top_k: Number of documents to retrieve (uses default if None)
            similarity_threshold: Minimum similarity score (uses default if None)
            metadata_filter: Optional metadata filter for documents
            
        Returns:
            List of retrieved documents with similarity scores
            
        Raises:
            RAGServiceError: If retrieval fails
        """
        try:
            if not query or not query.strip():
                logger.warning("Empty query provided to retrieve_context")
                return []
            
            # Use provided values or defaults
            k = top_k if top_k is not None else self.default_top_k
            threshold = similarity_threshold if similarity_threshold is not None else self.default_similarity_threshold
            
            # Create search query
            search_query = VectorSearchQuery(
                query_text=query.strip(),
                top_k=k,
                similarity_threshold=threshold,
                metadata_filter=metadata_filter
            )
            
            # Perform vector search
            start_time = time.time()
            search_response = self.vector_repository.search_similar(search_query)
            search_time_ms = int((time.time() - start_time) * 1000)
            
            # Convert to RetrievedDocument objects and apply relevance filtering
            retrieved_docs = []
            for result in search_response.results:
                # Apply additional relevance filtering
                if result.similarity_score >= self.relevance_threshold:
                    retrieved_doc = RetrievedDocument(
                        content=result.content,
                        similarity_score=result.similarity_score,
                        metadata=result.metadata,
                        source="vector_search",
                        document_id=result.document_id
                    )
                    retrieved_docs.append(retrieved_doc)
            
            # Sort by similarity score (descending)
            retrieved_docs.sort(key=lambda x: x.similarity_score, reverse=True)
            
            logger.info(f"Retrieved {len(retrieved_docs)} relevant documents for query "
                       f"(filtered from {len(search_response.results)} results) in {search_time_ms}ms")
            
            return retrieved_docs
            
        except Exception as e:
            logger.error(f"Failed to retrieve context for query '{query}': {str(e)}")
            raise RAGServiceError(f"Context retrieval failed: {str(e)}")
    
    def rank_documents(self, documents: List[RetrievedDocument], query: str) -> List[RetrievedDocument]:
        """
        Apply additional ranking to retrieved documents based on relevance.
        
        Args:
            documents: List of retrieved documents
            query: Original query for relevance scoring
            
        Returns:
            Re-ranked list of documents
        """
        try:
            if not documents:
                return documents
            
            # For now, use simple similarity-based ranking
            # In the future, this could include more sophisticated ranking algorithms
            ranked_docs = []
            
            for doc in documents:
                # Calculate relevance score based on multiple factors
                relevance_score = self._calculate_relevance_score(doc, query)
                
                # Update the document with the new relevance score
                doc.similarity_score = relevance_score
                ranked_docs.append(doc)
            
            # Sort by relevance score (descending)
            ranked_docs.sort(key=lambda x: x.similarity_score, reverse=True)
            
            logger.debug(f"Re-ranked {len(ranked_docs)} documents based on relevance")
            return ranked_docs
            
        except Exception as e:
            logger.error(f"Failed to rank documents: {str(e)}")
            # Return original documents if ranking fails
            return documents
    
    def _calculate_relevance_score(self, document: RetrievedDocument, query: str) -> float:
        """
        Calculate relevance score for a document based on multiple factors.
        
        Args:
            document: Retrieved document
            query: Original query
            
        Returns:
            Relevance score between 0.0 and 1.0
        """
        try:
            # Start with similarity score
            relevance_score = document.similarity_score
            
            # Apply content length penalty for very short or very long documents
            content_length = len(document.content)
            if content_length < 50:  # Very short documents might be less useful
                relevance_score *= 0.8
            elif content_length > 5000:  # Very long documents might be too verbose
                relevance_score *= 0.9
            
            # Boost score for documents with query terms in metadata
            query_terms = set(query.lower().split())
            metadata_text = " ".join(str(v).lower() for v in document.metadata.values())
            metadata_matches = sum(1 for term in query_terms if term in metadata_text)
            if metadata_matches > 0:
                relevance_score *= (1.0 + 0.1 * metadata_matches)
            
            # Ensure score stays within bounds
            return max(0.0, min(1.0, relevance_score))
            
        except Exception as e:
            logger.warning(f"Error calculating relevance score: {str(e)}")
            return document.similarity_score
    
    def filter_by_relevance(self, documents: List[RetrievedDocument], 
                           min_relevance: Optional[float] = None) -> List[RetrievedDocument]:
        """
        Filter documents by minimum relevance threshold.
        
        Args:
            documents: List of retrieved documents
            min_relevance: Minimum relevance score (uses class default if None)
            
        Returns:
            Filtered list of documents
        """
        try:
            if not documents:
                return documents
            
            threshold = min_relevance if min_relevance is not None else self.relevance_threshold
            
            filtered_docs = [
                doc for doc in documents 
                if doc.similarity_score >= threshold
            ]
            
            logger.debug(f"Filtered {len(documents)} documents to {len(filtered_docs)} "
                        f"using relevance threshold {threshold}")
            
            return filtered_docs
            
        except Exception as e:
            logger.error(f"Failed to filter documents by relevance: {str(e)}")
            return documents
    
    def create_rag_context(self, 
                          session_id: str,
                          query: str,
                          chat_history: List[Message],
                          top_k: Optional[int] = None,
                          similarity_threshold: Optional[float] = None,
                          metadata_filter: Optional[Dict[str, Any]] = None) -> RAGContext:
        """
        Create complete RAG context combining chat history and retrieved documents.
        
        Args:
            session_id: Session identifier
            query: Query for document retrieval
            chat_history: Recent chat messages
            top_k: Number of documents to retrieve
            similarity_threshold: Minimum similarity threshold
            metadata_filter: Optional metadata filter
            
        Returns:
            RAGContext with combined information
            
        Raises:
            RAGServiceError: If context creation fails
        """
        try:
            start_time = time.time()
            
            # Retrieve relevant documents
            retrieved_docs = self.retrieve_context(
                query=query,
                top_k=top_k,
                similarity_threshold=similarity_threshold,
                metadata_filter=metadata_filter
            )
            
            # Apply additional ranking
            ranked_docs = self.rank_documents(retrieved_docs, query)
            
            # Calculate total tokens (rough estimate)
            total_tokens = 0
            for message in chat_history:
                total_tokens += message.token_count or len(message.content.split()) * 1.3
            
            for doc in ranked_docs:
                total_tokens += len(doc.content.split()) * 1.3
            
            retrieval_time_ms = int((time.time() - start_time) * 1000)
            
            context = RAGContext(
                session_id=session_id,
                chat_history=chat_history,
                retrieved_documents=ranked_docs,
                total_tokens=int(total_tokens),
                retrieval_time_ms=retrieval_time_ms,
                query_used=query
            )
            
            logger.info(f"Created RAG context for session {session_id}: "
                       f"{len(chat_history)} messages, {len(ranked_docs)} documents, "
                       f"~{total_tokens} tokens in {retrieval_time_ms}ms")
            
            return context
            
        except Exception as e:
            logger.error(f"Failed to create RAG context: {str(e)}")
            raise RAGServiceError(f"RAG context creation failed: {str(e)}")


# Global RAG service instance
rag_service: Optional[RAGService] = None

def get_rag_service() -> RAGService:
    """
    Get the global RAG service instance.
    
    Returns:
        RAGService instance
        
    Raises:
        RuntimeError: If service is not initialized
    """
    global rag_service
    if rag_service is None:
        raise RuntimeError("RAG service not initialized. Call initialize_rag_service() first.")
    return rag_service

def initialize_rag_service(vector_repository: VectorRepository,
                          embedding_service: EmbeddingService,
                          default_top_k: int = 5,
                          default_similarity_threshold: float = 0.7,
                          relevance_threshold: float = 0.6) -> bool:
    """
    Initialize the global RAG service.
    
    Args:
        vector_repository: Vector repository instance
        embedding_service: Embedding service instance
        default_top_k: Default number of documents to retrieve
        default_similarity_threshold: Default similarity threshold
        relevance_threshold: Minimum relevance threshold
        
    Returns:
        bool: True if successful, False otherwise
    """
    global rag_service
    try:
        rag_service = RAGService(
            vector_repository=vector_repository,
            embedding_service=embedding_service,
            default_top_k=default_top_k,
            default_similarity_threshold=default_similarity_threshold,
            relevance_threshold=relevance_threshold
        )
        logger.info("Global RAG service initialized successfully")
        return True
    except Exception as e:
        logger.error(f"Failed to initialize RAG service: {str(e)}")
        return False

def check_rag_service_health() -> bool:
    """
    Check if RAG service is healthy.
    
    Returns:
        bool: True if healthy, False otherwise
    """
    try:
        service = get_rag_service()
        # Try a simple retrieval as health check
        test_docs = service.retrieve_context("health check", top_k=1)
        return True  # If no exception, service is healthy
    except Exception as e:
        logger.error(f"RAG service health check failed: {str(e)}")
        return False