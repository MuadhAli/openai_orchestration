"""
Chat service for handling OpenAI API integration and conversation management.
Enhanced with RAG integration and multi-session support.
"""
import os
import uuid
import logging
import asyncio
import time
from typing import Dict, Optional, List, AsyncIterator
from openai import OpenAI, APIError, RateLimitError, APIConnectionError, AuthenticationError
from openai.types.chat import ChatCompletion
from dotenv import load_dotenv

from app.models.chat import ChatRequest, ChatResponse, ConversationHistory, ErrorResponse
from app.models.message import Message, ConversationContext
from app.services.rag_service import RAGService, RAGContext, RAGServiceError
from app.services.session_service import SessionService, SessionServiceError
from app.services.message_service import MessageService, MessageServiceError

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()


class ChatServiceError(Exception):
    """Base exception for ChatService errors."""
    pass


class APIKeyError(ChatServiceError):
    """Raised when API key is invalid or missing."""
    pass


class ConversationError(ChatServiceError):
    """Raised when conversation operations fail."""
    pass


class OpenAIAPIError(ChatServiceError):
    """Raised when OpenAI API calls fail."""
    pass


class ChatService:
    """Service class for managing chat conversations and OpenAI API integration with RAG support."""
    
    def __init__(self, 
                 rag_service: Optional[RAGService] = None,
                 session_service: Optional[SessionService] = None,
                 message_service: Optional[MessageService] = None):
        """Initialize the chat service with OpenAI client and RAG integration."""
        try:
            self.api_key = os.getenv("OPENAI_API_KEY")
            if not self.api_key:
                raise APIKeyError("OPENAI_API_KEY environment variable is required")
            
            if not self.api_key.startswith('sk-'):
                raise APIKeyError("Invalid OpenAI API key format")
            
            self.client = OpenAI(api_key=self.api_key)
            self.conversations: Dict[str, ConversationHistory] = {}  # Legacy support
            self.default_model = "gpt-4o-mini"
            self.max_retries = 3
            self.retry_delay = 1.0
            
            # RAG and session integration
            self.rag_service = rag_service
            self.session_service = session_service
            self.message_service = message_service
            
            # Context management settings
            self.max_context_tokens = 8000  # Conservative limit for context window
            self.max_history_messages = 20  # Maximum chat history messages to include
            self.rag_enabled = rag_service is not None
            
            logger.info(f"ChatService initialized successfully (RAG enabled: {self.rag_enabled})")
            
        except Exception as e:
            logger.error(f"Failed to initialize ChatService: {str(e)}")
            raise
    
    def create_conversation(self) -> str:
        """Create a new conversation and return its ID."""
        try:
            conversation_id = str(uuid.uuid4())
            self.conversations[conversation_id] = ConversationHistory(conversation_id=conversation_id)
            
            logger.info(f"Created new conversation: {conversation_id}")
            return conversation_id
            
        except Exception as e:
            logger.error(f"Failed to create conversation: {str(e)}")
            raise ConversationError(f"Failed to create new conversation: {str(e)}")
    
    def get_conversation(self, conversation_id: str) -> Optional[ConversationHistory]:
        """Get a conversation by ID."""
        return self.conversations.get(conversation_id)
    
    async def process_message(self, session_id: str, user_message: str, 
                             use_rag: bool = True, metadata: Optional[Dict] = None) -> ChatResponse:
        """
        Process a message with session context and RAG integration.
        
        Args:
            session_id: Session identifier
            user_message: User's message content
            use_rag: Whether to use RAG for context retrieval
            metadata: Optional metadata for the message
            
        Returns:
            ChatResponse with AI response and session information
        """
        start_time = time.time()
        
        try:
            # Validate inputs
            if not session_id or not session_id.strip():
                return ChatResponse(
                    message="",
                    session_id="",
                    success=False,
                    error="Session ID is required"
                )
            
            if not user_message or not user_message.strip():
                return ChatResponse(
                    message="",
                    session_id=session_id,
                    success=False,
                    error="Message cannot be empty"
                )
            
            # Validate session exists (if session service available)
            if self.session_service:
                session_response = self.session_service.get_session(session_id)
                if not session_response.session:
                    return ChatResponse(
                        message="",
                        session_id=session_id,
                        success=False,
                        error="Session not found"
                    )
            
            # Store user message (if message service available)
            user_msg_id = None
            if self.message_service:
                try:
                    user_msg = self.message_service.create_user_message(
                        session_id, user_message.strip(), metadata
                    )
                    user_msg_id = user_msg.id
                except MessageServiceError as e:
                    logger.warning(f"Failed to store user message: {str(e)}")
            
            # Get conversation context
            context = await self.get_conversation_context(session_id, user_message, use_rag)
            
            # Generate response
            assistant_response = await self.generate_response_with_context(context)
            
            # Store assistant response (if message service available)
            assistant_msg_id = None
            processing_time_ms = int((time.time() - start_time) * 1000)
            
            if self.message_service and user_msg_id:
                try:
                    assistant_msg = self.message_service.create_assistant_response(
                        user_msg_id, assistant_response, 
                        processing_time_ms=processing_time_ms,
                        metadata={"rag_used": use_rag, "context_tokens": context.total_tokens if hasattr(context, 'total_tokens') else None}
                    )
                    assistant_msg_id = assistant_msg.id
                except MessageServiceError as e:
                    logger.warning(f"Failed to store assistant response: {str(e)}")
            
            logger.info(f"Successfully processed message for session {session_id} in {processing_time_ms}ms")
            
            return ChatResponse(
                message=assistant_response,
                session_id=session_id,
                success=True,
                message_id=assistant_msg_id,
                processing_time_ms=processing_time_ms
            )
            
        except Exception as e:
            logger.error(f"Error processing message for session {session_id}: {str(e)}")
            return ChatResponse(
                message="",
                session_id=session_id,
                success=False,
                error=f"Failed to process message: {str(e)}"
            )

    async def send_message(self, request: ChatRequest) -> ChatResponse:
        """
        Send a message to OpenAI and return the response.
        Legacy method that supports both old conversation_id and new session_id.
        
        Args:
            request: ChatRequest containing the user's message and optional session/conversation ID
            
        Returns:
            ChatResponse with the AI's response or error information
        """
        try:
            # Determine session ID (prefer session_id over conversation_id for backward compatibility)
            session_id = request.session_id or request.conversation_id
            
            # If no session provided and we have session service, create a default session
            if not session_id and self.session_service:
                try:
                    session_response = self.session_service.create_default_session()
                    if session_response.session:
                        session_id = session_response.session.id
                        logger.info(f"Created default session: {session_id}")
                except SessionServiceError as e:
                    logger.warning(f"Failed to create default session: {str(e)}")
            
            # If still no session, fall back to legacy conversation handling
            if not session_id:
                return await self._legacy_send_message(request)
            
            # Use new session-aware processing
            response = await self.process_message(session_id, request.message)
            
            # Add legacy conversation_id for backward compatibility
            response.conversation_id = session_id
            
            return response
            
        except Exception as e:
            logger.error(f"Unexpected error in send_message: {str(e)}", exc_info=True)
            return ChatResponse(
                message="",
                session_id="",
                success=False,
                error="An unexpected error occurred. Please try again."
            )
    
    async def get_conversation_context(self, session_id: str, user_message: str, 
                                     use_rag: bool = True) -> ConversationContext:
        """
        Get conversation context combining chat history and RAG retrieval.
        
        Args:
            session_id: Session identifier
            user_message: Current user message for RAG query
            use_rag: Whether to include RAG context
            
        Returns:
            ConversationContext with chat history and retrieved documents
        """
        try:
            # Get chat history
            chat_history = []
            if self.message_service:
                try:
                    context = self.message_service.get_conversation_context(
                        session_id, limit=self.max_history_messages
                    )
                    chat_history = context.messages
                except MessageServiceError as e:
                    logger.warning(f"Failed to get chat history: {str(e)}")
            
            # Get RAG context if enabled
            rag_context = None
            if use_rag and self.rag_service:
                try:
                    rag_context = self.rag_service.create_rag_context(
                        session_id=session_id,
                        query=user_message,
                        chat_history=chat_history
                    )
                except RAGServiceError as e:
                    logger.warning(f"RAG retrieval failed, continuing without RAG: {str(e)}")
            
            # Create combined context
            if rag_context:
                return ConversationContext(
                    session_id=session_id,
                    messages=rag_context.chat_history,
                    retrieved_documents=rag_context.retrieved_documents,
                    total_tokens=rag_context.total_tokens
                )
            else:
                return ConversationContext(
                    session_id=session_id,
                    messages=chat_history,
                    retrieved_documents=[],
                    total_tokens=sum(msg.token_count or len(msg.content.split()) for msg in chat_history)
                )
                
        except Exception as e:
            logger.error(f"Error getting conversation context: {str(e)}")
            # Return minimal context on error
            return ConversationContext(
                session_id=session_id,
                messages=[],
                retrieved_documents=[],
                total_tokens=0
            )

    async def generate_response_with_context(self, context: ConversationContext) -> str:
        """
        Generate response using combined chat history and RAG context.
        
        Args:
            context: Conversation context with history and retrieved documents
            
        Returns:
            Generated response text
            
        Raises:
            OpenAIAPIError: If response generation fails
        """
        try:
            # Build messages for OpenAI API
            messages = self._build_context_messages(context)
            
            # Truncate if exceeds token limit
            messages = self._truncate_context_if_needed(messages)
            
            logger.info(f"Generating response with {len(messages)} context messages")
            
            # Call OpenAI API
            response = await self._call_openai_api_with_retry(messages)
            
            # Validate and extract response
            if not response or not response.choices:
                raise OpenAIAPIError("Invalid response from OpenAI API")
            
            assistant_message = response.choices[0].message.content
            if not assistant_message:
                raise OpenAIAPIError("Empty response from OpenAI API")
            
            return assistant_message.strip()
            
        except OpenAIAPIError:
            raise
        except Exception as e:
            logger.error(f"Error generating response: {str(e)}")
            raise OpenAIAPIError(f"Response generation failed: {str(e)}")

    def _build_context_messages(self, context: ConversationContext) -> List[Dict[str, str]]:
        """
        Build OpenAI API messages from conversation context.
        
        Args:
            context: Conversation context
            
        Returns:
            List of messages in OpenAI format
        """
        messages = []
        
        # Add system message with RAG context if available
        if context.retrieved_documents:
            system_content = self._build_system_message_with_rag(context.retrieved_documents)
            messages.append({"role": "system", "content": system_content})
        
        # Add chat history messages
        for message in context.messages:
            messages.append({
                "role": message.role,
                "content": message.content
            })
        
        return messages

    def _build_system_message_with_rag(self, retrieved_documents) -> str:
        """
        Build system message incorporating RAG context.
        
        Args:
            retrieved_documents: List of retrieved documents
            
        Returns:
            System message content with RAG context
        """
        if not retrieved_documents:
            return "You are a helpful AI assistant."
        
        context_parts = [
            "You are a helpful AI assistant. Use the following context information to provide accurate and relevant responses.",
            "",
            "Context Information:"
        ]
        
        for i, doc in enumerate(retrieved_documents[:5], 1):  # Limit to top 5 documents
            context_parts.append(f"{i}. {doc.content[:500]}...")  # Truncate long documents
            if doc.source:
                context_parts.append(f"   Source: {doc.source}")
        
        context_parts.extend([
            "",
            "Instructions:",
            "- Use the context information to answer questions when relevant",
            "- If the context doesn't contain relevant information, rely on your general knowledge",
            "- Be clear about when you're using provided context vs. general knowledge",
            "- Provide helpful, accurate, and concise responses"
        ])
        
        return "\n".join(context_parts)

    def _truncate_context_if_needed(self, messages: List[Dict[str, str]]) -> List[Dict[str, str]]:
        """
        Truncate context messages if they exceed token limits.
        
        Args:
            messages: List of messages in OpenAI format
            
        Returns:
            Truncated messages list
        """
        # Rough token estimation (1 token ≈ 0.75 words)
        total_tokens = sum(len(msg["content"].split()) * 1.3 for msg in messages)
        
        if total_tokens <= self.max_context_tokens:
            return messages
        
        logger.info(f"Context exceeds {self.max_context_tokens} tokens ({total_tokens}), truncating...")
        
        # Keep system message if present
        system_messages = [msg for msg in messages if msg["role"] == "system"]
        chat_messages = [msg for msg in messages if msg["role"] != "system"]
        
        # Truncate chat messages from the beginning (keep recent messages)
        while chat_messages and total_tokens > self.max_context_tokens:
            removed_msg = chat_messages.pop(0)
            total_tokens -= len(removed_msg["content"].split()) * 1.3
        
        return system_messages + chat_messages

    async def _legacy_send_message(self, request: ChatRequest) -> ChatResponse:
        """
        Legacy message processing for backward compatibility.
        
        Args:
            request: ChatRequest with legacy conversation handling
            
        Returns:
            ChatResponse using legacy conversation system
        """
        conversation_id = None
        try:
            # Validate request
            if not request.message or len(request.message.strip()) == 0:
                raise ValueError("Message cannot be empty")
            
            if len(request.message) > 4000:
                raise ValueError("Message too long (maximum 4000 characters)")
            
            # Get or create conversation
            conversation_id = request.conversation_id
            if not conversation_id:
                conversation_id = self.create_conversation()
            
            conversation = self.get_conversation(conversation_id)
            if not conversation:
                logger.warning(f"Conversation {conversation_id} not found, creating new one")
                conversation_id = self.create_conversation()
                conversation = self.get_conversation(conversation_id)
            
            # Check conversation message limit
            if len(conversation.messages) > 100:
                logger.warning(f"Conversation {conversation_id} has too many messages, truncating")
                conversation.messages = conversation.messages[-50:]  # Keep last 50 messages
            
            # Add user message to conversation
            conversation.add_message("user", request.message)
            
            # Prepare messages for OpenAI API
            messages = conversation.get_openai_messages()
            
            logger.info(f"Sending message to OpenAI API for conversation {conversation_id}")
            
            # Call OpenAI API with retry logic
            response = await self._call_openai_api_with_retry(messages)
            
            # Validate response
            if not response or not response.choices:
                raise OpenAIAPIError("Invalid response from OpenAI API")
            
            assistant_message = response.choices[0].message.content
            if not assistant_message:
                raise OpenAIAPIError("Empty response from OpenAI API")
            
            # Add assistant response to conversation
            conversation.add_message("assistant", assistant_message)
            
            logger.info(f"Successfully processed message for conversation {conversation_id}")
            
            return ChatResponse(
                message=assistant_message,
                session_id=conversation_id,
                conversation_id=conversation_id,
                success=True
            )
            
        except ValueError as e:
            logger.warning(f"Validation error in _legacy_send_message: {str(e)}")
            return ChatResponse(
                message="",
                session_id=conversation_id or "",
                conversation_id=conversation_id or "",
                success=False,
                error=f"Invalid input: {str(e)}"
            )
        except (APIKeyError, ConversationError, OpenAIAPIError) as e:
            logger.error(f"Service error in _legacy_send_message: {str(e)}")
            return ChatResponse(
                message="",
                session_id=conversation_id or "",
                conversation_id=conversation_id or "",
                success=False,
                error=str(e)
            )
        except Exception as e:
            logger.error(f"Unexpected error in _legacy_send_message: {str(e)}", exc_info=True)
            return ChatResponse(
                message="",
                session_id=conversation_id or "",
                conversation_id=conversation_id or "",
                success=False,
                error="An unexpected error occurred. Please try again."
            )

    async def _call_openai_api_with_retry(self, messages: list) -> ChatCompletion:
        """
        Make API call to OpenAI with retry logic.
        
        Args:
            messages: List of messages in OpenAI format
            
        Returns:
            ChatCompletion response from OpenAI
            
        Raises:
            OpenAIAPIError: If all retry attempts fail
        """
        last_exception = None
        
        for attempt in range(self.max_retries):
            try:
                return await self._call_openai_api(messages)
                
            except RateLimitError as e:
                last_exception = e
           
        try:
            # Validate request
            if not request.message or len(request.message.strip()) == 0:
                raise ValueError("Message cannot be empty")
            
            if len(request.message) > 4000:
                raise ValueError("Message too long (maximum 4000 characters)")
            
            # Get or create conversation
            conversation_id = request.conversation_id
            if not conversation_id:
                conversation_id = self.create_conversation()
            
            conversation = self.get_conversation(conversation_id)
            if not conversation:
                logger.warning(f"Conversation {conversation_id} not found, creating new one")
                conversation_id = self.create_conversation()
                conversation = self.get_conversation(conversation_id)
            
            # Check conversation message limit
            if len(conversation.messages) > 100:
                logger.warning(f"Conversation has {len(conversation.messages)} messages")
        
        Args:
            messages: List of messages in OpenAI format
            
        Returns:
            ChatCompletion response from OpenAI
            
        Raises:
            OpenAIAPIError: If all retry attempts fail
        """
        last_exception = None
        
        for attempt in range(self.max_retries):
            try:
                return await self._call_openai_api(messages)
                
            except RateLimitError as e:
                last_exception = e
                wait_time = self.retry_delay * (2 ** attempt)  # Exponential backoff
                logger.warning(f"Rate limit hit, retrying in {wait_time}s (attempt {attempt + 1}/{self.max_retries})")
                await asyncio.sleep(wait_time)
                
            except APIConnectionError as e:
                last_exception = e
                wait_time = self.retry_delay * (2 ** attempt)
                logger.warning(f"Connection error, retrying in {wait_time}s (attempt {attempt + 1}/{self.max_retries})")
                await asyncio.sleep(wait_time)
                
            except (AuthenticationError, APIError) as e:
                # Don't retry authentication or other API errors
                logger.error(f"Non-retryable OpenAI API error: {str(e)}")
                raise OpenAIAPIError(f"OpenAI API error: {str(e)}")
                
            except Exception as e:
                last_exception = e
                logger.error(f"Unexpected error in API call (attempt {attempt + 1}/{self.max_retries}): {str(e)}")
                if attempt == self.max_retries - 1:
                    break
                await asyncio.sleep(self.retry_delay)
        
        # All retries failed
        error_msg = f"Failed to get response from OpenAI after {self.max_retries} attempts"
        if last_exception:
            error_msg += f": {str(last_exception)}"
        raise OpenAIAPIError(error_msg)
    
    async def _call_openai_api(self, messages: list) -> ChatCompletion:
        """
        Make the actual API call to OpenAI.
        
        Args:
            messages: List of messages in OpenAI format
            
        Returns:
            ChatCompletion response from OpenAI
            
        Raises:
            Various OpenAI exceptions: For different types of API failures
        """
        try:
            # Run the synchronous OpenAI call in a thread pool
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: self.client.chat.completions.create(
                    model=self.default_model,
                    messages=messages,
                    temperature=0.7,
                    max_tokens=1000,
                    timeout=30.0
                )
            )
            return response
            
        except AuthenticationError as e:
            logger.error(f"OpenAI authentication failed: {str(e)}")
            raise AuthenticationError("Invalid OpenAI API key")
            
        except RateLimitError as e:
            logger.warning(f"OpenAI rate limit exceeded: {str(e)}")
            raise
            
        except APIConnectionError as e:
            logger.error(f"OpenAI connection failed: {str(e)}")
            raise
            
        except APIError as e:
            logger.error(f"OpenAI API error: {str(e)}")
            raise
            
        except Exception as e:
            logger.error(f"Unexpected error in OpenAI API call: {str(e)}")
            raise Exception(f"Unexpected error: {str(e)}")
    
    def clear_conversation(self, conversation_id: str) -> bool:
        """
        Clear a conversation's message history.
        
        Args:
            conversation_id: ID of the conversation to clear
            
        Returns:
            True if conversation was cleared, False if not found
        """
        if conversation_id in self.conversations:
            self.conversations[conversation_id].messages.clear()
            logger.info(f"Cleared conversation: {conversation_id}")
            return True
        return False
    
    def delete_conversation(self, conversation_id: str) -> bool:
        """
        Delete a conversation entirely.
        
        Args:
            conversation_id: ID of the conversation to delete
            
        Returns:
            True if conversation was deleted, False if not found
        """
        if conversation_id in self.conversations:
            del self.conversations[conversation_id]
            logger.info(f"Deleted conversation: {conversation_id}")
            return True
        return False
    
    def get_conversation_count(self) -> int:
        """Get the total number of active conversations."""
        return len(self.conversations)
    
    def health_check(self) -> Dict[str, any]:
        """
        Perform a health check of the service.
        
        Returns:
            Dictionary with health status information
        """
        health_info = {
            "status": "unknown",
            "api_connection": "unknown",
            "active_conversations": 0,
            "model": self.default_model,
            "timestamp": None
        }
        
        try:
            # Get basic service info
            health_info["active_conversations"] = self.get_conversation_count()
            health_info["timestamp"] = str(uuid.uuid4())  # Simple timestamp alternative
            
            # Test API key validity with a minimal call
            test_response = self.client.chat.completions.create(
                model=self.default_model,
                messages=[{"role": "user", "content": "test"}],
                max_tokens=1,
                timeout=10.0
            )
            
            health_info.update({
                "status": "healthy",
                "api_connection": "ok"
            })
            
            return health_info
            
        except AuthenticationError as e:
            logger.error(f"Health check - Authentication failed: {str(e)}")
            health_info.update({
                "status": "unhealthy",
                "api_connection": "authentication_failed",
                "error": "Invalid API key"
            })
            
        except RateLimitError as e:
            logger.warning(f"Health check - Rate limited: {str(e)}")
            health_info.update({
                "status": "degraded",
                "api_connection": "rate_limited",
                "error": "Rate limit exceeded"
            })
            
        except APIConnectionError as e:
            logger.error(f"Health check - Connection failed: {str(e)}")
            health_info.update({
                "status": "unhealthy",
                "api_connection": "connection_failed",
                "error": "Cannot connect to OpenAI API"
            })
            
        except Exception as e:
            logger.error(f"Health check - Unexpected error: {str(e)}")
            health_info.update({
                "status": "unhealthy",
                "api_connection": "failed",
                "error": f"Unexpected error: {str(e)}"
            })
        
        return health_info