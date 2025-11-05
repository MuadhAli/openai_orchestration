"""
RAG-enhanced chat service that combines chat history with retrieved context.
"""
import logging
import os
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session as DBSession
import openai
from openai import OpenAI

from app.services.message_service import MessageService
from app.services.conversational_rag import ConversationalRAGService
from app.services.embedding_service import EmbeddingService
from app.models.message import MessageResponse

logger = logging.getLogger(__name__)


class RAGChatService:
    """Chat service enhanced with RAG capabilities."""
    
    def __init__(self, db_session: DBSession):
        """Initialize the RAG chat service."""
        self.db_session = db_session
        self.message_service = MessageService(db_session)
        self.embedding_service = EmbeddingService()
        self.conversational_rag = ConversationalRAGService(db_session, self.embedding_service)
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.model = "gpt-3.5-turbo"
    
    async def process_chat_message(self, session_id: str, user_message: str) -> MessageResponse:
        """Process a chat message with conversational RAG enhancement."""
        try:
            # 1. Store the user message
            user_msg = self.message_service.create_user_message(session_id, user_message)
            
            # 2. Store embedding for the user message
            await self.conversational_rag.store_message_embedding(user_msg)
            
            # 3. Get chat history for context
            chat_history = self.message_service.get_session_messages(session_id)
            
            # 4. Get relevant context from past conversations
            relevant_conversations = await self.conversational_rag.find_relevant_conversations(
                user_message, session_id
            )
            
            # 5. Generate AI response
            ai_response = self._generate_response(user_message, chat_history.messages, relevant_conversations)
            
            # 6. Store the AI response
            assistant_msg = self.message_service.create_assistant_message(session_id, ai_response)
            
            # 7. Store embedding for the AI response
            await self.conversational_rag.store_message_embedding(assistant_msg)
            
            logger.info(f"Processed chat message for session {session_id}")
            return assistant_msg
            
        except Exception as e:
            logger.error(f"Error processing chat message: {str(e)}")
            # Return error message as assistant response
            error_response = "I apologize, but I encountered an error processing your message. Please try again."
            return self.message_service.create_assistant_message(session_id, error_response)
    
    def _generate_response(self, user_message: str, chat_history: List[MessageResponse], 
                          relevant_conversations: List[str]) -> str:
        """Generate AI response using chat history and RAG context."""
        try:
            # Build the prompt with context and history
            messages = []
            
            # System message with conversational context handling
            system_content = """You are a helpful AI assistant with access to past conversations. You can learn from previous discussions to provide better, more contextual responses.

Instructions:
1. Use relevant information from past conversations when it helps answer the current question
2. Maintain conversation continuity within the current session
3. If past conversations contain relevant context, incorporate that knowledge naturally
4. Be concise but comprehensive in your responses
5. Always be helpful and accurate"""
            
            if relevant_conversations:
                past_context = "\n".join(relevant_conversations)
                system_content += f"\n\n=== RELEVANT PAST CONVERSATIONS ===\n{past_context}\n=== END PAST CONVERSATIONS ==="
            
            messages.append({"role": "system", "content": system_content})
            
            # Add recent chat history (limit to last 8 messages to save tokens for context)
            recent_history = chat_history[-8:] if len(chat_history) > 8 else chat_history
            
            for msg in recent_history[:-1]:  # Exclude the current user message as it will be added separately
                if msg.role in ["user", "assistant"]:
                    messages.append({"role": msg.role, "content": msg.content})
            
            # Add the current user message
            messages.append({"role": "user", "content": user_message})
            
            # Generate response
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=1000,
                temperature=0.7
            )
            
            ai_response = response.choices[0].message.content
            
            # Log context usage
            context_used = f"with {len(relevant_conversations)} past conversations" if relevant_conversations else "without past context"
            logger.info(f"Generated AI response {context_used}, history length: {len(recent_history)}")
            return ai_response
            
        except Exception as e:
            logger.error(f"Error generating AI response: {str(e)}")
            return "I apologize, but I'm having trouble generating a response right now. Please try again."
    
    def get_chat_history(self, session_id: str) -> List[Dict[str, Any]]:
        """Get formatted chat history for a session."""
        try:
            messages = self.message_service.get_session_messages(session_id)
            
            # Format messages for frontend
            formatted_messages = []
            for msg in messages.messages:
                formatted_messages.append({
                    "id": msg.id,
                    "role": msg.role,
                    "content": msg.content,
                    "timestamp": msg.timestamp.isoformat()
                })
            
            return formatted_messages
            
        except Exception as e:
            logger.error(f"Error getting chat history: {str(e)}")
            return []