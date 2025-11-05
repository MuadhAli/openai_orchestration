"""
ChromaDB service for vector database operations.
"""
import os
import logging
from typing import Optional, List, Dict, Any
from pathlib import Path
import chromadb
from chromadb.config import Settings
from chromadb.api.models.Collection import Collection

logger = logging.getLogger(__name__)

class ChromaDBService:
    """Service for managing ChromaDB local storage operations."""
    
    def __init__(self, persist_directory: Optional[str] = None):
        """
        Initialize ChromaDB service with persistent local storage.
        
        Args:
            persist_directory: Directory for persistent storage. Defaults to ./data/vector_db
        """
        self.persist_directory = persist_directory or os.path.join(".", "data", "vector_db")
        self.client: Optional[chromadb.Client] = None
        self.collections: Dict[str, Collection] = {}
        self._is_initialized = False
        
        # Ensure the persist directory exists
        Path(self.persist_directory).mkdir(parents=True, exist_ok=True)
    
    def initialize(self) -> bool:
        """
        Initialize ChromaDB client with persistent local storage.
        
        Returns:
            bool: True if initialization successful, False otherwise
        """
        try:
            # Create ChromaDB client with persistent storage
            self.client = chromadb.PersistentClient(
                path=self.persist_directory,
                settings=Settings(
                    anonymized_telemetry=False,
                    allow_reset=True
                )
            )
            
            self._is_initialized = True
            logger.info(f"ChromaDB initialized successfully with persist directory: {self.persist_directory}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize ChromaDB: {str(e)}")
            self._is_initialized = False
            return False
    
    def is_healthy(self) -> bool:
        """
        Check if ChromaDB connection is healthy.
        
        Returns:
            bool: True if healthy, False otherwise
        """
        try:
            if not self._is_initialized or self.client is None:
                return False
            
            # Try to list collections as a health check
            self.client.list_collections()
            return True
            
        except Exception as e:
            logger.error(f"ChromaDB health check failed: {str(e)}")
            return False
    
    def get_or_create_collection(self, name: str, metadata: Optional[Dict[str, Any]] = None) -> Optional[Collection]:
        """
        Get existing collection or create new one.
        
        Args:
            name: Collection name
            metadata: Optional metadata for the collection
            
        Returns:
            Collection object or None if failed
        """
        try:
            if not self._is_initialized or self.client is None:
                logger.error("ChromaDB not initialized")
                return None
            
            # Check if collection already exists in cache
            if name in self.collections:
                return self.collections[name]
            
            # Try to get existing collection first
            try:
                collection = self.client.get_collection(name=name)
                logger.info(f"Retrieved existing collection: {name}")
            except Exception:
                # Collection doesn't exist, create it
                collection = self.client.create_collection(
                    name=name,
                    metadata=metadata or {}
                )
                logger.info(f"Created new collection: {name}")
            
            # Cache the collection
            self.collections[name] = collection
            return collection
            
        except Exception as e:
            logger.error(f"Failed to get or create collection '{name}': {str(e)}")
            return None
    
    def delete_collection(self, name: str) -> bool:
        """
        Delete a collection.
        
        Args:
            name: Collection name to delete
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            if not self._is_initialized or self.client is None:
                logger.error("ChromaDB not initialized")
                return False
            
            self.client.delete_collection(name=name)
            
            # Remove from cache if exists
            if name in self.collections:
                del self.collections[name]
            
            logger.info(f"Deleted collection: {name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete collection '{name}': {str(e)}")
            return False
    
    def list_collections(self) -> List[str]:
        """
        List all collection names.
        
        Returns:
            List of collection names
        """
        try:
            if not self._is_initialized or self.client is None:
                logger.error("ChromaDB not initialized")
                return []
            
            collections = self.client.list_collections()
            return [col.name for col in collections]
            
        except Exception as e:
            logger.error(f"Failed to list collections: {str(e)}")
            return []
    
    def get_collection_count(self, collection_name: str) -> int:
        """
        Get the number of documents in a collection.
        
        Args:
            collection_name: Name of the collection
            
        Returns:
            Number of documents in the collection, -1 if error
        """
        try:
            collection = self.get_or_create_collection(collection_name)
            if collection is None:
                return -1
            
            return collection.count()
            
        except Exception as e:
            logger.error(f"Failed to get collection count for '{collection_name}': {str(e)}")
            return -1
    
    def reset_database(self) -> bool:
        """
        Reset the entire database (delete all collections and data).
        WARNING: This will delete all stored data!
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            if not self._is_initialized or self.client is None:
                logger.error("ChromaDB not initialized")
                return False
            
            self.client.reset()
            self.collections.clear()
            logger.warning("ChromaDB database has been reset - all data deleted!")
            return True
            
        except Exception as e:
            logger.error(f"Failed to reset database: {str(e)}")
            return False
    
    def close(self):
        """Close ChromaDB client and cleanup resources."""
        try:
            self.collections.clear()
            self.client = None
            self._is_initialized = False
            logger.info("ChromaDB service closed")
            
        except Exception as e:
            logger.error(f"Error closing ChromaDB service: {str(e)}")

# Global ChromaDB service instance
chroma_service = ChromaDBService()

def get_chroma_service() -> ChromaDBService:
    """
    Get the global ChromaDB service instance.
    
    Returns:
        ChromaDBService instance
    """
    return chroma_service

def initialize_vector_db() -> bool:
    """
    Initialize the vector database.
    
    Returns:
        bool: True if successful, False otherwise
    """
    return chroma_service.initialize()

def check_vector_db_health() -> bool:
    """
    Check vector database health.
    
    Returns:
        bool: True if healthy, False otherwise
    """
    return chroma_service.is_healthy()