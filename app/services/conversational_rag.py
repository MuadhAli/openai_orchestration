"""
Conversational RAG Service - Simple Implementation
"""
import logging
import math
from typing import List, Tuple, Optional
from sqlalchemy.orm import Session as DBSession

from app.database.models import Message, MessageEmbedding, MessageRole
from app.services.embedding_service import EmbeddingService

logger = logging.getLogger(__name__)


class ConversationalRAGService:
    """Simple conversational RAG service."""
    
    def __init__(self, db_session: DBSession, embedding_service: EmbeddingService):
        self.db_session = db_session
        self.embedding_service = embedding_service
    
    async def store_message_embedding(self, message: Message) -> bool:
        """Store embedding for a message."""
        try:
            # Generate embedding
            embedding_result = await self.embedding_service.generate_embedding(message.content)
            
            # Create embedding record
            message_embedding = MessageEmbedding(
                message_id=message.id,
                session_id=message.session_id,
                content=message.content,
                role=message.role,
                embedding=embedding_result.embedding
            )
            
            self.db_session.add(message_embedding)
            self.db_session.commit()
            
            logger.info(f"Stored embedding for message {message.id}")
            return True
            
        except Exception as e:
            self.db_session.rollback()
            logger.error(f"Failed to store embedding: {str(e)}")
            return False
    
    async def find_relevant_conversations(
        self, 
        query: str, 
        current_session_id: str,
        limit: int = 5
    ) -> List[str]:
        """Find relevant past conversations."""
        try:
            # Generate query embedding
            query_embedding = await self.embedding_service.generate_embedding(query)
            
            # Get all message embeddings except current session
            embeddings = self.db_session.query(MessageEmbedding).filter(
                MessageEmbedding.session_id != current_session_id
            ).all()
            
            # Calculate similarities
            similarities = []
            for emb in embeddings:
                similarity = self._cosine_similarity(query_embedding.embedding, emb.embedding)
                if similarity > 0.7:  # Threshold
                    similarities.append((emb.content, emb.role.value, similarity))
            
            # Sort by similarity and return top results
            similarities.sort(key=lambda x: x[2], reverse=True)
            
            # Format results
            results = []
            for content, role, score in similarities[:limit]:
                results.append(f"{role}: {content}")
            
            return results
            
        except Exception as e:
            logger.error(f"Failed to find relevant conversations: {str(e)}")
            return []
    
    def _cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """Calculate cosine similarity between two vectors."""
        try:
            # Dot product
            dot_product = sum(a * b for a, b in zip(vec1, vec2))
            
            # Magnitudes
            magnitude1 = math.sqrt(sum(a * a for a in vec1))
            magnitude2 = math.sqrt(sum(a * a for a in vec2))
            
            if magnitude1 == 0 or magnitude2 == 0:
                return 0
            
            return dot_product / (magnitude1 * magnitude2)
            
        except Exception:
            return 0