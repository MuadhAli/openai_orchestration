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
        self.min_context_quality = min_context_quality
        self.similarity_threshold = similarity_threshold
        self.compression_ratio_target = compression_ratio_target
        
        logger.info(f"ContextOptimizationService initialized with min_quality={min_context_quality}, "
                   f"similarity_threshold={similarity_threshold}")
    
    def optimize_context(self, 
                        context: ConversationContext,
                        target_tokens: int,
                        strategies: Optional[List[CompressionStrategy]] = None) -> OptimizationResult:
        """Optimize context to fit within target token limit while maintaining quality."""
        try:
            original_tokens = context.total_tokens
            
            if original_tokens <= target_tokens:
                # No optimization needed
                quality_metrics = self._calculate_quality_metrics(context, context.retrieved_context)
                return OptimizationResult(
                    optimized_context=context,
                    original_tokens=original_tokens,
                    optimized_tokens=original_tokens,
                    compression_ratio=1.0,
                    quality_metrics=quality_metrics,
                    strategies_applied=[]
                )
            
            # Use default strategies if none provided
            if strategies is None:
                strategies = [
                    CompressionStrategy.REMOVE_REDUNDANT,
                    CompressionStrategy.COMPRESS_REPETITIVE,
                    CompressionStrategy.PRIORITIZE_QUALITY,
                    CompressionStrategy.TRUNCATE_OLDEST
                ]
            
            # Apply optimization strategies in order
            optimized_context = context
            applied_strategies = []
            
            for strategy in strategies:
                if optimized_context.total_tokens <= target_tokens:
                    break
                    
                if strategy == CompressionStrategy.REMOVE_REDUNDANT:
                    optimized_context = self._remove_redundant_content(optimized_context)
                    applied_strategies.append(strategy)
                elif strategy == CompressionStrategy.COMPRESS_REPETITIVE:
                    optimized_context = self._compress_repetitive_content(optimized_context)
                    applied_strategies.append(strategy)
                elif strategy == CompressionStrategy.PRIORITIZE_QUALITY:
                    optimized_context = self._prioritize_by_quality(optimized_context, target_tokens)
                    applied_strategies.append(strategy)
                elif strategy == CompressionStrategy.TRUNCATE_OLDEST:
                    optimized_context = self._truncate_to_limit(optimized_context, target_tokens)
                    applied_strategies.append(strategy)
            
            # Calculate final metrics
            quality_metrics = self._calculate_quality_metrics(optimized_context, context.retrieved_context)
            compression_ratio = optimized_context.total_tokens / original_tokens if original_tokens > 0 else 1.0
            
            logger.info(f"Context optimized: {original_tokens} -> {optimized_context.total_tokens} tokens")
            
            return OptimizationResult(
                optimized_context=optimized_context,
                original_tokens=original_tokens,
                optimized_tokens=optimized_context.total_tokens,
                compression_ratio=compression_ratio,
                quality_metrics=quality_metrics,
                strategies_applied=applied_strategies
            )
            
        except Exception as e:
            logger.error(f"Failed to optimize context: {str(e)}")
            # Return original context on error
            quality_metrics = ContextQualityMetrics(0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0)
            return OptimizationResult(
                optimized_context=context,
                original_tokens=original_tokens,
                optimized_tokens=original_tokens,
                compression_ratio=1.0,
                quality_metrics=quality_metrics,
                strategies_applied=[]
            )
    
    def _truncate_to_limit(self, context: ConversationContext, target_tokens: int) -> ConversationContext:
        """Truncate context to fit within token limit."""
        try:
            # Reserve 30% for documents, 70% for messages
            doc_budget = int(target_tokens * 0.3)
            message_budget = target_tokens - doc_budget
            
            # Select documents within budget
            selected_docs = []
            used_doc_tokens = 0
            for doc in context.retrieved_context:
                doc_tokens = self._estimate_document_tokens(doc)
                if used_doc_tokens + doc_tokens <= doc_budget:
                    selected_docs.append(doc)
                    used_doc_tokens += doc_tokens
            
            # Select messages from most recent backwards
            selected_messages = []
            used_msg_tokens = 0
            
            for message in reversed(context.messages):
                message_tokens = self._estimate_message_tokens(message)
                if used_msg_tokens + message_tokens <= message_budget:
                    selected_messages.insert(0, message)
                    used_msg_tokens += message_tokens
                else:
                    break
            
            total_tokens = used_msg_tokens + used_doc_tokens
            
            return ConversationContext(
                session_id=context.session_id,
                messages=selected_messages,
                retrieved_context=selected_docs,
                total_tokens=total_tokens,
                context_window_limit=context.context_window_limit
            )
            
        except Exception as e:
            logger.error(f"Failed to truncate context: {str(e)}")
            return context
    
    def _calculate_quality_metrics(self, context: ConversationContext, original_docs: List[Dict[str, Any]]) -> ContextQualityMetrics:
        """Calculate comprehensive quality metrics for the context."""
        try:
            relevance_score = self._calculate_relevance_score(context.retrieved_context)
            recency_score = self._calculate_recency_score(context.messages)
            completeness_score = len(context.retrieved_context) / max(1, len(original_docs)) if original_docs else 1.0
            diversity_score = self._calculate_diversity_score(context)
            coherence_score = self._calculate_coherence_score(context)
            information_density = self._calculate_information_density(context)
            
            # Overall score (weighted combination)
            overall_score = (
                self.quality_weights["relevance"] * relevance_score +
                self.quality_weights["recency"] * recency_score +
                self.quality_weights["completeness"] * completeness_score +
                self.quality_weights["diversity"] * diversity_score +
                self.quality_weights["coherence"] * coherence_score +
                self.quality_weights["information_density"] * information_density
            )
            
            return ContextQualityMetrics(
                relevance_score=relevance_score,
                recency_score=recency_score,
                completeness_score=completeness_score,
                diversity_score=diversity_score,
                coherence_score=coherence_score,
                information_density=information_density,
                overall_score=overall_score
            )
            
        except Exception as e:
            logger.error(f"Failed to calculate quality metrics: {str(e)}")
            return ContextQualityMetrics(0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0)
    
    def _calculate_relevance_score(self, retrieved_docs: List[Dict[str, Any]]) -> float:
        """Calculate relevance score based on retrieved documents."""
        if not retrieved_docs:
            return 0.0
        
        total_score = sum(doc.get("similarity_score", 0.0) for doc in retrieved_docs)
        return total_score / len(retrieved_docs)
    
    def _estimate_message_tokens(self, message: Message) -> int:
        """Estimate tokens for a message."""
        if message.token_count:
            return message.token_count
        return int(len(message.content.split()) * self.tokens_per_word)
    
    def _estimate_document_tokens(self, doc_dict: Dict[str, Any]) -> int:
        """Estimate tokens for a document."""
        content = doc_dict.get("content", "")
        return int(len(content.split()) * self.tokens_per_word)
    
    def _remove_redundant_content(self, context: ConversationContext) -> ConversationContext:
        """Remove redundant messages and documents from context."""
        try:
            # Remove duplicate documents
            unique_docs = []
            seen_content = set()
            
            for doc in context.retrieved_context:
                content_hash = hash(doc.get("content", ""))
                if content_hash not in seen_content:
                    unique_docs.append(doc)
                    seen_content.add(content_hash)
            
            # Remove similar messages
            unique_messages = []
            for message in context.messages:
                is_duplicate = False
                for existing_msg in unique_messages:
                    if self._are_messages_similar(message, existing_msg):
                        is_duplicate = True
                        break
                
                if not is_duplicate:
                    unique_messages.append(message)
            
            # Recalculate tokens
            new_tokens = (
                sum(self._estimate_message_tokens(msg) for msg in unique_messages) +
                sum(self._estimate_document_tokens(doc) for doc in unique_docs)
            )
            
            return ConversationContext(
                session_id=context.session_id,
                messages=unique_messages,
                retrieved_context=unique_docs,
                total_tokens=new_tokens,
                context_window_limit=context.context_window_limit
            )
            
        except Exception as e:
            logger.error(f"Failed to remove redundant content: {str(e)}")
            return context
    
    def _compress_repetitive_content(self, context: ConversationContext) -> ConversationContext:
        """Compress repetitive patterns in messages."""
        try:
            compressed_messages = []
            
            for message in context.messages:
                compressed_content = self._compress_message_content(message.content)
                
                # Create new message with compressed content
                compressed_message = Message(
                    id=message.id,
                    session_id=message.session_id,
                    content=compressed_content,
                    role=message.role,
                    timestamp=message.timestamp,
                    token_count=int(len(compressed_content.split()) * self.tokens_per_word),
                    processing_time_ms=message.processing_time_ms,
                    message_metadata=message.message_metadata
                )
                compressed_messages.append(compressed_message)
            
            # Recalculate total tokens
            new_tokens = (
                sum(self._estimate_message_tokens(msg) for msg in compressed_messages) +
                sum(self._estimate_document_tokens(doc) for doc in context.retrieved_context)
            )
            
            return ConversationContext(
                session_id=context.session_id,
                messages=compressed_messages,
                retrieved_context=context.retrieved_context,
                total_tokens=new_tokens,
                context_window_limit=context.context_window_limit
            )
            
        except Exception as e:
            logger.error(f"Failed to compress repetitive content: {str(e)}")
            return context
    
    def _prioritize_by_quality(self, context: ConversationContext, target_tokens: int) -> ConversationContext:
        """Prioritize content by quality scores."""
        try:
            # Score messages and documents
            message_scores = [(msg, self._score_message_quality(msg, context.messages)) 
                            for msg in context.messages]
            doc_scores = [(doc, self._score_document_quality(doc)) 
                         for doc in context.retrieved_context]
            
            # Sort by quality (descending)
            message_scores.sort(key=lambda x: x[1], reverse=True)
            doc_scores.sort(key=lambda x: x[1], reverse=True)
            
            # Select highest quality content within budget
            selected_messages = []
            selected_docs = []
            
            # Allocate 70% to messages, 30% to documents
            message_budget = int(target_tokens * 0.7)
            doc_budget = target_tokens - message_budget
            
            # Select messages
            used_msg_tokens = 0
            for message, score in message_scores:
                msg_tokens = self._estimate_message_tokens(message)
                if used_msg_tokens + msg_tokens <= message_budget:
                    selected_messages.append(message)
                    used_msg_tokens += msg_tokens
            
            # Select documents
            used_doc_tokens = 0
            for doc, score in doc_scores:
                doc_tokens = self._estimate_document_tokens(doc)
                if used_doc_tokens + doc_tokens <= doc_budget:
                    selected_docs.append(doc)
                    used_doc_tokens += doc_tokens
            
            total_tokens = used_msg_tokens + used_doc_tokens
            
            return ConversationContext(
                session_id=context.session_id,
                messages=selected_messages,
                retrieved_context=selected_docs,
                total_tokens=total_tokens,
                context_window_limit=context.context_window_limit
            )
            
        except Exception as e:
            logger.error(f"Failed to prioritize by quality: {str(e)}")
            return context
    
    def _remove_redundant_content(self, context: ConversationContext) -> ConversationContext:
        """Remove redundant messages and documents from context."""
        try:
            # Remove duplicate documents
            unique_docs = []
            seen_content = set()
            
            for doc in context.retrieved_context:
                content_hash = hash(doc.get("content", ""))
                if content_hash not in seen_content:
                    unique_docs.append(doc)
                    seen_content.add(content_hash)
            
            # Remove similar messages
            unique_messages = []
            for i, message in enumerate(context.messages):
                is_duplicate = False
                for existing_msg in unique_messages:
                    if self._are_messages_similar(message, existing_msg):
                        is_duplicate = True
                        break
                
                if not is_duplicate:
                    unique_messages.append(message)
            
            # Recalculate tokens
            new_tokens = (
                sum(self._estimate_message_tokens(msg) for msg in unique_messages) +
                sum(self._estimate_document_tokens(doc) for doc in unique_docs)
            )
            
            return ConversationContext(
                session_id=context.session_id,
                messages=unique_messages,
                retrieved_context=unique_docs,
                total_tokens=new_tokens,
                context_window_limit=context.context_window_limit
            )
            
        except Exception as e:
            logger.error(f"Failed to remove redundant content: {str(e)}")
            return context
    
    def _compress_repetitive_content(self, context: ConversationContext) -> ConversationContext:
        """Compress repetitive patterns in messages."""
        try:
            compressed_messages = []
            
            for message in context.messages:
                compressed_content = self._compress_message_content(message.content)
                
                # Create new message with compressed content
                compressed_message = Message(
                    id=message.id,
                    session_id=message.session_id,
                    content=compressed_content,
                    role=message.role,
                    timestamp=message.timestamp,
                    token_count=int(len(compressed_content.split()) * self.tokens_per_word),
                    processing_time_ms=message.processing_time_ms,
                    message_metadata=message.message_metadata
                )
                compressed_messages.append(compressed_message)
            
            # Recalculate total tokens
            new_tokens = (
                sum(self._estimate_message_tokens(msg) for msg in compressed_messages) +
                sum(self._estimate_document_tokens(doc) for doc in context.retrieved_context)
            )
            
            return ConversationContext(
                session_id=context.session_id,
                messages=compressed_messages,
                retrieved_context=context.retrieved_context,
                total_tokens=new_tokens,
                context_window_limit=context.context_window_limit
            )
            
        except Exception as e:
            logger.error(f"Failed to compress repetitive content: {str(e)}")
            return context
    
    def _prioritize_by_quality(self, context: ConversationContext, target_tokens: int) -> ConversationContext:
        """Prioritize content by quality scores."""
        try:
            # Score messages and documents
            message_scores = [(msg, self._score_message_quality(msg, context.messages)) 
                            for msg in context.messages]
            doc_scores = [(doc, self._score_document_quality(doc)) 
                         for doc in context.retrieved_context]
            
            # Sort by quality (descending)
            message_scores.sort(key=lambda x: x[1], reverse=True)
            doc_scores.sort(key=lambda x: x[1], reverse=True)
            
            # Select highest quality content within budget
            selected_messages = []
            selected_docs = []
            used_tokens = 0
            
            # Allocate 70% to messages, 30% to documents
            message_budget = int(target_tokens * 0.7)
            doc_budget = target_tokens - message_budget
            
            # Select messages
            for message, score in message_scores:
                msg_tokens = self._estimate_message_tokens(message)
                if used_tokens + msg_tokens <= message_budget:
                    selected_messages.append(message)
                    used_tokens += msg_tokens
            
            # Select documents
            doc_tokens_used = 0
            for doc, score in doc_scores:
                doc_tokens = self._estimate_document_tokens(doc)
                if doc_tokens_used + doc_tokens <= doc_budget:
                    selected_docs.append(doc)
                    doc_tokens_used += doc_tokens
            
            total_tokens = used_tokens + doc_tokens_used
            
            return ConversationContext(
                session_id=context.session_id,
                messages=selected_messages,
                retrieved_context=selected_docs,
                total_tokens=total_tokens,
                context_window_limit=context.context_window_limit
            )
            
        except Exception as e:
            logger.error(f"Failed to prioritize by quality: {str(e)}")
            return context
    
    def _calculate_recency_score(self, messages: List[Message]) -> float:
        """Calculate recency score based on message timestamps."""
        if not messages:
            return 0.0
        
        try:
            now = datetime.now()
            total_score = 0.0
            
            for message in messages:
                # Calculate time difference in hours
                time_diff = (now - message.timestamp).total_seconds() / 3600
                
                # Exponential decay: more recent = higher score
                recency_score = max(0.0, 1.0 - (time_diff / 24.0))  # Decay over 24 hours
                total_score += recency_score
            
            return total_score / len(messages)
            
        except Exception as e:
            logger.error(f"Failed to calculate recency score: {str(e)}")
            return 0.5
    
    def _calculate_diversity_score(self, context: ConversationContext) -> float:
        """Calculate diversity score based on content variety."""
        try:
            all_content = []
            
            # Collect all content
            for message in context.messages:
                all_content.append(message.content.lower())
            
            for doc in context.retrieved_context:
                all_content.append(doc.get("content", "").lower())
            
            if not all_content:
                return 0.0
            
            # Calculate vocabulary diversity
            all_words = []
            for content in all_content:
                words = re.findall(r'\b\w+\b', content)
                all_words.extend(words)
            
            if not all_words:
                return 0.0
            
            # Unique words / total words
            unique_words = len(set(all_words))
            total_words = len(all_words)
            
            return unique_words / total_words
            
        except Exception as e:
            logger.error(f"Failed to calculate diversity score: {str(e)}")
            return 0.5


# Global optimization service instance
optimization_service: Optional[ContextOptimizationService] = None

def get_optimization_service() -> ContextOptimizationService:
    """Get the global optimization service instance."""
    global optimization_service
    if optimization_service is None:
        raise RuntimeError("Optimization service not initialized. Call initialize_optimization_service() first.")
    return optimization_service

def initialize_optimization_service(tokens_per_word: float = 1.3,
                                   quality_weights: Optional[Dict[str, float]] = None,
                                   min_context_quality: float = 0.6) -> bool:
    """Initialize the global optimization service."""
    global optimization_service
    try:
        optimization_service = ContextOptimizationService(
            tokens_per_word=tokens_per_word,
            quality_weights=quality_weights,
            min_context_quality=min_context_quality
        )
        logger.info("Global optimization service initialized successfully")
        return True
    except Exception as e:
        logger.error(f"Failed to initialize optimization service: {str(e)}")
        return False

def check_optimization_service_health() -> bool:
    """Check if optimization service is healthy."""
    try:
        service = get_optimization_service()
        # Try a simple optimization as health check
        test_context = ConversationContext(
            session_id="test",
            messages=[],
            retrieved_context=[],
            total_tokens=0,
            context_window_limit=1000
        )
        result = service.optimize_context(test_context, 500)
        return True
    except Exception as e:
        logger.error(f"Optimization service health check failed: {str(e)}")
        return False
        """Calculate recency score based on message timestamps."""
        if not messages:
            return 0.0
        
        try:
            now = datetime.now()
            total_score = 0.0
            
            for message in messages:
                # Calculate time difference in hours
                time_diff = (now - message.timestamp).total_seconds() / 3600
                
                # Exponential decay: more recent = higher score
                recency_score = max(0.0, 1.0 - (time_diff / 24.0))  # Decay over 24 hours
                total_score += recency_score
            
            return total_score / len(messages)
            
        except Exception as e:
            logger.error(f"Failed to calculate recency score: {str(e)}")
            return 0.5
    
    def _calculate_diversity_score(self, context: ConversationContext) -> float:
        """Calculate diversity score based on content variety."""
        try:
            all_content = []
            
            # Collect all content
            for message in context.messages:
                all_content.append(message.content.lower())
            
            for doc in context.retrieved_context:
                all_content.append(doc.get("content", "").lower())
            
            if not all_content:
                return 0.0
            
            # Calculate vocabulary diversity
            all_words = []
            for content in all_content:
                words = re.findall(r'\b\w+\b', content)
                all_words.extend(words)
            
            if not all_words:
                return 0.0
            
            # Unique words / total words
            unique_words = len(set(all_words))
            total_words = len(all_words)
            
            return unique_words / total_words
            
        except Exception as e:
            logger.error(f"Failed to calculate diversity score: {str(e)}")
            return 0.5
    
    def _calculate_coherence_score(self, context: ConversationContext) -> float:
        """Calculate coherence score based on conversation flow."""
        try:
            if len(context.messages) < 2:
                return 1.0  # Single message is perfectly coherent
            
            coherence_sum = 0.0
            comparisons = 0
            
            # Check coherence between adjacent messages
            for i in range(len(context.messages) - 1):
                current_msg = context.messages[i]
                next_msg = context.messages[i + 1]
                
                # Simple coherence check based on role alternation
                if current_msg.role != next_msg.role:
                    coherence_sum += 1.0  # Good alternation
                else:
                    coherence_sum += 0.5  # Same role, less coherent
                
                comparisons += 1
            
            return coherence_sum / comparisons if comparisons > 0 else 1.0
            
        except Exception as e:
            logger.error(f"Failed to calculate coherence score: {str(e)}")
            return 0.5
    
    def _calculate_information_density(self, context: ConversationContext) -> float:
        """Calculate information density (meaningful content per token)."""
        try:
            if context.total_tokens == 0:
                return 0.0
            
            # Count meaningful words (excluding common stop words)
            stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'being', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should'}
            
            meaningful_words = 0
            total_words = 0
            
            # Count in messages
            for message in context.messages:
                words = re.findall(r'\b\w+\b', message.content.lower())
                total_words += len(words)
                meaningful_words += sum(1 for word in words if word not in stop_words)
            
            # Count in documents
            for doc in context.retrieved_context:
                words = re.findall(r'\b\w+\b', doc.get("content", "").lower())
                total_words += len(words)
                meaningful_words += sum(1 for word in words if word not in stop_words)
            
            return meaningful_words / total_words if total_words > 0 else 0.0
            
        except Exception as e:
            logger.error(f"Failed to calculate information density: {str(e)}")
            return 0.5
    
    def _are_messages_similar(self, msg1: Message, msg2: Message, threshold: float = None) -> bool:
        """Check if two messages are similar based on content."""
        if threshold is None:
            threshold = self.similarity_threshold
        
        try:
            # Simple similarity based on word overlap
            words1 = set(re.findall(r'\b\w+\b', msg1.content.lower()))
            words2 = set(re.findall(r'\b\w+\b', msg2.content.lower()))
            
            if not words1 or not words2:
                return False
            
            # Jaccard similarity
            intersection = len(words1.intersection(words2))
            union = len(words1.union(words2))
            
            similarity = intersection / union if union > 0 else 0.0
            return similarity >= threshold
            
        except Exception as e:
            logger.error(f"Failed to check message similarity: {str(e)}")
            return False
    
    def _score_message_quality(self, message: Message, all_messages: List[Message]) -> float:
        """Score the quality of a message."""
        try:
            score = 0.0
            
            # Length score (moderate length is better)
            word_count = len(message.content.split())
            if 5 <= word_count <= 50:
                score += 0.3
            elif word_count > 50:
                score += 0.2
            else:
                score += 0.1
            
            # Role diversity score
            if message.role == "user":
                score += 0.2  # User messages are important for context
            else:
                score += 0.3  # Assistant messages contain answers
            
            # Recency score
            if all_messages and message == all_messages[-1]:
                score += 0.3  # Most recent message is important
            elif all_messages and message in all_messages[-3:]:
                score += 0.2  # Recent messages are important
            
            # Content quality (simple heuristic)
            if '?' in message.content:
                score += 0.1  # Questions are valuable
            if any(word in message.content.lower() for word in ['explain', 'how', 'what', 'why', 'when', 'where']):
                score += 0.1  # Informational content
            
            return min(1.0, score)
            
        except Exception as e:
            logger.error(f"Failed to score message quality: {str(e)}")
            return 0.5
    
    def _score_document_quality(self, doc: Dict[str, Any]) -> float:
        """Score the quality of a retrieved document."""
        try:
            score = 0.0
            
            # Similarity score (most important)
            similarity = doc.get("similarity_score", 0.0)
            score += similarity * 0.6
            
            # Content length score
            content = doc.get("content", "")
            word_count = len(content.split())
            if 10 <= word_count <= 200:
                score += 0.3
            elif word_count > 200:
                score += 0.2
            else:
                score += 0.1
            
            # Metadata quality
            metadata = doc.get("metadata", {})
            if metadata and len(metadata) > 0:
                score += 0.1
            
            return min(1.0, score)
            
        except Exception as e:
            logger.error(f"Failed to score document quality: {str(e)}")
            return 0.5
    
    def _compress_message_content(self, content: str) -> str:
        """Compress repetitive patterns in message content."""
        try:
            # Remove excessive whitespace
            compressed = re.sub(r'\s+', ' ', content.strip())
            
            # Remove repeated phrases (simple approach)
            words = compressed.split()
            if len(words) > 10:
                # Look for repeated sequences
                for seq_len in range(3, min(6, len(words) // 2)):
                    i = 0
                    while i <= len(words) - seq_len * 2:
                        sequence = words[i:i + seq_len]
                        next_sequence = words[i + seq_len:i + seq_len * 2]
                        
                        if sequence == next_sequence:
                            # Remove the duplicate sequence
                            words = words[:i + seq_len] + words[i + seq_len * 2:]
                        else:
                            i += 1
                
                compressed = ' '.join(words)
            
            return compressed
            
        except Exception as e:
            logger.error(f"Failed to compress message content: {str(e)}")
            return content
    
    def _create_message_summary(self, messages: List[Message]) -> str:
        """Create a summary of messages for compression."""
        if not messages:
            return "No messages"
        
        try:
            # Simple summary: first and last message with count
            if len(messages) == 1:
                return f"Message: {messages[0].content[:50]}..."
            elif len(messages) == 2:
                return f"Messages: '{messages[0].content[:30]}...' and '{messages[1].content[:30]}...'"
            else:
                return f"Conversation ({len(messages)} messages): '{messages[0].content[:30]}...' ... '{messages[-1].content[:30]}...'"
                
        except Exception as e:
            logger.error(f"Failed to create message summary: {str(e)}")
            return f"Conversation with {len(messages)} messages"

    def _are_messages_similar(self, msg1: Message, msg2: Message, threshold: float = None) -> bool:
        """Check if two messages are similar based on content."""
        if threshold is None:
            threshold = self.similarity_threshold
        
        try:
            # Simple similarity based on word overlap
            words1 = set(re.findall(r'\b\w+\b', msg1.content.lower()))
            words2 = set(re.findall(r'\b\w+\b', msg2.content.lower()))
            
            if not words1 or not words2:
                return False
            
            # Jaccard similarity
            intersection = len(words1.intersection(words2))
            union = len(words1.union(words2))
            
            similarity = intersection / union if union > 0 else 0.0
            return similarity >= threshold
            
        except Exception as e:
            logger.error(f"Failed to check message similarity: {str(e)}")
            return False
    
    def _score_message_quality(self, message: Message, all_messages: List[Message]) -> float:
        """Score the quality of a message."""
        try:
            score = 0.0
            
            # Length score (moderate length is better)
            word_count = len(message.content.split())
            if 5 <= word_count <= 50:
                score += 0.3
            elif word_count > 50:
                score += 0.2
            else:
                score += 0.1
            
            # Role diversity score
            if message.role == "user":
                score += 0.2  # User messages are important for context
            else:
                score += 0.3  # Assistant messages contain answers
            
            # Recency score
            if all_messages and message == all_messages[-1]:
                score += 0.3  # Most recent message is important
            elif all_messages and message in all_messages[-3:]:
                score += 0.2  # Recent messages are important
            
            # Content quality (simple heuristic)
            if '?' in message.content:
                score += 0.1  # Questions are valuable
            if any(word in message.content.lower() for word in ['explain', 'how', 'what', 'why', 'when', 'where']):
                score += 0.1  # Informational content
            
            return min(1.0, score)
            
        except Exception as e:
            logger.error(f"Failed to score message quality: {str(e)}")
            return 0.5
    
    def _score_document_quality(self, doc: Dict[str, Any]) -> float:
        """Score the quality of a retrieved document."""
        try:
            score = 0.0
            
            # Similarity score (most important)
            similarity = doc.get("similarity_score", 0.0)
            score += similarity * 0.6
            
            # Content length score
            content = doc.get("content", "")
            word_count = len(content.split())
            if 10 <= word_count <= 200:
                score += 0.3
            elif word_count > 200:
                score += 0.2
            else:
                score += 0.1
            
            # Metadata quality
            metadata = doc.get("metadata", {})
            if metadata and len(metadata) > 0:
                score += 0.1
            
            return min(1.0, score)
            
        except Exception as e:
            logger.error(f"Failed to score document quality: {str(e)}")
            return 0.5
    
    def _compress_message_content(self, content: str) -> str:
        """Compress repetitive patterns in message content."""
        try:
            # Remove excessive whitespace
            compressed = re.sub(r'\s+', ' ', content.strip())
            
            # Remove repeated phrases (simple approach)
            words = compressed.split()
            if len(words) > 10:
                # Look for repeated sequences
                for seq_len in range(3, min(6, len(words) // 2)):
                    i = 0
                    while i <= len(words) - seq_len * 2:
                        sequence = words[i:i + seq_len]
                        next_sequence = words[i + seq_len:i + seq_len * 2]
                        
                        if sequence == next_sequence:
                            # Remove the duplicate sequence
                            words = words[:i + seq_len] + words[i + seq_len * 2:]
                        else:
                            i += 1
                
                compressed = ' '.join(words)
            
            return compressed
            
        except Exception as e:
            logger.error(f"Failed to compress message content: {str(e)}")
            return content
    
    def _estimate_message_tokens(self, message: Message) -> int:
        """Estimate tokens for a message."""
        if message.token_count:
            return message.token_count
        return int(len(message.content.split()) * self.tokens_per_word)
    
    def _estimate_document_tokens(self, doc_dict: Dict[str, Any]) -> int:
        """Estimate tokens for a document."""
        content = doc_dict.get("content", "")
        return int(len(content.split()) * self.tokens_per_word)


# Global optimization service instance
optimization_service: Optional[ContextOptimizationService] = None

def get_optimization_service() -> ContextOptimizationService:
    """Get the global optimization service instance."""
    global optimization_service
    if optimization_service is None:
        raise RuntimeError("Optimization service not initialized. Call initialize_optimization_service() first.")
    return optimization_service

def initialize_optimization_service(tokens_per_word: float = 1.3,
                                   quality_weights: Optional[Dict[str, float]] = None,
                                   min_context_quality: float = 0.6) -> bool:
    """Initialize the global optimization service."""
    global optimization_service
    try:
        optimization_service = ContextOptimizationService(
            tokens_per_word=tokens_per_word,
            quality_weights=quality_weights,
            min_context_quality=min_context_quality
        )
        logger.info("Global optimization service initialized successfully")
        return True
    except Exception as e:
        logger.error(f"Failed to initialize optimization service: {str(e)}")
        return False

def check_optimization_service_health() -> bool:
    """Check if optimization service is healthy."""
    try:
        service = get_optimization_service()
        # Try a simple optimization as health check
        test_context = ConversationContext(
            session_id="test",
            messages=[],
            retrieved_context=[],
            total_tokens=0,
            context_window_limit=1000
        )
        result = service.optimize_context(test_context, 500)
        return True
    except Exception as e:
        logger.error(f"Optimization service health check failed: {str(e)}")
        return False