"""
Simple service for creating embeddings using OpenAI.
"""
import logging
import os
from typing import List, Optional
import openai
from openai import OpenAI

logger = logging.getLogger(__name__)


class EmbeddingService:
    """Simple service for creating text embeddings."""
    
    def __init__(self):
        """Initialize the embedding service."""
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.model = "text-embedding-ada-002"
    
    def create_embedding(self, text: str) -> List[float]:
        """Create embedding for a single text."""
        try:
            if not text or not text.strip():
                raise ValueError("Text cannot be empty")
            
            response = self.client.embeddings.create(
                model=self.model,
                input=text.strip()
            )
            
            embedding = response.data[0].embedding
            logger.info(f"Created embedding for text of length {len(text)}")
            return embedding
            
        except Exception as e:
            logger.error(f"Error creating embedding: {str(e)}")
            raise Exception(f"Failed to create embedding: {str(e)}")
    
    def create_embeddings_batch(self, texts: List[str]) -> List[List[float]]:
        """Create embeddings for multiple texts."""
        try:
            if not texts:
                return []
            
            # Filter out empty texts
            valid_texts = [text.strip() for text in texts if text and text.strip()]
            
            if not valid_texts:
                return []
            
            response = self.client.embeddings.create(
                model=self.model,
                input=valid_texts
            )
            
            embeddings = [data.embedding for data in response.data]
            logger.info(f"Created {len(embeddings)} embeddings")
            return embeddings
            
        except Exception as e:
            logger.error(f"Error creating batch embeddings: {str(e)}")
            raise Exception(f"Failed to create batch embeddings: {str(e)}")
    
    def chunk_text(self, text: str, chunk_size: int = 1000, overlap: int = 100) -> List[str]:
        """Split text into chunks for embedding."""
        if not text or not text.strip():
            return []
        
        text = text.strip()
        
        # If text is shorter than chunk size, return as single chunk
        if len(text) <= chunk_size:
            return [text]
        
        chunks = []
        start = 0
        
        while start < len(text):
            end = start + chunk_size
            
            # If this is not the last chunk, try to break at a sentence or word boundary
            if end < len(text):
                # Look for sentence boundary (. ! ?)
                sentence_end = max(
                    text.rfind('.', start, end),
                    text.rfind('!', start, end),
                    text.rfind('?', start, end)
                )
                
                if sentence_end > start:
                    end = sentence_end + 1
                else:
                    # Look for word boundary
                    word_end = text.rfind(' ', start, end)
                    if word_end > start:
                        end = word_end
            
            chunk = text[start:end].strip()
            if chunk:
                chunks.append(chunk)
            
            # Move start position with overlap
            start = end - overlap if end < len(text) else end
        
        logger.info(f"Split text into {len(chunks)} chunks")
        return chunks