"""
Conversational RAG Service
Handles embedding creation and retrieval for chat messages to enable conversational RAG.
"""
import logging
import json
from typing import List, Optional, Tuple
from sqlalchemy.orm import Session as DBSession
from sqlalchemy import text

from app.database.models import Message, MessageEmbedding, MessageRole
from app.services.embedding_service import EmbeddingService

logger = logging.getLogger(__name__)


class ConversationalRAGService:
    """Service for conversational RAG functionality."""
    
    def __init__(self, db_session: DBSession, embeddi