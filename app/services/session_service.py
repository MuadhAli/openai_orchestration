"""
Simple service layer for session management.
"""
import logging
from datetime import datetime
from typing import List, Optional
from sqlalchemy.orm import Session as DBSession
from sqlalchemy.exc import SQLAlchemyError

from app.models.session import SessionCreate, SessionUpdate, SessionResponse, SessionListResponse
from app.database.models import Session, Message

logger = logging.getLogger(__name__)


class SessionService:
    """Simple service for session management."""
    
    def __init__(self, db_session: DBSession):
        """Initialize service with database session."""
        self.db_session = db_session
    
    def create_session(self, session_create: SessionCreate) -> SessionResponse:
        """Create a new session."""
        try:
            # Create new session
            session = Session(name=session_create.name)
            
            self.db_session.add(session)
            self.db_session.commit()
            self.db_session.refresh(session)
            
            logger.info(f"Created session: {session.id}")
            return SessionResponse(
                id=session.id,
                name=session.name,
                created_at=session.created_at
            )
            
        except SQLAlchemyError as e:
            self.db_session.rollback()
            logger.error(f"Database error creating session: {str(e)}")
            raise Exception("Failed to create session")
        except Exception as e:
            self.db_session.rollback()
            logger.error(f"Error creating session: {str(e)}")
            raise
    
    def get_session(self, session_id: str) -> Optional[SessionResponse]:
        """Get a session by ID."""
        try:
            session = self.db_session.query(Session).filter(Session.id == session_id).first()
            
            if not session:
                return None
            
            return SessionResponse(
                id=session.id,
                name=session.name,
                created_at=session.created_at
            )
            
        except SQLAlchemyError as e:
            logger.error(f"Database error getting session {session_id}: {str(e)}")
            return None
    
    def list_sessions(self) -> SessionListResponse:
        """List all sessions."""
        try:
            sessions = self.db_session.query(Session).order_by(Session.created_at.desc()).all()
            
            session_responses = [
                SessionResponse(
                    id=session.id,
                    name=session.name,
                    created_at=session.created_at
                )
                for session in sessions
            ]
            
            return SessionListResponse(sessions=session_responses)
            
        except SQLAlchemyError as e:
            logger.error(f"Database error listing sessions: {str(e)}")
            return SessionListResponse(sessions=[])
    
    def update_session(self, session_id: str, session_update: SessionUpdate) -> Optional[SessionResponse]:
        """Update a session."""
        try:
            session = self.db_session.query(Session).filter(Session.id == session_id).first()
            
            if not session:
                return None
            
            if session_update.name:
                session.name = session_update.name
            
            self.db_session.commit()
            self.db_session.refresh(session)
            
            logger.info(f"Updated session: {session.id}")
            return SessionResponse(
                id=session.id,
                name=session.name,
                created_at=session.created_at
            )
            
        except SQLAlchemyError as e:
            self.db_session.rollback()
            logger.error(f"Database error updating session {session_id}: {str(e)}")
            return None
    
    def delete_session(self, session_id: str) -> bool:
        """Delete a session and all its messages."""
        try:
            session = self.db_session.query(Session).filter(Session.id == session_id).first()
            
            if not session:
                return False
            
            # Delete the session (messages will be deleted due to cascade)
            self.db_session.delete(session)
            self.db_session.commit()
            
            logger.info(f"Deleted session: {session_id}")
            return True
            
        except SQLAlchemyError as e:
            self.db_session.rollback()
            logger.error(f"Database error deleting session {session_id}: {str(e)}")
            return False
    
    def get_session_messages(self, session_id: str) -> List[dict]:
        """Get all messages for a session."""
        try:
            messages = (
                self.db_session.query(Message)
                .filter(Message.session_id == session_id)
                .order_by(Message.timestamp.asc())
                .all()
            )
            
            return [
                {
                    "id": msg.id,
                    "content": msg.content,
                    "role": msg.role.value,
                    "timestamp": msg.timestamp
                }
                for msg in messages
            ]
            
        except SQLAlchemyError as e:
            logger.error(f"Database error getting messages for session {session_id}: {str(e)}")
            return []
    
    def create_default_session(self) -> SessionResponse:
        """Create a default session."""
        default_name = f"New Chat {datetime.now().strftime('%Y-%m-%d %H:%M')}"
        session_create = SessionCreate(name=default_name)
        return self.create_session(session_create)