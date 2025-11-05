"""
Context optimization service for intelligent truncation and quality scoring.
"""
import logging
import re
from typing import List, Dict, Any, Optional, Set, Tuple
from dataclasses import dataclass
from enum import Enum
from datetime import datetime, timedelta
from collections import Counter

from app.models.message import Message, ConversationContext

logger = logging.getLogger(__name__)


class CompressionStrategy(Enum):
    """Strategies for context compression."""
    TRUNCATE_OLDEST = "truncate_oldest"
    PRIORITIZE_QUALITY = "prioritize_quality"
    REMOVE_REDUNDANT = "remove_redundant"
    COMPRESS_REPETITIVE = "compress_repetitive"
    SEMANTIC_SUMMARIZATION = "semantic_summarization"


@dataclass
class ContextQualityMetrics:
    """Metrics for evaluating context quality."""
    relevance_score: float
    recency_score: float
    completeness_score: float
    diversity_score: float
    coherence_score: float
    information_density: float
    overall_score: float


@dataclass
class OptimizationResult:
    """Result of context optimization."""
    optimized_context: ConversationContext
    original_tokens: int
    optimized_tokens: int
    compression_ratio: float
    quality_metrics: ContextQualityMetrics
    strategies_applied: List[CompressionStrategy]


class ContextOptimizationService:
    """Service for intelligent context truncation and optimization."""
    
    def __init__(self, 
                 tokens_per_word: float = 1.3,
                 quality_weights: Optional[Dict[str, float]] = None,
                 min_context_quality: float = 0.6,
                 similarity_threshold: float = 0.8,
                 compression_ratio_target: float = 0.7):
        """Initialize context optimization service."""
        self.tokens_per_word = tokens_per_word
        self.quality_weights = quality_weights or {
            "relevance": 0.25,
            "recency": 0.25,
            "completeness": 0.2,
            "diversity": 0.15,
            "coherence": 0.1,
            "information_density": 0.05
        }
        self.min_context_quality = min_context_qual