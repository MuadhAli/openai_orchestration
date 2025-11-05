"""
Database initialization script for RAG chat system.
"""
import logging
from app.database.config import db_config, Base
from app.database.models import Session, Message, MessageEmbedding

logger = logging.getLogger(__name__)

def init_database():
    """Initialize database tables."""
    try:
        # Create engine and tables
        engine = db_config.create_engine()
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created successfully")
        return True
    except Exception as e:
        logger.error(f"Failed to initialize database: {str(e)}")
        return False

def check_database_connection():
    """Check if database connection is working."""
    try:
        from sqlalchemy import text
        engine = db_config.create_engine()
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        logger.info("Database connection successful")
        return True
    except Exception as e:
        logger.error(f"Database connection failed: {str(e)}")
        return False

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    print("Checking database connection...")
    if check_database_connection():
        print("✓ Database connection successful")
        
        print("Initializing database tables...")
        if init_database():
            print("✓ Database initialization complete")
        else:
            print("✗ Database initialization failed")
    else:
        print("✗ Database connection failed")
        print("Please check your database configuration in environment variables:")
        print("- DB_HOST (default: localhost)")
        print("- DB_PORT (default: 3306)")
        print("- DB_USER (default: root)")
        print("- DB_PASSWORD (default: empty)")
        print("- DB_NAME (default: rag_chat_db)")