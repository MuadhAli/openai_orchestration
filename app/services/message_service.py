"""
Simple service layer for message management.
"""
import logging
from datetime import datetime
from typing import List, Optional
from sqlalchemy.orm import Session as DBSession
from sqlalchemy.exc import SQLAlchemyError

from app.models.message import MessageCreate, MessageResponse, MessageListResponse
from app.database.models import Message, Session, MessageRole

logger = logging.getLogger(__name__)


class MessageService:
    """Simple service for message management."""
    
    def __init__(self, db_session: DBSession):
        """Initialize service with database session."""
        self.db_session = db_session
    
    def create_message(self, message_create: MessageCreate) -> MessageResponse:
        """Create a new message."""
        try:
            # Verify session exists
            session = self.db_session.query(Session).filter(Session.id == message_create.session_id).first()
            if not session:
                raise Exception("Session not found")
            
            # Create message
            message = Message(
                session_id=message_create.session_id,
                content=message_create.content,
                role=MessageRole.USER if message_create.role == "user" else MessageRole.ASSISTANT
            )
            
            self.db_session.add(message)
            self.db_session.commit()
            self.db_session.refresh(message)
            
            logger.info(f"Created message: {message.id}")
            return MessageResponse(
                id=message.id,
                session_id=message.session_id,
                content=message.content,
                role=message.role.value,
                timestamp=message.timestamp
            )
            
        except SQLAlchemyError as e:
            self.db_session.rollback()
            logger.error(f"Database error creating message: {str(e)}")
            raise Exception("Failed to create message")
        except Exception as e:
            self.db_session.rollback()
            logger.error(f"Error creating message: {str(e)}")
            raise
    
    def get_session_messages(self, session_id: str) -> MessageListResponse:
        """Get all messages for a session."""
        try:
            messages = (
                self.db_session.query(Message)
                .filter(Message.session_id == session_id)
                .order_by(Message.timestamp.asc())
                .all()
            )
            
            message_responses = [
                MessageResponse(
                    id=message.id,
                    session_id=message.session_id,
                    content=message.content,
                    role=message.role.value,
                    timestamp=message.timestamp
                )
                for message in messages
            ]
            
            return MessageListResponse(messages=message_responses)
            
        except SQLAlchemyError as e:
            logger.error(f"Database error getting messages for session {session_id}: {str(e)}")
            return MessageListResponse(messages=[])
    
    def create_user_message(self, session_id: str, content: str) -> MessageResponse:
        """Create a user message."""
        message_create = MessageCreate(
            session_id=session_id,
            content=content,
            role="user"
        )
        return self.create_message(message_create)
    
    def create_assistant_message(self, session_id: str, content: str) -> MessageResponse:
        """Create an assistant message."""
        message_create = MessageCreate(
            session_id=session_id,
            content=content,
            role="assistant"
        )
        return self.create_message(message_create)