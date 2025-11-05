"""
Repository for message data access operations.
"""
import logging
import uuid
from datetime import datetime
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session as DBSession
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from sqlalchemy import func, desc, asc, and_, or_

from app.database.models import Message as MessageModel, Session as SessionModel, MessageRole
from app.models.message import (
    Message, MessageCreate, MessageUpdate, MessageSummary, 
    MessageStats, MessageSearchRequest
)

logger = logging.getLogger(__name__)


class MessageRepositoryError(Exception):
    """Base exception for message repository operations."""
    pass


class MessageNotFoundError(MessageRepositoryError):
    """Exception raised when a message is not found."""
    pass


class SessionNotFoundError(MessageRepositoryError):
    """Exception raised when a session is not found."""
    pass


class MessageRepository:
    """Repository for message CRUD operations."""
    
    def __init__(self, db_session: DBSession):
        """Initialize repository with database session."""
        self.db_session = db_session
    
    def create_message(self, message_create: MessageCreate) -> Message:
        """
        Create a new message in the database.
        
        Args:
            message_create: Message creation data
            
        Returns:
            Created message
            
        Raises:
            MessageRepositoryError: If creation fails
            SessionNotFoundError: If session doesn't exist
        """
        try:
            # Verify session exists
            session_exists = self.db_session.query(SessionModel).filter(
                SessionModel.id == message_create.session_id
            ).first() is not None
            
            if not session_exists:
                raise SessionNotFoundError(f"Session with ID {message_create.session_id} not found")
            
            # Convert role string to enum
            role_enum = MessageRole.USER if message_create.role == "user" else MessageRole.ASSISTANT
            
            # Create SQLAlchemy model instance
            db_message = MessageModel(
                session_id=message_create.session_id,
                content=message_create.content,
                role=role_enum,
                message_metadata=message_create.message_metadata or {}
            )
            
            # Add to database
            self.db_session.add(db_message)
            self.db_session.commit()
            self.db_session.refresh(db_message)
            
            logger.info(f"Created message with ID: {db_message.id}")
            
            # Convert to Pydantic model
            return self._db_message_to_pydantic(db_message)
            
        except SessionNotFoundError:
            raise
        except IntegrityError as e:
            self.db_session.rollback()
            logger.error(f"Integrity error creating message: {str(e)}")
            raise MessageRepositoryError(f"Failed to create message: {str(e)}")
        except SQLAlchemyError as e:
            self.db_session.rollback()
            logger.error(f"Database error creating message: {str(e)}")
            raise MessageRepositoryError(f"Database error: {str(e)}")
        except Exception as e:
            self.db_session.rollback()
            logger.error(f"Unexpected error creating message: {str(e)}")
            raise MessageRepositoryError(f"Unexpected error: {str(e)}")
    
    def get_message_by_id(self, message_id: str) -> Message:
        """
        Get a message by its ID.
        
        Args:
            message_id: Message identifier
            
        Returns:
            Message data
            
        Raises:
            MessageNotFoundError: If message doesn't exist
            MessageRepositoryError: If retrieval fails
        """
        try:
            db_message = self.db_session.query(MessageModel).filter(
                MessageModel.id == message_id
            ).first()
            
            if not db_message:
                raise MessageNotFoundError(f"Message with ID {message_id} not found")
            
            return self._db_message_to_pydantic(db_message)
            
        except MessageNotFoundError:
            raise
        except SQLAlchemyError as e:
            logger.error(f"Database error retrieving message {message_id}: {str(e)}")
            raise MessageRepositoryError(f"Database error: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error retrieving message {message_id}: {str(e)}")
            raise MessageRepositoryError(f"Unexpected error: {str(e)}")
    
    def update_message(self, message_id: str, message_update: MessageUpdate) -> Message:
        """
        Update an existing message.
        
        Args:
            message_id: Message identifier
            message_update: Update data
            
        Returns:
            Updated message
            
        Raises:
            MessageNotFoundError: If message doesn't exist
            MessageRepositoryError: If update fails
        """
        try:
            db_message = self.db_session.query(MessageModel).filter(
                MessageModel.id == message_id
            ).first()
            
            if not db_message:
                raise MessageNotFoundError(f"Message with ID {message_id} not found")
            
            # Update fields if provided
            if message_update.content is not None:
                db_message.content = message_update.content
            
            if message_update.message_metadata is not None:
                db_message.message_metadata = message_update.message_metadata
            
            if message_update.token_count is not None:
                db_message.token_count = message_update.token_count
            
            if message_update.processing_time_ms is not None:
                db_message.processing_time_ms = message_update.processing_time_ms
            
            self.db_session.commit()
            self.db_session.refresh(db_message)
            
            logger.info(f"Updated message with ID: {message_id}")
            
            return self._db_message_to_pydantic(db_message)
            
        except MessageNotFoundError:
            raise
        except IntegrityError as e:
            self.db_session.rollback()
            logger.error(f"Integrity error updating message {message_id}: {str(e)}")
            raise MessageRepositoryError(f"Failed to update message: {str(e)}")
        except SQLAlchemyError as e:
            self.db_session.rollback()
            logger.error(f"Database error updating message {message_id}: {str(e)}")
            raise MessageRepositoryError(f"Database error: {str(e)}")
        except Exception as e:
            self.db_session.rollback()
            logger.error(f"Unexpected error updating message {message_id}: {str(e)}")
            raise MessageRepositoryError(f"Unexpected error: {str(e)}")
    
    def delete_message(self, message_id: str) -> bool:
        """
        Delete a message.
        
        Args:
            message_id: Message identifier
            
        Returns:
            True if deleted successfully
            
        Raises:
            MessageNotFoundError: If message doesn't exist
            MessageRepositoryError: If deletion fails
        """
        try:
            db_message = self.db_session.query(MessageModel).filter(
                MessageModel.id == message_id
            ).first()
            
            if not db_message:
                raise MessageNotFoundError(f"Message with ID {message_id} not found")
            
            # Delete message
            self.db_session.delete(db_message)
            self.db_session.commit()
            
            logger.info(f"Deleted message with ID: {message_id}")
            return True
            
        except MessageNotFoundError:
            raise
        except SQLAlchemyError as e:
            self.db_session.rollback()
            logger.error(f"Database error deleting message {message_id}: {str(e)}")
            raise MessageRepositoryError(f"Database error: {str(e)}")
        except Exception as e:
            self.db_session.rollback()
            logger.error(f"Unexpected error deleting message {message_id}: {str(e)}")
            raise MessageRepositoryError(f"Unexpected error: {str(e)}")
    
    def get_messages_by_session(
        self, 
        session_id: str, 
        page: int = 1, 
        page_size: int = 50,
        order_desc: bool = False
    ) -> List[MessageSummary]:
        """
        Get messages for a specific session with pagination.
        
        Args:
            session_id: Session identifier
            page: Page number (1-based)
            page_size: Number of messages per page
            order_desc: Whether to order by timestamp descending
            
        Returns:
            List of message summaries
            
        Raises:
            MessageRepositoryError: If retrieval fails
        """
        try:
            # Validate parameters
            if page < 1:
                raise ValueError("Page must be greater than 0")
            if page_size < 1 or page_size > 100:
                raise ValueError("Page size must be between 1 and 100")
            
            # Build query
            query = self.db_session.query(MessageModel).filter(
                MessageModel.session_id == session_id
            )
            
            # Apply ordering
            if order_desc:
                query = query.order_by(desc(MessageModel.timestamp))
            else:
                query = query.order_by(asc(MessageModel.timestamp))
            
            # Apply pagination
            offset = (page - 1) * page_size
            results = query.offset(offset).limit(page_size).all()
            
            # Convert to MessageSummary objects
            summaries = []
            for db_message in results:
                # Create content preview (first 100 characters)
                content_preview = db_message.content[:100]
                if len(db_message.content) > 100:
                    content_preview += "..."
                
                summary = MessageSummary(
                    id=db_message.id,
                    session_id=db_message.session_id,
                    role=db_message.role.value,
                    content_preview=content_preview,
                    timestamp=db_message.timestamp,
                    token_count=db_message.token_count
                )
                summaries.append(summary)
            
            logger.info(f"Retrieved {len(summaries)} messages for session {session_id} (page {page})")
            return summaries
            
        except ValueError as e:
            logger.error(f"Invalid parameters for get_messages_by_session: {str(e)}")
            raise MessageRepositoryError(f"Invalid parameters: {str(e)}")
        except SQLAlchemyError as e:
            logger.error(f"Database error retrieving messages for session {session_id}: {str(e)}")
            raise MessageRepositoryError(f"Database error: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error retrieving messages for session {session_id}: {str(e)}")
            raise MessageRepositoryError(f"Unexpected error: {str(e)}")
    
    def get_session_message_count(self, session_id: str) -> int:
        """
        Get total number of messages in a session.
        
        Args:
            session_id: Session identifier
            
        Returns:
            Total message count
            
        Raises:
            MessageRepositoryError: If count fails
        """
        try:
            count = self.db_session.query(MessageModel).filter(
                MessageModel.session_id == session_id
            ).count()
            return count
        except SQLAlchemyError as e:
            logger.error(f"Database error counting messages for session {session_id}: {str(e)}")
            raise MessageRepositoryError(f"Database error: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error counting messages for session {session_id}: {str(e)}")
            raise MessageRepositoryError(f"Unexpected error: {str(e)}")
    
    def message_exists(self, message_id: str) -> bool:
        """
        Check if a message exists.
        
        Args:
            message_id: Message identifier
            
        Returns:
            True if message exists
            
        Raises:
            MessageRepositoryError: If check fails
        """
        try:
            exists = self.db_session.query(MessageModel).filter(
                MessageModel.id == message_id
            ).first() is not None
            return exists
        except SQLAlchemyError as e:
            logger.error(f"Database error checking message existence: {str(e)}")
            raise MessageRepositoryError(f"Database error: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error checking message existence: {str(e)}")
            raise MessageRepositoryError(f"Unexpected error: {str(e)}")
    
    def search_messages(self, search_request: MessageSearchRequest) -> List[MessageSummary]:
        """
        Search messages in a session by content.
        
        Args:
            search_request: Search parameters
            
        Returns:
            List of matching message summaries
            
        Raises:
            MessageRepositoryError: If search fails
        """
        try:
            # Build base query
            query = self.db_session.query(MessageModel).filter(
                MessageModel.session_id == search_request.session_id
            )
            
            # Add content search (case-insensitive)
            query = query.filter(
                MessageModel.content.ilike(f"%{search_request.query}%")
            )
            
            # Add role filter if specified
            if search_request.role_filter:
                role_enum = MessageRole.USER if search_request.role_filter == "user" else MessageRole.ASSISTANT
                query = query.filter(MessageModel.role == role_enum)
            
            # Order by timestamp (most recent first)
            query = query.order_by(desc(MessageModel.timestamp))
            
            # Apply limit
            results = query.limit(search_request.limit).all()
            
            # Convert to MessageSummary objects
            summaries = []
            for db_message in results:
                # Create content preview with search term highlighted
                content_preview = db_message.content[:100]
                if len(db_message.content) > 100:
                    content_preview += "..."
                
                summary = MessageSummary(
                    id=db_message.id,
                    session_id=db_message.session_id,
                    role=db_message.role.value,
                    content_preview=content_preview,
                    timestamp=db_message.timestamp,
                    token_count=db_message.token_count
                )
                summaries.append(summary)
            
            logger.info(f"Found {len(summaries)} messages matching query '{search_request.query}' in session {search_request.session_id}")
            return summaries
            
        except SQLAlchemyError as e:
            logger.error(f"Database error searching messages: {str(e)}")
            raise MessageRepositoryError(f"Database error: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error searching messages: {str(e)}")
            raise MessageRepositoryError(f"Unexpected error: {str(e)}")
    
    def get_session_message_stats(self, session_id: str) -> MessageStats:
        """
        Get statistics about messages in a session.
        
        Args:
            session_id: Session identifier
            
        Returns:
            Message statistics
            
        Raises:
            MessageRepositoryError: If stats calculation fails
        """
        try:
            # Get basic counts
            total_query = self.db_session.query(MessageModel).filter(
                MessageModel.session_id == session_id
            )
            
            total_messages = total_query.count()
            
            if total_messages == 0:
                return MessageStats(
                    session_id=session_id,
                    total_messages=0,
                    user_messages=0,
                    assistant_messages=0,
                    total_tokens=0,
                    average_tokens_per_message=0.0
                )
            
            # Count by role
            user_messages = total_query.filter(MessageModel.role == MessageRole.USER).count()
            assistant_messages = total_query.filter(MessageModel.role == MessageRole.ASSISTANT).count()
            
            # Get token statistics
            token_stats = self.db_session.query(
                func.sum(MessageModel.token_count).label('total_tokens'),
                func.avg(MessageModel.token_count).label('avg_tokens'),
                func.min(MessageModel.timestamp).label('first_message'),
                func.max(MessageModel.timestamp).label('last_message'),
                func.avg(MessageModel.processing_time_ms).label('avg_processing_time')
            ).filter(
                MessageModel.session_id == session_id
            ).first()
            
            total_tokens = int(token_stats.total_tokens or 0)
            avg_tokens = float(token_stats.avg_tokens or 0.0)
            first_message_at = token_stats.first_message
            last_message_at = token_stats.last_message
            avg_processing_time = float(token_stats.avg_processing_time or 0.0) if token_stats.avg_processing_time else None
            
            return MessageStats(
                session_id=session_id,
                total_messages=total_messages,
                user_messages=user_messages,
                assistant_messages=assistant_messages,
                total_tokens=total_tokens,
                average_tokens_per_message=round(avg_tokens, 2),
                first_message_at=first_message_at,
                last_message_at=last_message_at,
                average_processing_time_ms=round(avg_processing_time, 2) if avg_processing_time else None
            )
            
        except SQLAlchemyError as e:
            logger.error(f"Database error calculating message stats for session {session_id}: {str(e)}")
            raise MessageRepositoryError(f"Database error: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error calculating message stats for session {session_id}: {str(e)}")
            raise MessageRepositoryError(f"Unexpected error: {str(e)}")
    
    def get_conversation_history(
        self, 
        session_id: str, 
        limit: Optional[int] = None,
        include_metadata: bool = False
    ) -> List[Message]:
        """
        Get complete conversation history for a session in chronological order.
        
        Args:
            session_id: Session identifier
            limit: Maximum number of messages to return (most recent)
            include_metadata: Whether to include message metadata
            
        Returns:
            List of messages in chronological order
            
        Raises:
            MessageRepositoryError: If retrieval fails
        """
        try:
            # Build query
            query = self.db_session.query(MessageModel).filter(
                MessageModel.session_id == session_id
            ).order_by(asc(MessageModel.timestamp))
            
            # Apply limit if specified (get most recent messages)
            if limit and limit > 0:
                # Get total count first
                total_count = query.count()
                if total_count > limit:
                    # Skip older messages to get the most recent ones
                    offset = total_count - limit
                    query = query.offset(offset)
            
            results = query.all()
            
            # Convert to Message objects
            messages = []
            for db_message in results:
                message = self._db_message_to_pydantic(db_message, include_metadata)
                messages.append(message)
            
            logger.info(f"Retrieved {len(messages)} messages for conversation history in session {session_id}")
            return messages
            
        except SQLAlchemyError as e:
            logger.error(f"Database error retrieving conversation history for session {session_id}: {str(e)}")
            raise MessageRepositoryError(f"Database error: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error retrieving conversation history for session {session_id}: {str(e)}")
            raise MessageRepositoryError(f"Unexpected error: {str(e)}")
    
    def delete_session_messages(self, session_id: str) -> int:
        """
        Delete all messages in a session.
        
        Args:
            session_id: Session identifier
            
        Returns:
            Number of messages deleted
            
        Raises:
            MessageRepositoryError: If deletion fails
        """
        try:
            # Count messages before deletion
            count = self.db_session.query(MessageModel).filter(
                MessageModel.session_id == session_id
            ).count()
            
            # Delete all messages in the session
            self.db_session.query(MessageModel).filter(
                MessageModel.session_id == session_id
            ).delete()
            
            self.db_session.commit()
            
            logger.info(f"Deleted {count} messages from session {session_id}")
            return count
            
        except SQLAlchemyError as e:
            self.db_session.rollback()
            logger.error(f"Database error deleting messages for session {session_id}: {str(e)}")
            raise MessageRepositoryError(f"Database error: {str(e)}")
        except Exception as e:
            self.db_session.rollback()
            logger.error(f"Unexpected error deleting messages for session {session_id}: {str(e)}")
            raise MessageRepositoryError(f"Unexpected error: {str(e)}")
    
    def create_threaded_message(self, message_create: MessageCreate, parent_message_id: Optional[str] = None) -> Message:
        """
        Create a new message with threading support.
        
        Args:
            message_create: Message creation data
            parent_message_id: ID of the parent message (for responses)
            
        Returns:
            Created message with threading information
            
        Raises:
            MessageRepositoryError: If creation fails
            SessionNotFoundError: If session doesn't exist
            MessageNotFoundError: If parent message doesn't exist
        """
        try:
            # Verify session exists
            session_exists = self.db_session.query(SessionModel).filter(
                SessionModel.id == message_create.session_id
            ).first() is not None
            
            if not session_exists:
                raise SessionNotFoundError(f"Session with ID {message_create.session_id} not found")
            
            # Verify parent message exists if provided
            thread_id = None
            if parent_message_id:
                parent_message = self.db_session.query(MessageModel).filter(
                    MessageModel.id == parent_message_id
                ).first()
                
                if not parent_message:
                    raise MessageNotFoundError(f"Parent message with ID {parent_message_id} not found")
                
                # Use parent's thread_id or create new one
                thread_id = parent_message.thread_id or str(uuid.uuid4())
            
            # Convert role string to enum
            role_enum = MessageRole.USER if message_create.role == "user" else MessageRole.ASSISTANT
            
            # Create SQLAlchemy model instance
            db_message = MessageModel(
                session_id=message_create.session_id,
                content=message_create.content,
                role=role_enum,
                message_metadata=message_create.message_metadata or {},
                parent_message_id=parent_message_id,
                thread_id=thread_id
            )
            
            # Add to database
            self.db_session.add(db_message)
            self.db_session.commit()
            self.db_session.refresh(db_message)
            
            logger.info(f"Created threaded message with ID: {db_message.id}, thread_id: {thread_id}")
            
            # Convert to Pydantic model
            return self._db_message_to_pydantic(db_message)
            
        except (SessionNotFoundError, MessageNotFoundError):
            raise
        except IntegrityError as e:
            self.db_session.rollback()
            logger.error(f"Integrity error creating threaded message: {str(e)}")
            raise MessageRepositoryError(f"Failed to create threaded message: {str(e)}")
        except SQLAlchemyError as e:
            self.db_session.rollback()
            logger.error(f"Database error creating threaded message: {str(e)}")
            raise MessageRepositoryError(f"Database error: {str(e)}")
        except Exception as e:
            self.db_session.rollback()
            logger.error(f"Unexpected error creating threaded message: {str(e)}")
            raise MessageRepositoryError(f"Unexpected error: {str(e)}")
    
    def get_message_thread(self, thread_id: str) -> List[Message]:
        """
        Get all messages in a thread, ordered chronologically.
        
        Args:
            thread_id: Thread identifier
            
        Returns:
            List of messages in the thread
            
        Raises:
            MessageRepositoryError: If retrieval fails
        """
        try:
            results = self.db_session.query(MessageModel).filter(
                MessageModel.thread_id == thread_id
            ).order_by(asc(MessageModel.timestamp)).all()
            
            messages = [self._db_message_to_pydantic(db_message) for db_message in results]
            
            logger.info(f"Retrieved {len(messages)} messages for thread {thread_id}")
            return messages
            
        except SQLAlchemyError as e:
            logger.error(f"Database error retrieving thread {thread_id}: {str(e)}")
            raise MessageRepositoryError(f"Database error: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error retrieving thread {thread_id}: {str(e)}")
            raise MessageRepositoryError(f"Unexpected error: {str(e)}")
    
    def get_message_children(self, parent_message_id: str) -> List[Message]:
        """
        Get all direct child messages of a parent message.
        
        Args:
            parent_message_id: Parent message identifier
            
        Returns:
            List of child messages
            
        Raises:
            MessageRepositoryError: If retrieval fails
        """
        try:
            results = self.db_session.query(MessageModel).filter(
                MessageModel.parent_message_id == parent_message_id
            ).order_by(asc(MessageModel.timestamp)).all()
            
            messages = [self._db_message_to_pydantic(db_message) for db_message in results]
            
            logger.info(f"Retrieved {len(messages)} child messages for parent {parent_message_id}")
            return messages
            
        except SQLAlchemyError as e:
            logger.error(f"Database error retrieving children of {parent_message_id}: {str(e)}")
            raise MessageRepositoryError(f"Database error: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error retrieving children of {parent_message_id}: {str(e)}")
            raise MessageRepositoryError(f"Unexpected error: {str(e)}")
    
    def update_message_metrics(self, message_id: str, token_count: Optional[int] = None, 
                              processing_time_ms: Optional[int] = None) -> Message:
        """
        Update message metrics (token count and processing time).
        
        Args:
            message_id: Message identifier
            token_count: Number of tokens in the message
            processing_time_ms: Processing time in milliseconds
            
        Returns:
            Updated message
            
        Raises:
            MessageNotFoundError: If message doesn't exist
            MessageRepositoryError: If update fails
        """
        try:
            db_message = self.db_session.query(MessageModel).filter(
                MessageModel.id == message_id
            ).first()
            
            if not db_message:
                raise MessageNotFoundError(f"Message with ID {message_id} not found")
            
            # Update metrics if provided
            if token_count is not None:
                db_message.token_count = token_count
            
            if processing_time_ms is not None:
                db_message.processing_time_ms = processing_time_ms
            
            self.db_session.commit()
            self.db_session.refresh(db_message)
            
            logger.info(f"Updated metrics for message {message_id}: tokens={token_count}, time={processing_time_ms}ms")
            
            return self._db_message_to_pydantic(db_message)
            
        except MessageNotFoundError:
            raise
        except IntegrityError as e:
            self.db_session.rollback()
            logger.error(f"Integrity error updating message metrics {message_id}: {str(e)}")
            raise MessageRepositoryError(f"Failed to update message metrics: {str(e)}")
        except SQLAlchemyError as e:
            self.db_session.rollback()
            logger.error(f"Database error updating message metrics {message_id}: {str(e)}")
            raise MessageRepositoryError(f"Database error: {str(e)}")
        except Exception as e:
            self.db_session.rollback()
            logger.error(f"Unexpected error updating message metrics {message_id}: {str(e)}")
            raise MessageRepositoryError(f"Unexpected error: {str(e)}")
    
    def get_conversation_threads(self, session_id: str) -> List[Dict[str, Any]]:
        """
        Get all conversation threads in a session with thread summaries.
        
        Args:
            session_id: Session identifier
            
        Returns:
            List of thread summaries with metadata
            
        Raises:
            MessageRepositoryError: If retrieval fails
        """
        try:
            # Get unique thread IDs with message counts and timestamps
            thread_query = self.db_session.query(
                MessageModel.thread_id,
                func.count(MessageModel.id).label('message_count'),
                func.min(MessageModel.timestamp).label('first_message_at'),
                func.max(MessageModel.timestamp).label('last_message_at'),
                func.sum(MessageModel.token_count).label('total_tokens')
            ).filter(
                MessageModel.session_id == session_id,
                MessageModel.thread_id.isnot(None)
            ).group_by(MessageModel.thread_id).all()
            
            threads = []
            for thread_data in thread_query:
                # Get the first message content for preview
                first_message = self.db_session.query(MessageModel).filter(
                    MessageModel.thread_id == thread_data.thread_id,
                    MessageModel.timestamp == thread_data.first_message_at
                ).first()
                
                thread_summary = {
                    'thread_id': thread_data.thread_id,
                    'message_count': thread_data.message_count,
                    'first_message_at': thread_data.first_message_at,
                    'last_message_at': thread_data.last_message_at,
                    'total_tokens': thread_data.total_tokens or 0,
                    'preview': first_message.content[:100] + "..." if first_message and len(first_message.content) > 100 else first_message.content if first_message else ""
                }
                threads.append(thread_summary)
            
            # Sort by last message timestamp (most recent first)
            threads.sort(key=lambda x: x['last_message_at'], reverse=True)
            
            logger.info(f"Retrieved {len(threads)} conversation threads for session {session_id}")
            return threads
            
        except SQLAlchemyError as e:
            logger.error(f"Database error retrieving conversation threads for session {session_id}: {str(e)}")
            raise MessageRepositoryError(f"Database error: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error retrieving conversation threads for session {session_id}: {str(e)}")
            raise MessageRepositoryError(f"Unexpected error: {str(e)}")

    def _db_message_to_pydantic(self, db_message: MessageModel, include_metadata: bool = True) -> Message:
        """
        Convert SQLAlchemy message model to Pydantic model.
        
        Args:
            db_message: SQLAlchemy message instance
            include_metadata: Whether to include metadata
            
        Returns:
            Pydantic Message model
        """
        return Message(
            id=db_message.id,
            session_id=db_message.session_id,
            content=db_message.content,
            role=db_message.role.value,
            timestamp=db_message.timestamp,
            token_count=db_message.token_count,
            processing_time_ms=db_message.processing_time_ms,
            message_metadata=db_message.message_metadata if (include_metadata and db_message.message_metadata) else {},
            parent_message_id=db_message.parent_message_id,
            thread_id=db_message.thread_id
        )