"""
Pydantic models for vector database operations.
"""
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field, validator
from datetime import datetime


class DocumentCreate(BaseModel):
    """Model for creating a new document."""
    content: str = Field(..., min_length=1, description="Document content")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Document metadata")
    
    @validator('content')
    def validate_content(cls, v):
        if not v or not v.strip():
            raise ValueError("Content cannot be empty")
        return v.strip()


class DocumentUpdate(BaseModel):
    """Model for updating an existing document."""
    content: Optional[str] = Field(None, min_length=1, description="Updated document content")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Updated document metadata")
    
    @validator('content')
    def validate_content(cls, v):
        if v is not None and (not v or not v.strip()):
            raise ValueError("Content cannot be empty")
        return v.strip() if v else v


class DocumentResponse(BaseModel):
    """Model for document response."""
    id: str = Field(..., description="Document ID")
    content: str = Field(..., description="Document content")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Document metadata")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: Optional[datetime] = Field(None, description="Last update timestamp")
    
    class Config:
        from_attributes = True


class SimilarityResult(BaseModel):
    """Model for similarity search result."""
    document_id: str = Field(..., description="Document ID")
    content: str = Field(..., description="Document content")
    similarity_score: float = Field(..., ge=0.0, le=1.0, description="Similarity score (0-1)")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Document metadata")
    distance: Optional[float] = Field(None, description="Distance metric (lower is more similar)")
    
    @validator('similarity_score')
    def validate_similarity_score(cls, v):
        if not 0.0 <= v <= 1.0:
            raise ValueError("Similarity score must be between 0.0 and 1.0")
        return v


class VectorSearchQuery(BaseModel):
    """Model for vector search query."""
    query_text: str = Field(..., min_length=1, description="Query text")
    top_k: int = Field(default=5, ge=1, le=100, description="Number of results to return")
    similarity_threshold: float = Field(default=0.7, ge=0.0, le=1.0, description="Minimum similarity threshold")
    metadata_filter: Optional[Dict[str, Any]] = Field(None, description="Metadata filter criteria")
    
    @validator('query_text')
    def validate_query_text(cls, v):
        if not v or not v.strip():
            raise ValueError("Query text cannot be empty")
        return v.strip()
    
    @validator('top_k')
    def validate_top_k(cls, v):
        if v < 1 or v > 100:
            raise ValueError("top_k must be between 1 and 100")
        return v
    
    @validator('similarity_threshold')
    def validate_similarity_threshold(cls, v):
        if not 0.0 <= v <= 1.0:
            raise ValueError("Similarity threshold must be between 0.0 and 1.0")
        return v


class VectorSearchResponse(BaseModel):
    """Model for vector search response."""
    query: str = Field(..., description="Original query text")
    results: List[SimilarityResult] = Field(default_factory=list, description="Search results")
    total_results: int = Field(..., ge=0, description="Total number of results found")
    search_time_ms: int = Field(..., ge=0, description="Search time in milliseconds")
    used_fallback: bool = Field(default=False, description="Whether fallback storage was used")
    
    @validator('total_results')
    def validate_total_results(cls, v, values):
        if 'results' in values and v != len(values['results']):
            raise ValueError("total_results must match the length of results list")
        return v


class CollectionStats(BaseModel):
    """Model for collection statistics."""
    collection_name: str = Field(..., description="Collection name")
    document_count: int = Field(..., ge=0, description="Number of documents")
    total_size_bytes: Optional[int] = Field(None, ge=0, description="Total size in bytes")
    embedding_dimension: int = Field(..., gt=0, description="Embedding vector dimension")
    storage_backend: str = Field(..., description="Storage backend (chromadb or mysql)")
    created_at: Optional[datetime] = Field(None, description="Collection creation time")
    last_updated: Optional[datetime] = Field(None, description="Last update time")


class BulkDocumentCreate(BaseModel):
    """Model for bulk document creation."""
    documents: List[DocumentCreate] = Field(..., min_items=1, max_items=1000, description="List of documents to create")
    
    @validator('documents')
    def validate_documents(cls, v):
        if not v:
            raise ValueError("At least one document is required")
        if len(v) > 1000:
            raise ValueError("Cannot create more than 1000 documents at once")
        return v


class BulkDocumentResponse(BaseModel):
    """Model for bulk document creation response."""
    created_documents: List[DocumentResponse] = Field(default_factory=list, description="Successfully created documents")
    failed_documents: List[Dict[str, Any]] = Field(default_factory=list, description="Failed document creations with errors")
    total_requested: int = Field(..., ge=0, description="Total number of documents requested")
    total_created: int = Field(..., ge=0, description="Total number of documents created")
    total_failed: int = Field(..., ge=0, description="Total number of failed creations")
    processing_time_ms: int = Field(..., ge=0, description="Total processing time in milliseconds")
    
    @validator('total_created')
    def validate_total_created(cls, v, values):
        if 'created_documents' in values and v != len(values['created_documents']):
            raise ValueError("total_created must match the length of created_documents list")
        return v
    
    @validator('total_failed')
    def validate_total_failed(cls, v, values):
        if 'failed_documents' in values and v != len(values['failed_documents']):
            raise ValueError("total_failed must match the length of failed_documents list")
        return v


class DocumentListRequest(BaseModel):
    """Model for document listing request."""
    limit: int = Field(default=100, ge=1, le=1000, description="Maximum number of documents to return")
    offset: int = Field(default=0, ge=0, description="Number of documents to skip")
    metadata_filter: Optional[Dict[str, Any]] = Field(None, description="Metadata filter criteria")
    
    @validator('limit')
    def validate_limit(cls, v):
        if v < 1 or v > 1000:
            raise ValueError("Limit must be between 1 and 1000")
        return v


class DocumentListResponse(BaseModel):
    """Model for document listing response."""
    documents: List[DocumentResponse] = Field(default_factory=list, description="List of documents")
    total_count: int = Field(..., ge=0, description="Total number of documents matching criteria")
    limit: int = Field(..., ge=1, description="Requested limit")
    offset: int = Field(..., ge=0, description="Requested offset")
    has_more: bool = Field(..., description="Whether there are more documents available")


class DocumentMetadataUpdate(BaseModel):
    """Model for updating document metadata only."""
    metadata_updates: Dict[str, Any] = Field(..., description="Metadata fields to update")
    
    @validator('metadata_updates')
    def validate_metadata_updates(cls, v):
        if not v:
            raise ValueError("At least one metadata field must be provided for update")
        return v


class BulkDeleteRequest(BaseModel):
    """Model for bulk document deletion by metadata."""
    metadata_filter: Dict[str, Any] = Field(..., description="Metadata filter criteria for deletion")
    confirm_deletion: bool = Field(default=False, description="Confirmation flag for deletion")
    
    @validator('metadata_filter')
    def validate_metadata_filter(cls, v):
        if not v:
            raise ValueError("Metadata filter is required for bulk deletion")
        return v
    
    @validator('confirm_deletion')
    def validate_confirmation(cls, v):
        if not v:
            raise ValueError("Deletion must be explicitly confirmed by setting confirm_deletion=True")
        return v


class BulkDeleteResponse(BaseModel):
    """Model for bulk deletion response."""
    deleted_count: int = Field(..., ge=0, description="Number of documents deleted")
    metadata_filter: Dict[str, Any] = Field(..., description="Metadata filter used for deletion")
    processing_time_ms: int = Field(..., ge=0, description="Processing time in milliseconds")


class ProgressCallback(BaseModel):
    """Model for progress tracking callback."""
    current: int = Field(..., ge=0, description="Current progress count")
    total: int = Field(..., gt=0, description="Total items to process")
    percentage: float = Field(..., ge=0.0, le=100.0, description="Progress percentage")
    message: Optional[str] = Field(None, description="Optional progress message")
    
    @validator('percentage')
    def calculate_percentage(cls, v, values):
        if 'current' in values and 'total' in values:
            calculated = (values['current'] / values['total']) * 100
            return round(calculated, 2)
        return v


class VectorRepositoryConfig(BaseModel):
    """Configuration for vector repository."""
    use_chromadb: bool = Field(default=True, description="Whether to use ChromaDB as primary storage")
    chromadb_path: str = Field(default="./data/vector_db", description="Path for ChromaDB storage")
    mysql_fallback: bool = Field(default=True, description="Whether to use MySQL as fallback")
    collection_name: str = Field(default="documents", description="Default collection name")
    embedding_dimension: int = Field(default=1536, gt=0, description="Embedding vector dimension")
    similarity_metric: str = Field(default="cosine", description="Similarity metric to use")
    
    @validator('similarity_metric')
    def validate_similarity_metric(cls, v):
        allowed_metrics = ["cosine", "euclidean", "dot_product"]
        if v not in allowed_metrics:
            raise ValueError(f"Similarity metric must be one of: {allowed_metrics}")
        return v