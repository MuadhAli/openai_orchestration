"""
Context service for managing conversation context and combining chat history with retrieved documents.
"""
import logging
import time
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass

from app.models.message import Message, ConversationContext
from app.services.rag_service import RetrievedDocument

logger = logging.getLogger(__name__)


@dataclass
class ContextWindow:
    """Represents a context window with token management."""
    messages: List[Message]
    retrieved_docs: List[RetrievedDocument]
    total_tokens: int
    max_tokens: int
    truncated: bool = False


@dataclass
class ContextPriority:
    """Configuration for context prioritization."""
    recent_messages_weight: float = 0.7
    retrieved_content_weight: float = 0.3
    system_message_priority: bool = True
    preserve_last_n_messages: int = 2


class ConversationContextService:
    """Service for combining chat history and retrieved documents into context."""
    
    def __init__(self, 
                 default_max_tokens: int = 4000,
                 tokens_per_word: float = 1.3,
                 context_priority: Optional[ContextPriority] = None):
        """
        Initialize context service.
        
        Args:
            default_max_tokens: Default maximum tokens for context window
            tokens_per_word: Rough estimation of tokens per word
            context_priority: Configuration for context prioritization
        """
        self.default_max_tokens = default_max_tokens
        self.tokens_per_word = tokens_per_word
        self.context_priority = context_priority or ContextPriority()
        
        logger.info(f"ConversationContextService initialized with max_tokens={default_max_tokens}")
    
    def combine_context(self, 
                       chat_history: List[Message],
                       retrieved_documents: List[RetrievedDocument],
                       max_tokens: Optional[int] = None) -> ConversationContext:
        """
        Combine chat history and retrieved documents into a conversation context.
        
        Args:
            chat_history: List of chat messages
            retrieved_documents: List of retrieved documents
            max_tokens: Maximum tokens for context (uses default if None)
            
        Returns:
            ConversationContext with combined information
        """
        try:
            max_tokens = max_tokens or self.default_max_tokens
            
            # Calculate token counts
            message_tokens = self._calculate_message_tokens(chat_history)
            doc_tokens = self._calculate_document_tokens(retrieved_documents)
            total_tokens = message_tokens + doc_tokens
            
            # Create initial context
            context = ConversationContext(
                session_id=chat_history[0].session_id if chat_history else "unknown",
                messages=chat_history.copy(),
                retrieved_context=[self._doc_to_dict(doc) for doc in retrieved_documents],
                total_tokens=total_tokens,
                context_window_limit=max_tokens
            )
            
            # Apply token-aware management if needed
            if total_tokens > max_tokens:
                context = self._apply_token_management(context, retrieved_documents, max_tokens)
            
            logger.info(f"Combined context: {len(context.messages)} messages, "
                       f"{len(context.retrieved_context)} documents, "
                       f"{context.total_tokens} tokens")
            
            return context
            
        except Exception as e:
            logger.error(f"Failed to combine context: {str(e)}")
            # Return minimal context on error
            return ConversationContext(
                session_id=chat_history[0].session_id if chat_history else "unknown",
                messages=[],
                retrieved_context=[],
                total_tokens=0,
                context_window_limit=max_tokens or self.default_max_tokens
            )
    
    def _calculate_message_tokens(self, messages: List[Message]) -> int:
        """Calculate total tokens for messages."""
        total_tokens = 0
        for message in messages:
            if message.token_count:
                total_tokens += message.token_count
            else:
                # Rough estimation based on word count
                word_count = len(message.content.split())
                total_tokens += int(word_count * self.tokens_per_word)
        return total_tokens
    
    def _calculate_document_tokens(self, documents: List[RetrievedDocument]) -> int:
        """Calculate total tokens for retrieved documents."""
        total_tokens = 0
        for doc in documents:
            word_count = len(doc.content.split())
            total_tokens += int(word_count * self.tokens_per_word)
        return total_tokens
    
    def _doc_to_dict(self, doc: RetrievedDocument) -> Dict[str, Any]:
        """Convert RetrievedDocument to dictionary format."""
        return {
            "content": doc.content,
            "similarity_score": doc.similarity_score,
            "metadata": doc.metadata,
            "source": doc.source,
            "document_id": doc.document_id
        }
    
    def _apply_token_management(self, 
                               context: ConversationContext,
                               retrieved_documents: List[RetrievedDocument],
                               max_tokens: int) -> ConversationContext:
        """
        Apply token-aware context window management.
        
        Args:
            context: Original context
            retrieved_documents: Retrieved documents for reference
            max_tokens: Maximum allowed tokens
            
        Returns:
            Context with token management applied
        """
        try:
            # Calculate token allocation based on priority weights
            message_token_budget = int(max_tokens * self.context_priority.recent_messages_weight)
            doc_token_budget = int(max_tokens * self.context_priority.retrieved_content_weight)
            
            # Prioritize and truncate messages
            prioritized_messages = self._prioritize_messages(context.messages, message_token_budget)
            
            # Prioritize and truncate documents
            prioritized_docs = self._prioritize_documents(retrieved_documents, doc_token_budget)
            
            # Recalculate total tokens
            final_message_tokens = self._calculate_message_tokens(prioritized_messages)
            final_doc_tokens = self._calculate_document_tokens(prioritized_docs)
            final_total_tokens = final_message_tokens + final_doc_tokens
            
            # Create updated context
            updated_context = ConversationContext(
                session_id=context.session_id,
                messages=prioritized_messages,
                retrieved_context=[self._doc_to_dict(doc) for doc in prioritized_docs],
                total_tokens=final_total_tokens,
                context_window_limit=max_tokens
            )
            
            logger.info(f"Applied token management: reduced from {context.total_tokens} to {final_total_tokens} tokens")
            
            return updated_context
            
        except Exception as e:
            logger.error(f"Failed to apply token management: {str(e)}")
            return context
    
    def _prioritize_messages(self, messages: List[Message], token_budget: int) -> List[Message]:
        """
        Prioritize and truncate messages based on token budget.
        
        Args:
            messages: List of messages to prioritize
            token_budget: Available token budget for messages
            
        Returns:
            Prioritized and potentially truncated list of messages
        """
        if not messages:
            return []
        
        # Always preserve the last N messages (most recent conversation)
        preserve_count = min(self.context_priority.preserve_last_n_messages, len(messages))
        preserved_messages = messages[-preserve_count:] if preserve_count > 0 else []
        
        # Calculate tokens for preserved messages
        preserved_tokens = self._calculate_message_tokens(preserved_messages)
        
        # If preserved messages exceed budget, truncate them
        if preserved_tokens > token_budget:
            return self._truncate_messages_to_budget(preserved_messages, token_budget)
        
        # Add more messages from history if budget allows
        remaining_budget = token_budget - preserved_tokens
        additional_messages = []
        
        # Work backwards from the messages before preserved ones
        for i in range(len(messages) - preserve_count - 1, -1, -1):
            message = messages[i]
            message_tokens = message.token_count or int(len(message.content.split()) * self.tokens_per_word)
            
            if message_tokens <= remaining_budget:
                additional_messages.insert(0, message)
                remaining_budget -= message_tokens
            else:
                break
        
        return additional_messages + preserved_messages
    
    def _prioritize_documents(self, documents: List[RetrievedDocument], token_budget: int) -> List[RetrievedDocument]:
        """
        Prioritize and truncate documents based on token budget and relevance.
        
        Args:
            documents: List of documents to prioritize
            token_budget: Available token budget for documents
            
        Returns:
            Prioritized and potentially truncated list of documents
        """
        if not documents:
            return []
        
        # Sort documents by similarity score (descending)
        sorted_docs = sorted(documents, key=lambda x: x.similarity_score, reverse=True)
        
        selected_docs = []
        used_tokens = 0
        
        for doc in sorted_docs:
            doc_tokens = int(len(doc.content.split()) * self.tokens_per_word)
            
            if used_tokens + doc_tokens <= token_budget:
                selected_docs.append(doc)
                used_tokens += doc_tokens
            else:
                # Try to fit a truncated version of the document
                remaining_budget = token_budget - used_tokens
                if remaining_budget > 50:  # Only if we have meaningful space left
                    truncated_doc = self._truncate_document(doc, remaining_budget)
                    if truncated_doc:
                        selected_docs.append(truncated_doc)
                break
        
        return selected_docs
    
    def _truncate_messages_to_budget(self, messages: List[Message], token_budget: int) -> List[Message]:
        """
        Truncate messages to fit within token budget, preserving the most recent ones.
        
        Args:
            messages: Messages to truncate
            token_budget: Token budget
            
        Returns:
            Truncated list of messages
        """
        if not messages:
            return []
        
        truncated_messages = []
        used_tokens = 0
        
        # Start from the most recent messages
        for message in reversed(messages):
            message_tokens = message.token_count or int(len(message.content.split()) * self.tokens_per_word)
            
            if used_tokens + message_tokens <= token_budget:
                truncated_messages.insert(0, message)
                used_tokens += message_tokens
            else:
                break
        
        return truncated_messages
    
    def _truncate_document(self, document: RetrievedDocument, token_budget: int) -> Optional[RetrievedDocument]:
        """
        Truncate a document to fit within token budget.
        
        Args:
            document: Document to truncate
            token_budget: Available token budget
            
        Returns:
            Truncated document or None if can't fit meaningfully
        """
        if token_budget < 50:  # Not enough space for meaningful content
            return None
        
        words = document.content.split()
        max_words = int(token_budget / self.tokens_per_word)
        
        if len(words) <= max_words:
            return document
        
        # Truncate and add ellipsis
        truncated_content = " ".join(words[:max_words]) + "..."
        
        return RetrievedDocument(
            content=truncated_content,
            similarity_score=document.similarity_score,
            metadata={**document.metadata, "truncated": True},
            source=document.source,
            document_id=document.document_id
        )
    
    def create_context_window(self, 
                             messages: List[Message],
                             retrieved_docs: List[RetrievedDocument],
                             max_tokens: int) -> ContextWindow:
        """
        Create a context window with the given constraints.
        
        Args:
            messages: Chat messages
            retrieved_docs: Retrieved documents
            max_tokens: Maximum tokens allowed
            
        Returns:
            ContextWindow with managed content
        """
        try:
            # Calculate initial token counts
            message_tokens = self._calculate_message_tokens(messages)
            doc_tokens = self._calculate_document_tokens(retrieved_docs)
            total_tokens = message_tokens + doc_tokens
            
            # Apply management if needed
            if total_tokens > max_tokens:
                # Apply token management
                message_budget = int(max_tokens * self.context_priority.recent_messages_weight)
                doc_budget = int(max_tokens * self.context_priority.retrieved_content_weight)
                
                managed_messages = self._prioritize_messages(messages, message_budget)
                managed_docs = self._prioritize_documents(retrieved_docs, doc_budget)
                
                final_tokens = self._calculate_message_tokens(managed_messages) + self._calculate_document_tokens(managed_docs)
                
                return ContextWindow(
                    messages=managed_messages,
                    retrieved_docs=managed_docs,
                    total_tokens=final_tokens,
                    max_tokens=max_tokens,
                    truncated=True
                )
            else:
                return ContextWindow(
                    messages=messages,
                    retrieved_docs=retrieved_docs,
                    total_tokens=total_tokens,
                    max_tokens=max_tokens,
                    truncated=False
                )
                
        except Exception as e:
            logger.error(f"Failed to create context window: {str(e)}")
            return ContextWindow(
                messages=[],
                retrieved_docs=[],
                total_tokens=0,
                max_tokens=max_tokens,
                truncated=True
            )


# Global context service instance
context_service: Optional[ConversationContextService] = None

def get_context_service() -> ConversationContextService:
    """
    Get the global context service instance.
    
    Returns:
        ConversationContextService instance
        
    Raises:
        RuntimeError: If service is not initialized
    """
    global context_service
    if context_service is None:
        raise RuntimeError("Context service not initialized. Call initialize_context_service() first.")
    return context_service

def initialize_context_service(default_max_tokens: int = 4000,
                              tokens_per_word: float = 1.3,
                              context_priority: Optional[ContextPriority] = None) -> bool:
    """
    Initialize the global context service.
    
    Args:
        default_max_tokens: Default maximum tokens for context window
        tokens_per_word: Rough estimation of tokens per word
        context_priority: Configuration for context prioritization
        
    Returns:
        bool: True if successful, False otherwise
    """
    global context_service
    try:
        context_service = ConversationContextService(
            default_max_tokens=default_max_tokens,
            tokens_per_word=tokens_per_word,
            context_priority=context_priority
        )
        logger.info("Global context service initialized successfully")
        return True
    except Exception as e:
        logger.error(f"Failed to initialize context service: {str(e)}")
        return False

def check_context_service_health() -> bool:
    """
    Check if context service is healthy.
    
    Returns:
        bool: True if healthy, False otherwise
    """
    try:
        service = get_context_service()
        # Try a simple context combination as health check
        test_context = service.combine_context([], [])
        return True
    except Exception as e:
        logger.error(f"Context service health check failed: {str(e)}")
        return False