"""
Chat service for handling OpenAI API integration and conversation management.
"""
import os
import uuid
import logging
import asyncio
from typing import Dict, Optional
from openai import OpenAI, APIError, RateLimitError, APIConnectionError, AuthenticationError
from openai.types.chat import ChatCompletion
from dotenv import load_dotenv

from app.models.chat import ChatRequest, ChatResponse, ConversationHistory, ErrorResponse

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
    """Service class for managing chat conversations and OpenAI API integration."""
    
    def __init__(self):
        """Initialize the chat service with OpenAI client and conversation storage."""
        try:
            self.api_key = os.getenv("OPENAI_API_KEY")
            if not self.api_key:
                raise APIKeyError("OPENAI_API_KEY environment variable is required")
            
            if not self.api_key.startswith('sk-'):
                raise APIKeyError("Invalid OpenAI API key format")
            
            self.client = OpenAI(api_key=self.api_key)
            self.conversations: Dict[str, ConversationHistory] = {}
            self.default_model = "gpt-4o-mini"
            self.max_retries = 3
            self.retry_delay = 1.0
            
            logger.info("ChatService initialized successfully")
            
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
    
    async def send_message(self, request: ChatRequest) -> ChatResponse:
        """
        Send a message to OpenAI and return the response.
        
        Args:
            request: ChatRequest containing the user's message and optional conversation_id
            
        Returns:
            ChatResponse with the AI's response or error information
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
                conversation_id=conversation_id,
                success=True
            )
            
        except ValueError as e:
            logger.warning(f"Validation error in send_message: {str(e)}")
            return ChatResponse(
                message="",
                conversation_id=conversation_id or "",
                success=False,
                error=f"Invalid input: {str(e)}"
            )
        except (APIKeyError, ConversationError, OpenAIAPIError) as e:
            logger.error(f"Service error in send_message: {str(e)}")
            return ChatResponse(
                message="",
                conversation_id=conversation_id or "",
                success=False,
                error=str(e)
            )
        except Exception as e:
            logger.error(f"Unexpected error in send_message: {str(e)}", exc_info=True)
            return ChatResponse(
                message="",
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