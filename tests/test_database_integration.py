"""
Integration tests for database setup with SQLite.
"""
import pytest
import tempfile
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database.config import Base
from app.database.models import Session, Message, Embedding, MessageRole

class TestDatabaseIntegration:
    """Test database operations with SQLite."""
    
    @pytest.fixture
    def sqlite_engine(self):
        """Create an in-memory SQLite engine for testing."""
        engine = create_engine("sqlite:///:memory:", echo=False)
        Base.metadata.create_all(bind=engine)
        return engine
    
    @pytest.fixture
    def db_session(self, sqlite_engine):
        """Create a database session for testing."""
        SessionLocal = sessionmaker(bind=sqlite_engine)
        session = SessionLocal()
        yield session
        session.close()
    
    def test_create_session(self, db_session):
        """Test creating and retrieving a session."""
        # Create a session
        session = Session(name="Test Session")
        db_session.add(session)
        db_session.commit()
        
        # Retrieve the session
        retrieved_session = db_session.query(Session).filter_by(name="Test Session").first()
        
        assert retrieved_session is not None
        assert retrieved_session.name == "Test Session"
        assert retrieved_session.id is not None
        assert retrieved_session.created_at is not None
    
    def test_create_message(self, db_session):
        """Test creating and retrieving a message."""
        # Create a session first
        session = Session(name="Test Session")
        db_session.add(session)
        db_session.commit()
        
        # Create a message
        message = Message(
            session_id=session.id,
            content="Hello, world!",
            role=MessageRole.USER
        )
        db_session.add(message)
        db_session.commit()
        
        # Retrieve the message
        retrieved_message = db_session.query(Message).filter_by(content="Hello, world!").first()
        
        assert retrieved_message is not None
        assert retrieved_message.content == "Hello, world!"
        assert retrieved_message.role == MessageRole.USER
        assert retrieved_message.session_id == session.id
    
    def test_session_message_relationship(self, db_session):
        """Test the relationship between sessions and messages."""
        # Create a session
        session = Session(name="Test Session")
        db_session.add(session)
        db_session.commit()
        
        # Create multiple messages
        message1 = Message(
            session_id=session.id,
            content="First message",
            role=MessageRole.USER
        )
        message2 = Message(
            session_id=session.id,
            content="Second message",
            role=MessageRole.ASSISTANT
        )
        
        db_session.add_all([message1, message2])
        db_session.commit()
        
        # Test relationship
        retrieved_session = db_session.query(Session).filter_by(id=session.id).first()
        assert len(retrieved_session.messages) == 2
        
        # Test messages are ordered by timestamp
        messages = sorted(retrieved_session.messages, key=lambda m: m.timestamp)
        assert messages[0].content == "First message"
        assert messages[1].content == "Second message"
    
    def test_create_embedding(self, db_session):
        """Test creating and retrieving an embedding."""
        # Create an embedding
        embedding = Embedding(
            content="Test document content",
            embedding=b"fake_embedding_data",
            embedding_metadata={"source": "test"}
        )
        db_session.add(embedding)
        db_session.commit()
        
        # Retrieve the embedding
        retrieved_embedding = db_session.query(Embedding).filter_by(content="Test document content").first()
        
        assert retrieved_embedding is not None
        assert retrieved_embedding.content == "Test document content"
        assert retrieved_embedding.embedding == b"fake_embedding_data"
        assert retrieved_embedding.embedding_metadata == {"source": "test"}
    
    def test_cascade_delete(self, db_session):
        """Test that deleting a session cascades to messages."""
        # Create a session with messages
        session = Session(name="Test Session")
        db_session.add(session)
        db_session.commit()
        
        message = Message(
            session_id=session.id,
            content="Test message",
            role=MessageRole.USER
        )
        db_session.add(message)
        db_session.commit()
        
        # Verify message exists
        assert db_session.query(Message).count() == 1
        
        # Delete session
        db_session.delete(session)
        db_session.commit()
        
        # Verify message was also deleted due to cascade
        assert db_session.query(Message).count() == 0
        assert db_session.query(Session).count() == 0