"""
Vector repository with ChromaDB and MySQL fallback support.
"""
import logging
import json
import pickle
import time
import numpy as np
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.models.vector import (
    DocumentCreate, DocumentUpdate, DocumentResponse, SimilarityResult,
    VectorSearchQuery, VectorSearchResponse, CollectionStats,
    BulkDocumentCreate, BulkDocumentResponse, VectorRepositoryConfig
)
from app.database.models import Embedding
from app.database.config import get_database_session
from app.services.vector_db_service import ChromaDBService
from app.services.embedding_service import EmbeddingService

logger = logging.getLogger(__name__)


class VectorRepository:
    """Repository for vector operations with ChromaDB and MySQL fallback."""
    
    def __init__(self, 
                 config: VectorRepositoryConfig,
                 chroma_service: ChromaDBService,
                 embedding_service: EmbeddingService,
                 db_session: Optional[Session] = None):
        """
        Initialize vector repository.
        
        Args:
            config: Repository configuration
            chroma_service: ChromaDB service instance
            embedding_service: Embedding service instance
            db_session: Database session (optional, will create if not provided)
        """
        self.config = config
        self.chroma_service = chroma_service
        self.embedding_service = embedding_service
        self.db_session = db_session
        self._use_chromadb = config.use_chromadb
        self._collection = None
        
        # Initialize ChromaDB if enabled
        if self._use_chromadb:
            self._initialize_chromadb()
    
    def _initialize_chromadb(self) -> bool:
        """
        Initialize ChromaDB collection.
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            if not self.chroma_service.is_healthy():
                logger.warning("ChromaDB not healthy, will use MySQL fallback")
                self._use_chromadb = False
                return False
            
            self._collection = self.chroma_service.get_or_create_collection(
                name=self.config.collection_name,
                metadata={
                    "embedding_dimension": self.config.embedding_dimension,
                    "similarity_metric": self.config.similarity_metric,
                    "created_at": datetime.now().isoformat()
                }
            )
            
            if self._collection is None:
                logger.warning("Failed to create ChromaDB collection, using MySQL fallback")
                self._use_chromadb = False
                return False
            
            logger.info(f"ChromaDB collection '{self.config.collection_name}' initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize ChromaDB: {str(e)}")
            self._use_chromadb = False
            return False
    
    def _get_db_session(self) -> Session:
        """Get database session."""
        if self.db_session:
            return self.db_session
        return next(get_database_session())
    
    def _serialize_embedding(self, embedding: List[float]) -> bytes:
        """Serialize embedding vector for MySQL storage."""
        return pickle.dumps(embedding)
    
    def _deserialize_embedding(self, data: bytes) -> List[float]:
        """Deserialize embedding vector from MySQL storage."""
        return pickle.loads(data)
    
    def _calculate_cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """Calculate cosine similarity between two vectors."""
        try:
            # Convert to numpy arrays for efficient computation
            a = np.array(vec1)
            b = np.array(vec2)
            
            # Calculate cosine similarity
            dot_product = np.dot(a, b)
            norm_a = np.linalg.norm(a)
            norm_b = np.linalg.norm(b)
            
            if norm_a == 0 or norm_b == 0:
                return 0.0
            
            similarity = dot_product / (norm_a * norm_b)
            
            # Ensure result is between 0 and 1
            return max(0.0, min(1.0, (similarity + 1) / 2))
            
        except Exception as e:
            logger.error(f"Error calculating cosine similarity: {str(e)}")
            return 0.0
    
    def add_document(self, document: DocumentCreate) -> DocumentResponse:
        """
        Add a single document to the vector store.
        
        Args:
            document: Document to add
            
        Returns:
            DocumentResponse with created document info
            
        Raises:
            Exception: If document creation fails
        """
        try:
            # Generate embedding
            embedding_result = self.embedding_service.generate_embedding(document.content)
            
            # Generate document ID
            doc_id = f"doc_{int(time.time() * 1000000)}"
            created_at = datetime.now()
            
            # Try ChromaDB first
            if self._use_chromadb and self._collection:
                try:
                    self._collection.add(
                        ids=[doc_id],
                        documents=[document.content],
                        embeddings=[embedding_result.embedding],
                        metadatas=[{
                            **document.metadata,
                            "created_at": created_at.isoformat(),
                            "token_count": embedding_result.token_count
                        }]
                    )
                    
                    logger.debug(f"Document {doc_id} added to ChromaDB")
                    
                    return DocumentResponse(
                        id=doc_id,
                        content=document.content,
                        metadata=document.metadata,
                        created_at=created_at
                    )
                    
                except Exception as e:
                    logger.warning(f"ChromaDB add failed, falling back to MySQL: {str(e)}")
                    self._use_chromadb = False
            
            # Fallback to MySQL
            db_session = self._get_db_session()
            try:
                embedding_record = Embedding(
                    id=doc_id,
                    content=document.content,
                    embedding=self._serialize_embedding(embedding_result.embedding),
                    embedding_metadata={
                        **document.metadata,
                        "created_at": created_at.isoformat(),
                        "token_count": embedding_result.token_count,
                        "embedding_dimension": len(embedding_result.embedding)
                    },
                    created_at=created_at
                )
                
                db_session.add(embedding_record)
                db_session.commit()
                
                logger.debug(f"Document {doc_id} added to MySQL")
                
                return DocumentResponse(
                    id=doc_id,
                    content=document.content,
                    metadata=document.metadata,
                    created_at=created_at
                )
                
            except Exception as e:
                db_session.rollback()
                raise Exception(f"Failed to add document to MySQL: {str(e)}")
            finally:
                if not self.db_session:  # Only close if we created the session
                    db_session.close()
                    
        except Exception as e:
            logger.error(f"Failed to add document: {str(e)}")
            raise
    
    def add_documents_bulk(self, bulk_request: BulkDocumentCreate, progress_callback=None) -> BulkDocumentResponse:
        """
        Add multiple documents in bulk with progress tracking.
        
        Args:
            bulk_request: Bulk document creation request
            progress_callback: Optional callback function for progress updates (current, total)
            
        Returns:
            BulkDocumentResponse with results
        """
        start_time = time.time()
        created_documents = []
        failed_documents = []
        total_documents = len(bulk_request.documents)
        
        logger.info(f"Starting bulk document ingestion: {total_documents} documents")
        
        for i, document in enumerate(bulk_request.documents):
            try:
                result = self.add_document(document)
                created_documents.append(result)
                
                # Progress tracking
                if progress_callback:
                    progress_callback(i + 1, total_documents)
                
                # Log progress every 10% or every 100 documents
                if (i + 1) % max(1, total_documents // 10) == 0 or (i + 1) % 100 == 0:
                    progress_pct = ((i + 1) / total_documents) * 100
                    logger.info(f"Bulk ingestion progress: {i + 1}/{total_documents} ({progress_pct:.1f}%)")
                    
            except Exception as e:
                failed_documents.append({
                    "index": i,
                    "document": document.model_dump(),
                    "error": str(e)
                })
                logger.error(f"Failed to add document at index {i}: {str(e)}")
        
        processing_time_ms = int((time.time() - start_time) * 1000)
        
        logger.info(f"Bulk ingestion completed: {len(created_documents)} created, {len(failed_documents)} failed, "
                   f"time: {processing_time_ms}ms")
        
        return BulkDocumentResponse(
            created_documents=created_documents,
            failed_documents=failed_documents,
            total_requested=len(bulk_request.documents),
            total_created=len(created_documents),
            total_failed=len(failed_documents),
            processing_time_ms=processing_time_ms
        )
    
    def search_similar(self, query: VectorSearchQuery) -> VectorSearchResponse:
        """
        Search for similar documents.
        
        Args:
            query: Search query parameters
            
        Returns:
            VectorSearchResponse with results
        """
        start_time = time.time()
        used_fallback = False
        
        try:
            # Generate query embedding
            embedding_result = self.embedding_service.generate_embedding(query.query_text)
            query_embedding = embedding_result.embedding
            
            # Try ChromaDB first
            if self._use_chromadb and self._collection:
                try:
                    results = self._search_chromadb(query_embedding, query)
                    search_time_ms = int((time.time() - start_time) * 1000)
                    
                    return VectorSearchResponse(
                        query=query.query_text,
                        results=results,
                        total_results=len(results),
                        search_time_ms=search_time_ms,
                        used_fallback=False
                    )
                    
                except Exception as e:
                    logger.warning(f"ChromaDB search failed, falling back to MySQL: {str(e)}")
                    self._use_chromadb = False
                    used_fallback = True
            
            # Fallback to MySQL
            results = self._search_mysql(query_embedding, query)
            search_time_ms = int((time.time() - start_time) * 1000)
            
            return VectorSearchResponse(
                query=query.query_text,
                results=results,
                total_results=len(results),
                search_time_ms=search_time_ms,
                used_fallback=used_fallback or not self.config.use_chromadb
            )
            
        except Exception as e:
            logger.error(f"Search failed: {str(e)}")
            raise
    
    def _search_chromadb(self, query_embedding: List[float], query: VectorSearchQuery) -> List[SimilarityResult]:
        """Search using ChromaDB."""
        try:
            # Prepare where clause for metadata filtering
            where_clause = None
            if query.metadata_filter:
                where_clause = query.metadata_filter
            
            # Perform search
            results = self._collection.query(
                query_embeddings=[query_embedding],
                n_results=query.top_k,
                where=where_clause
            )
            
            # Process results
            similarity_results = []
            
            if results['ids'] and results['ids'][0]:
                for i in range(len(results['ids'][0])):
                    doc_id = results['ids'][0][i]
                    content = results['documents'][0][i]
                    distance = results['distances'][0][i]
                    metadata = results['metadatas'][0][i] if results['metadatas'][0] else {}
                    
                    # Convert distance to similarity score (ChromaDB uses distance, lower is better)
                    # For cosine distance: similarity = 1 - distance
                    similarity_score = max(0.0, min(1.0, 1.0 - distance))
                    
                    # Apply similarity threshold
                    if similarity_score >= query.similarity_threshold:
                        similarity_results.append(SimilarityResult(
                            document_id=doc_id,
                            content=content,
                            similarity_score=similarity_score,
                            metadata=metadata,
                            distance=distance
                        ))
            
            return similarity_results
            
        except Exception as e:
            logger.error(f"ChromaDB search error: {str(e)}")
            raise
    
    def _search_mysql(self, query_embedding: List[float], query: VectorSearchQuery) -> List[SimilarityResult]:
        """Search using MySQL fallback."""
        db_session = self._get_db_session()
        
        try:
            # Get all embeddings (this is not efficient for large datasets)
            embeddings = db_session.query(Embedding).all()
            
            # Calculate similarities
            similarities = []
            for embedding_record in embeddings:
                try:
                    stored_embedding = self._deserialize_embedding(embedding_record.embedding)
                    similarity_score = self._calculate_cosine_similarity(query_embedding, stored_embedding)
                    
                    # Apply similarity threshold
                    if similarity_score >= query.similarity_threshold:
                        # Apply metadata filter if specified
                        if query.metadata_filter:
                            metadata = embedding_record.embedding_metadata or {}
                            if not self._matches_metadata_filter(metadata, query.metadata_filter):
                                continue
                        
                        similarities.append((similarity_score, embedding_record))
                
                except Exception as e:
                    logger.warning(f"Error processing embedding {embedding_record.id}: {str(e)}")
                    continue
            
            # Sort by similarity (descending) and take top_k
            similarities.sort(key=lambda x: x[0], reverse=True)
            similarities = similarities[:query.top_k]
            
            # Convert to SimilarityResult objects
            results = []
            for similarity_score, embedding_record in similarities:
                results.append(SimilarityResult(
                    document_id=embedding_record.id,
                    content=embedding_record.content,
                    similarity_score=similarity_score,
                    metadata=embedding_record.embedding_metadata or {},
                    distance=1.0 - similarity_score  # Convert similarity to distance
                ))
            
            return results
            
        except Exception as e:
            logger.error(f"MySQL search error: {str(e)}")
            raise
        finally:
            if not self.db_session:
                db_session.close()
    
    def _matches_metadata_filter(self, metadata: Dict[str, Any], filter_criteria: Dict[str, Any]) -> bool:
        """Check if metadata matches filter criteria."""
        for key, value in filter_criteria.items():
            if key not in metadata or metadata[key] != value:
                return False
        return True
    
    def get_document(self, document_id: str) -> Optional[DocumentResponse]:
        """
        Get a document by ID.
        
        Args:
            document_id: Document ID
            
        Returns:
            DocumentResponse if found, None otherwise
        """
        try:
            # Try ChromaDB first
            if self._use_chromadb and self._collection:
                try:
                    results = self._collection.get(ids=[document_id])
                    
                    if results['ids'] and results['ids'][0]:
                        content = results['documents'][0]
                        metadata = results['metadatas'][0] if results['metadatas'] else {}
                        
                        # Extract created_at from metadata
                        created_at_str = metadata.get('created_at')
                        created_at = datetime.fromisoformat(created_at_str) if created_at_str else datetime.now()
                        
                        return DocumentResponse(
                            id=document_id,
                            content=content,
                            metadata={k: v for k, v in metadata.items() if k not in ['created_at', 'token_count']},
                            created_at=created_at
                        )
                        
                except Exception as e:
                    logger.warning(f"ChromaDB get failed, trying MySQL: {str(e)}")
            
            # Fallback to MySQL
            db_session = self._get_db_session()
            try:
                embedding_record = db_session.query(Embedding).filter(Embedding.id == document_id).first()
                
                if embedding_record:
                    metadata = embedding_record.embedding_metadata or {}
                    return DocumentResponse(
                        id=embedding_record.id,
                        content=embedding_record.content,
                        metadata={k: v for k, v in metadata.items() if k not in ['created_at', 'token_count', 'embedding_dimension']},
                        created_at=embedding_record.created_at
                    )
                
                return None
                
            finally:
                if not self.db_session:
                    db_session.close()
                    
        except Exception as e:
            logger.error(f"Failed to get document {document_id}: {str(e)}")
            return None
    
    def update_document(self, document_id: str, update: DocumentUpdate) -> Optional[DocumentResponse]:
        """
        Update a document.
        
        Args:
            document_id: Document ID
            update: Update data
            
        Returns:
            Updated DocumentResponse if successful, None otherwise
        """
        try:
            # Get existing document first
            existing_doc = self.get_document(document_id)
            if not existing_doc:
                return None
            
            # Prepare updated content and metadata
            new_content = update.content if update.content is not None else existing_doc.content
            new_metadata = update.metadata if update.metadata is not None else existing_doc.metadata
            
            # If content changed, regenerate embedding
            if update.content is not None:
                embedding_result = self.embedding_service.generate_embedding(new_content)
                updated_at = datetime.now()
                
                # Try ChromaDB first
                if self._use_chromadb and self._collection:
                    try:
                        # ChromaDB doesn't have direct update, so delete and add
                        self._collection.delete(ids=[document_id])
                        self._collection.add(
                            ids=[document_id],
                            documents=[new_content],
                            embeddings=[embedding_result.embedding],
                            metadatas=[{
                                **new_metadata,
                                "created_at": existing_doc.created_at.isoformat(),
                                "updated_at": updated_at.isoformat(),
                                "token_count": embedding_result.token_count
                            }]
                        )
                        
                        return DocumentResponse(
                            id=document_id,
                            content=new_content,
                            metadata=new_metadata,
                            created_at=existing_doc.created_at,
                            updated_at=updated_at
                        )
                        
                    except Exception as e:
                        logger.warning(f"ChromaDB update failed, trying MySQL: {str(e)}")
                
                # Fallback to MySQL
                db_session = self._get_db_session()
                try:
                    embedding_record = db_session.query(Embedding).filter(Embedding.id == document_id).first()
                    
                    if embedding_record:
                        embedding_record.content = new_content
                        embedding_record.embedding = self._serialize_embedding(embedding_result.embedding)
                        embedding_record.embedding_metadata = {
                            **new_metadata,
                            "created_at": existing_doc.created_at.isoformat(),
                            "updated_at": updated_at.isoformat(),
                            "token_count": embedding_result.token_count,
                            "embedding_dimension": len(embedding_result.embedding)
                        }
                        
                        db_session.commit()
                        
                        return DocumentResponse(
                            id=document_id,
                            content=new_content,
                            metadata=new_metadata,
                            created_at=existing_doc.created_at,
                            updated_at=updated_at
                        )
                    
                    return None
                    
                except Exception as e:
                    db_session.rollback()
                    raise Exception(f"Failed to update document in MySQL: {str(e)}")
                finally:
                    if not self.db_session:
                        db_session.close()
            
            else:
                # Only metadata update, no need to regenerate embedding
                # This is a simplified case - in practice, you might want to update metadata in storage
                return DocumentResponse(
                    id=document_id,
                    content=existing_doc.content,
                    metadata=new_metadata,
                    created_at=existing_doc.created_at,
                    updated_at=datetime.now()
                )
                
        except Exception as e:
            logger.error(f"Failed to update document {document_id}: {str(e)}")
            return None
    
    def delete_document(self, document_id: str) -> bool:
        """
        Delete a document.
        
        Args:
            document_id: Document ID
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            success = False
            
            # Try ChromaDB first
            if self._use_chromadb and self._collection:
                try:
                    self._collection.delete(ids=[document_id])
                    success = True
                    logger.debug(f"Document {document_id} deleted from ChromaDB")
                except Exception as e:
                    logger.warning(f"ChromaDB delete failed, trying MySQL: {str(e)}")
            
            # Also try MySQL (or as fallback)
            db_session = self._get_db_session()
            try:
                embedding_record = db_session.query(Embedding).filter(Embedding.id == document_id).first()
                
                if embedding_record:
                    db_session.delete(embedding_record)
                    db_session.commit()
                    success = True
                    logger.debug(f"Document {document_id} deleted from MySQL")
                
            except Exception as e:
                db_session.rollback()
                logger.error(f"Failed to delete document from MySQL: {str(e)}")
            finally:
                if not self.db_session:
                    db_session.close()
            
            return success
            
        except Exception as e:
            logger.error(f"Failed to delete document {document_id}: {str(e)}")
            return False
    
    def list_documents(self, limit: int = 100, offset: int = 0, metadata_filter: Optional[Dict[str, Any]] = None) -> List[DocumentResponse]:
        """
        List documents with optional filtering and pagination.
        
        Args:
            limit: Maximum number of documents to return
            offset: Number of documents to skip
            metadata_filter: Optional metadata filter criteria
            
        Returns:
            List of DocumentResponse objects
        """
        try:
            documents = []
            
            # Try ChromaDB first
            if self._use_chromadb and self._collection:
                try:
                    # ChromaDB doesn't support offset directly, so we get more and slice
                    get_limit = limit + offset
                    
                    # Prepare where clause for metadata filtering
                    where_clause = metadata_filter if metadata_filter else None
                    
                    results = self._collection.get(
                        limit=get_limit,
                        where=where_clause
                    )
                    
                    if results['ids']:
                        # Apply offset by slicing
                        start_idx = offset
                        end_idx = offset + limit
                        
                        for i in range(start_idx, min(end_idx, len(results['ids']))):
                            if i < len(results['ids']):
                                doc_id = results['ids'][i]
                                content = results['documents'][i]
                                metadata = results['metadatas'][i] if results['metadatas'] else {}
                                
                                # Extract created_at from metadata
                                created_at_str = metadata.get('created_at')
                                created_at = datetime.fromisoformat(created_at_str) if created_at_str else datetime.now()
                                
                                documents.append(DocumentResponse(
                                    id=doc_id,
                                    content=content,
                                    metadata={k: v for k, v in metadata.items() if k not in ['created_at', 'token_count']},
                                    created_at=created_at
                                ))
                    
                    return documents
                    
                except Exception as e:
                    logger.warning(f"ChromaDB list failed, trying MySQL: {str(e)}")
            
            # Fallback to MySQL
            db_session = self._get_db_session()
            try:
                query = db_session.query(Embedding)
                
                # Apply metadata filter if specified
                if metadata_filter:
                    for key, value in metadata_filter.items():
                        # Use JSON operations for metadata filtering
                        query = query.filter(
                            text(f"JSON_EXTRACT(metadata, '$.{key}') = :value")
                        ).params(value=value)
                
                # Apply pagination
                embeddings = query.offset(offset).limit(limit).all()
                
                for embedding_record in embeddings:
                    metadata = embedding_record.embedding_metadata or {}
                    documents.append(DocumentResponse(
                        id=embedding_record.id,
                        content=embedding_record.content,
                        metadata={k: v for k, v in metadata.items() if k not in ['created_at', 'token_count', 'embedding_dimension']},
                        created_at=embedding_record.created_at
                    ))
                
                return documents
                
            finally:
                if not self.db_session:
                    db_session.close()
                    
        except Exception as e:
            logger.error(f"Failed to list documents: {str(e)}")
            return []
    
    def delete_documents_by_metadata(self, metadata_filter: Dict[str, Any]) -> int:
        """
        Delete documents matching metadata criteria.
        
        Args:
            metadata_filter: Metadata filter criteria
            
        Returns:
            Number of documents deleted
        """
        try:
            deleted_count = 0
            
            # Get documents matching filter first
            matching_docs = self.list_documents(limit=10000, metadata_filter=metadata_filter)
            
            # Delete each document
            for doc in matching_docs:
                if self.delete_document(doc.id):
                    deleted_count += 1
            
            logger.info(f"Deleted {deleted_count} documents matching metadata filter: {metadata_filter}")
            return deleted_count
            
        except Exception as e:
            logger.error(f"Failed to delete documents by metadata: {str(e)}")
            return 0
    
    def update_document_metadata(self, document_id: str, metadata_updates: Dict[str, Any]) -> Optional[DocumentResponse]:
        """
        Update only the metadata of a document without changing content.
        
        Args:
            document_id: Document ID
            metadata_updates: Metadata fields to update
            
        Returns:
            Updated DocumentResponse if successful, None otherwise
        """
        try:
            # Get existing document
            existing_doc = self.get_document(document_id)
            if not existing_doc:
                return None
            
            # Merge metadata
            new_metadata = {**existing_doc.metadata, **metadata_updates}
            updated_at = datetime.now()
            
            # Try ChromaDB first (requires delete and re-add)
            if self._use_chromadb and self._collection:
                try:
                    # Get existing embedding from ChromaDB
                    results = self._collection.get(ids=[document_id])
                    if results['ids'] and results['ids'][0]:
                        existing_metadata = results['metadatas'][0] if results['metadatas'] else {}
                        
                        # Update metadata while preserving system fields
                        updated_metadata = {
                            **new_metadata,
                            "created_at": existing_doc.created_at.isoformat(),
                            "updated_at": updated_at.isoformat(),
                            "token_count": existing_metadata.get("token_count", 0)
                        }
                        
                        # Delete and re-add with updated metadata
                        self._collection.delete(ids=[document_id])
                        self._collection.add(
                            ids=[document_id],
                            documents=[existing_doc.content],
                            embeddings=[results['embeddings'][0]] if results.get('embeddings') else None,
                            metadatas=[updated_metadata]
                        )
                        
                        return DocumentResponse(
                            id=document_id,
                            content=existing_doc.content,
                            metadata=new_metadata,
                            created_at=existing_doc.created_at,
                            updated_at=updated_at
                        )
                        
                except Exception as e:
                    logger.warning(f"ChromaDB metadata update failed, trying MySQL: {str(e)}")
            
            # Fallback to MySQL
            db_session = self._get_db_session()
            try:
                embedding_record = db_session.query(Embedding).filter(Embedding.id == document_id).first()
                
                if embedding_record:
                    # Update metadata while preserving system fields
                    existing_metadata = embedding_record.embedding_metadata or {}
                    updated_metadata = {
                        **new_metadata,
                        "created_at": existing_doc.created_at.isoformat(),
                        "updated_at": updated_at.isoformat(),
                        "token_count": existing_metadata.get("token_count", 0),
                        "embedding_dimension": existing_metadata.get("embedding_dimension", self.config.embedding_dimension)
                    }
                    
                    embedding_record.embedding_metadata = updated_metadata
                    db_session.commit()
                    
                    return DocumentResponse(
                        id=document_id,
                        content=existing_doc.content,
                        metadata=new_metadata,
                        created_at=existing_doc.created_at,
                        updated_at=updated_at
                    )
                
                return None
                
            except Exception as e:
                db_session.rollback()
                raise Exception(f"Failed to update document metadata in MySQL: {str(e)}")
            finally:
                if not self.db_session:
                    db_session.close()
                    
        except Exception as e:
            logger.error(f"Failed to update document metadata {document_id}: {str(e)}")
            return None
    
    def get_collection_stats(self) -> CollectionStats:
        """
        Get collection statistics.
        
        Returns:
            CollectionStats with collection information
        """
        try:
            # Try ChromaDB first
            if self._use_chromadb and self._collection:
                try:
                    count = self._collection.count()
                    
                    return CollectionStats(
                        collection_name=self.config.collection_name,
                        document_count=count,
                        embedding_dimension=self.config.embedding_dimension,
                        storage_backend="chromadb",
                        created_at=datetime.now()  # ChromaDB doesn't store creation time
                    )
                    
                except Exception as e:
                    logger.warning(f"ChromaDB stats failed, trying MySQL: {str(e)}")
            
            # Fallback to MySQL
            db_session = self._get_db_session()
            try:
                count = db_session.query(Embedding).count()
                
                # Get earliest created_at as collection creation time
                earliest_record = db_session.query(Embedding).order_by(Embedding.created_at.asc()).first()
                created_at = earliest_record.created_at if earliest_record else None
                
                return CollectionStats(
                    collection_name=self.config.collection_name,
                    document_count=count,
                    embedding_dimension=self.config.embedding_dimension,
                    storage_backend="mysql",
                    created_at=created_at
                )
                
            finally:
                if not self.db_session:
                    db_session.close()
                    
        except Exception as e:
            logger.error(f"Failed to get collection stats: {str(e)}")
            return CollectionStats(
                collection_name=self.config.collection_name,
                document_count=0,
                embedding_dimension=self.config.embedding_dimension,
                storage_backend="unknown"
            )