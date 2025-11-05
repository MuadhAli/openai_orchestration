"""
Repository for session data access operations.
"""
import logging
from datetime import datetime
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session as DBSession
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from sqlalchemy import func, desc

from app.database.models import Session as SessionModel, Message as MessageModel
from app.models.session import Session, SessionCreate, SessionUpdate, SessionSummary

logger = logging.getLogger(__name__)


class SessionRepositoryError(Exception):
    """Base exception for session repository operations."""
    pass


class SessionNotFoundError(SessionRepositoryError):
    """Exception raised when a session is not found."""
    pass


class SessionRepository:
    """Repository for session CRUD operations."""
    
    def __init__(self, db_session: DBSession):
        """Initialize repository with database session."""
        self.db_session = db_session
    
    def create_session(self, session_create: SessionCreate) -> Session:
        """
        Create a new session in the database.
        
        Args:
            session_create: Session creation data
            
        Returns:
            Created session
            
        Raises:
            SessionRepositoryError: If creation fails
        """
        try:
            # Create SQLAlchemy model instance
            db_session = SessionModel(
                name=session_create.name,
                session_metadata=session_create.session_metadata or {}
            )
            
            # Add to database
            self.db_session.add(db_session)
            self.db_session.commit()
            self.db_session.refresh(db_session)
            
            logger.info(f"Created session with ID: {db_session.id}")
            
            # Convert to Pydantic model
            return self._db_session_to_pydantic(db_session)
            
        except IntegrityError as e:
            self.db_session.rollback()
            logger.error(f"Integrity error creating session: {str(e)}")
            raise SessionRepositoryError(f"Failed to create session: {str(e)}")
        except SQLAlchemyError as e:
            self.db_session.rollback()
            logger.error(f"Database error creating session: {str(e)}")
            raise SessionRepositoryError(f"Database error: {str(e)}")
        except Exception as e:
            self.db_session.rollback()
            logger.error(f"Unexpected error creating session: {str(e)}")
            raise SessionRepositoryError(f"Unexpected error: {str(e)}")
    
    def get_session_by_id(self, session_id: str) -> Session:
        """
        Get a session by its ID.
        
        Args:
            session_id: Session identifier
            
        Returns:
            Session data
            
        Raises:
            SessionNotFoundError: If session doesn't exist
            SessionRepositoryError: If retrieval fails
        """
        try:
            db_session = self.db_session.query(SessionModel).filter(
                SessionModel.id == session_id
            ).first()
            
            if not db_session:
                raise SessionNotFoundError(f"Session with ID {session_id} not found")
            
            return self._db_session_to_pydantic(db_session)
            
        except SessionNotFoundError:
            raise
        except SQLAlchemyError as e:
            logger.error(f"Database error retrieving session {session_id}: {str(e)}")
            raise SessionRepositoryError(f"Database error: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error retrieving session {session_id}: {str(e)}")
            raise SessionRepositoryError(f"Unexpected error: {str(e)}")
    
    def update_session(self, session_id: str, session_update: SessionUpdate) -> Session:
        """
        Update an existing session.
        
        Args:
            session_id: Session identifier
            session_update: Update data
            
        Returns:
            Updated session
            
        Raises:
            SessionNotFoundError: If session doesn't exist
            SessionRepositoryError: If update fails
        """
        try:
            db_session = self.db_session.query(SessionModel).filter(
                SessionModel.id == session_id
            ).first()
            
            if not db_session:
                raise SessionNotFoundError(f"Session with ID {session_id} not found")
            
            # Update fields if provided
            if session_update.name is not None:
                db_session.name = session_update.name
            
            if session_update.session_metadata is not None:
                db_session.session_metadata = session_update.session_metadata
            
            # Update timestamp
            db_session.updated_at = datetime.now()
            
            self.db_session.commit()
            self.db_session.refresh(db_session)
            
            logger.info(f"Updated session with ID: {session_id}")
            
            return self._db_session_to_pydantic(db_session)
            
        except SessionNotFoundError:
            raise
        except IntegrityError as e:
            self.db_session.rollback()
            logger.error(f"Integrity error updating session {session_id}: {str(e)}")
            raise SessionRepositoryError(f"Failed to update session: {str(e)}")
        except SQLAlchemyError as e:
            self.db_session.rollback()
            logger.error(f"Database error updating session {session_id}: {str(e)}")
            raise SessionRepositoryError(f"Database error: {str(e)}")
        except Exception as e:
            self.db_session.rollback()
            logger.error(f"Unexpected error updating session {session_id}: {str(e)}")
            raise SessionRepositoryError(f"Unexpected error: {str(e)}")
    
    def delete_session(self, session_id: str) -> bool:
        """
        Delete a session and all its messages.
        
        Args:
            session_id: Session identifier
            
        Returns:
            True if deleted successfully
            
        Raises:
            SessionNotFoundError: If session doesn't exist
            SessionRepositoryError: If deletion fails
        """
        try:
            db_session = self.db_session.query(SessionModel).filter(
                SessionModel.id == session_id
            ).first()
            
            if not db_session:
                raise SessionNotFoundError(f"Session with ID {session_id} not found")
            
            # Delete session (messages will be cascade deleted)
            self.db_session.delete(db_session)
            self.db_session.commit()
            
            logger.info(f"Deleted session with ID: {session_id}")
            return True
            
        except SessionNotFoundError:
            raise
        except SQLAlchemyError as e:
            self.db_session.rollback()
            logger.error(f"Database error deleting session {session_id}: {str(e)}")
            raise SessionRepositoryError(f"Database error: {str(e)}")
        except Exception as e:
            self.db_session.rollback()
            logger.error(f"Unexpected error deleting session {session_id}: {str(e)}")
            raise SessionRepositoryError(f"Unexpected error: {str(e)}")
    
    def list_sessions(
        self, 
        page: int = 1, 
        page_size: int = 50,
        order_by: str = "updated_at",
        order_desc: bool = True
    ) -> List[SessionSummary]:
        """
        List sessions with pagination and ordering.
        
        Args:
            page: Page number (1-based)
            page_size: Number of sessions per page
            order_by: Field to order by (created_at, updated_at, name)
            order_desc: Whether to order in descending order
            
        Returns:
            List of session summaries
            
        Raises:
            SessionRepositoryError: If listing fails
        """
        try:
            # Validate parameters
            if page < 1:
                raise ValueError("Page must be greater than 0")
            if page_size < 1 or page_size > 100:
                raise ValueError("Page size must be between 1 and 100")
            
            # Build query with message count
            query = self.db_session.query(
                SessionModel,
                func.count(MessageModel.id).label('message_count'),
                func.max(MessageModel.timestamp).label('last_message_at')
            ).outerjoin(MessageModel).group_by(SessionModel.id)
            
            # Apply ordering
            order_field = getattr(SessionModel, order_by, SessionModel.updated_at)
            if order_desc:
                query = query.order_by(desc(order_field))
            else:
                query = query.order_by(order_field)
            
            # Apply pagination
            offset = (page - 1) * page_size
            results = query.offset(offset).limit(page_size).all()
            
            # Convert to SessionSummary objects
            summaries = []
            for db_session, message_count, last_message_at in results:
                summary = SessionSummary(
                    id=db_session.id,
                    name=db_session.name,
                    created_at=db_session.created_at,
                    updated_at=db_session.updated_at,
                    message_count=message_count or 0,
                    last_message_at=last_message_at
                )
                summaries.append(summary)
            
            logger.info(f"Retrieved {len(summaries)} sessions (page {page})")
            return summaries
            
        except ValueError as e:
            logger.error(f"Invalid parameters for list_sessions: {str(e)}")
            raise SessionRepositoryError(f"Invalid parameters: {str(e)}")
        except SQLAlchemyError as e:
            logger.error(f"Database error listing sessions: {str(e)}")
            raise SessionRepositoryError(f"Database error: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error listing sessions: {str(e)}")
            raise SessionRepositoryError(f"Unexpected error: {str(e)}")
    
    def get_session_count(self) -> int:
        """
        Get total number of sessions.
        
        Returns:
            Total session count
            
        Raises:
            SessionRepositoryError: If count fails
        """
        try:
            count = self.db_session.query(SessionModel).count()
            return count
        except SQLAlchemyError as e:
            logger.error(f"Database error counting sessions: {str(e)}")
            raise SessionRepositoryError(f"Database error: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error counting sessions: {str(e)}")
            raise SessionRepositoryError(f"Unexpected error: {str(e)}")
    
    def session_exists(self, session_id: str) -> bool:
        """
        Check if a session exists.
        
        Args:
            session_id: Session identifier
            
        Returns:
            True if session exists
            
        Raises:
            SessionRepositoryError: If check fails
        """
        try:
            exists = self.db_session.query(SessionModel).filter(
                SessionModel.id == session_id
            ).first() is not None
            return exists
        except SQLAlchemyError as e:
            logger.error(f"Database error checking session existence: {str(e)}")
            raise SessionRepositoryError(f"Database error: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error checking session existence: {str(e)}")
            raise SessionRepositoryError(f"Unexpected error: {str(e)}")
    
    def get_sessions_by_name_pattern(self, name_pattern: str) -> List[SessionSummary]:
        """
        Get sessions matching a name pattern.
        
        Args:
            name_pattern: Pattern to match (supports SQL LIKE syntax)
            
        Returns:
            List of matching session summaries
            
        Raises:
            SessionRepositoryError: If search fails
        """
        try:
            query = self.db_session.query(
                SessionModel,
                func.count(MessageModel.id).label('message_count'),
                func.max(MessageModel.timestamp).label('last_message_at')
            ).outerjoin(MessageModel).filter(
                SessionModel.name.like(f"%{name_pattern}%")
            ).group_by(SessionModel.id).order_by(desc(SessionModel.updated_at))
            
            results = query.all()
            
            summaries = []
            for db_session, message_count, last_message_at in results:
                summary = SessionSummary(
                    id=db_session.id,
                    name=db_session.name,
                    created_at=db_session.created_at,
                    updated_at=db_session.updated_at,
                    message_count=message_count or 0,
                    last_message_at=last_message_at
                )
                summaries.append(summary)
            
            logger.info(f"Found {len(summaries)} sessions matching pattern: {name_pattern}")
            return summaries
            
        except SQLAlchemyError as e:
            logger.error(f"Database error searching sessions: {str(e)}")
            raise SessionRepositoryError(f"Database error: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error searching sessions: {str(e)}")
            raise SessionRepositoryError(f"Unexpected error: {str(e)}")
    
    def _db_session_to_pydantic(self, db_session: SessionModel) -> Session:
        """
        Convert SQLAlchemy session model to Pydantic model.
        
        Args:
            db_session: SQLAlchemy session instance
            
        Returns:
            Pydantic Session model
        """
        # Get message count for this session
        message_count = self.db_session.query(MessageModel).filter(
            MessageModel.session_id == db_session.id
        ).count()
        
        return Session(
            id=db_session.id,
            name=db_session.name,
            created_at=db_session.created_at,
            updated_at=db_session.updated_at,
            session_metadata=db_session.session_metadata or {},
            message_count=message_count
        )