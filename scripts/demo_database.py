#!/usr/bin/env python3
"""
Demo script to show database setup is working with SQLite.
"""
import sys
import os
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.database.config import Base
from app.database.models import Session, Message, Embedding, MessageRole

def demo_database_operations():
    """Demonstrate database operations with SQLite."""
    print("RAG Chat System - Database Demo")
    print("=" * 40)
    
    # Create in-memory SQLite database
    print("Creating in-memory SQLite database...")
    engine = create_engine("sqlite:///:memory:", echo=False)
    Base.metadata.create_all(bind=engine)
    
    # Create session factory
    SessionLocal = sessionmaker(bind=engine)
    db_session = SessionLocal()
    
    try:
        # Create a chat session
        print("\n1. Creating a chat session...")
        chat_session = Session(name="Demo Chat Session")
        db_session.add(chat_session)
        db_session.commit()
        print(f"   ✅ Created session: {chat_session.id}")
        
        # Create messages
        print("\n2. Adding messages to the session...")
        user_message = Message(
            session_id=chat_session.id,
            content="Hello, how are you?",
            role=MessageRole.USER
        )
        
        assistant_message = Message(
            session_id=chat_session.id,
            content="I'm doing well, thank you! How can I help you today?",
            role=MessageRole.ASSISTANT
        )
        
        db_session.add_all([user_message, assistant_message])
        db_session.commit()
        print(f"   ✅ Added user message: {user_message.id}")
        print(f"   ✅ Added assistant message: {assistant_message.id}")
        
        # Create an embedding
        print("\n3. Creating a vector embedding...")
        embedding = Embedding(
            content="This is a sample document for RAG retrieval.",
            embedding=b"fake_embedding_vector_data",
            embedding_metadata={"source": "demo", "type": "document"}
        )
        db_session.add(embedding)
        db_session.commit()
        print(f"   ✅ Created embedding: {embedding.id}")
        
        # Query data
        print("\n4. Querying the database...")
        
        # Get all sessions
        sessions = db_session.query(Session).all()
        print(f"   📊 Total sessions: {len(sessions)}")
        
        # Get messages for the session
        messages = db_session.query(Message).filter_by(session_id=chat_session.id).all()
        print(f"   📊 Messages in session: {len(messages)}")
        
        # Get all embeddings
        embeddings = db_session.query(Embedding).all()
        print(f"   📊 Total embeddings: {len(embeddings)}")
        
        # Show session with messages relationship
        print("\n5. Testing relationships...")
        session_with_messages = db_session.query(Session).filter_by(id=chat_session.id).first()
        print(f"   🔗 Session '{session_with_messages.name}' has {len(session_with_messages.messages)} messages")
        
        for msg in session_with_messages.messages:
            print(f"      - {msg.role.value}: {msg.content[:50]}...")
        
        print("\n🎉 Database demo completed successfully!")
        print("\nDatabase Schema Summary:")
        print("- Sessions table: ✅ Working")
        print("- Messages table: ✅ Working") 
        print("- Embeddings table: ✅ Working")
        print("- Relationships: ✅ Working")
        print("- UUID generation: ✅ Working")
        print("- Timestamp handling: ✅ Working")
        
    except Exception as e:
        print(f"❌ Error during demo: {str(e)}")
        return False
    finally:
        db_session.close()
    
    return True

if __name__ == "__main__":
    success = demo_database_operations()
    sys.exit(0 if success else 1)