"""
API routes for session management.
"""
from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database.config import get_database_session
from app.models.session import SessionCreate, SessionUpdate, SessionResponse, SessionListResponse
from app.services.session_service import SessionService

router = APIRouter(prefix="/api/sessions", tags=["sessions"])


def get_session_service(db: Session = Depends(get_database_session)) -> SessionService:
    """Dependency to get session service."""
    return SessionService(db)


@router.get("/", response_model=SessionListResponse)
async def list_sessions(service: SessionService = Depends(get_session_service)):
    """List all sessions."""
    try:
        return service.list_sessions()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list sessions: {str(e)}")


@router.post("/", response_model=SessionResponse)
async def create_session(
    session_create: SessionCreate,
    service: SessionService = Depends(get_session_service)
):
    """Create a new session."""
    try:
        return service.create_session(session_create)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create session: {str(e)}")


@router.get("/{session_id}", response_model=SessionResponse)
async def get_session(
    session_id: str,
    service: SessionService = Depends(get_session_service)
):
    """Get a session by ID."""
    try:
        session = service.get_session(session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        return session
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get session: {str(e)}")


@router.put("/{session_id}", response_model=SessionResponse)
async def update_session(
    session_id: str,
    session_update: SessionUpdate,
    service: SessionService = Depends(get_session_service)
):
    """Update a session."""
    try:
        session = service.update_session(session_id, session_update)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        return session
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update session: {str(e)}")


@router.delete("/{session_id}")
async def delete_session(
    session_id: str,
    service: SessionService = Depends(get_session_service)
):
    """Delete a session."""
    try:
        success = service.delete_session(session_id)
        if not success:
            raise HTTPException(status_code=404, detail="Session not found")
        return {"message": "Session deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete session: {str(e)}")


@router.get("/{session_id}/messages")
async def get_session_messages(
    session_id: str,
    service: SessionService = Depends(get_session_service)
):
    """Get all messages for a session."""
    try:
        # First check if session exists
        session = service.get_session(session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        messages = service.get_session_messages(session_id)
        return {"messages": messages}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get session messages: {str(e)}")