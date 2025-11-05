"""
Database configuration and connection management.
"""
import os
from typing import Optional
from sqlalchemy import create_engine, Engine
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import QueuePool
import logging

logger = logging.getLogger(__name__)

# SQLAlchemy base class for models
Base = declarative_base()

class DatabaseConfig:
    """Database configuration class."""
    
    def __init__(self):
        self.database_url = self._build_database_url()
        self.engine: Optional[Engine] = None
        self.SessionLocal: Optional[sessionmaker] = None
    
    def _build_database_url(self) -> str:
        """Build database URL from environment variables."""
        # Default values for development
        db_host = os.getenv("DB_HOST", "localhost")
        db_port = os.getenv("DB_PORT", "3306")
        db_user = os.getenv("DB_USER", "root")
        db_password = os.getenv("DB_PASSWORD", "")
        db_name = os.getenv("DB_NAME", "rag_chat_db")
        
        # Build MySQL connection URL
        if db_password:
            url = f"mysql+pymysql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"
        else:
            url = f"mysql+pymysql://{db_user}@{db_host}:{db_port}/{db_name}"
        
        logger.info(f"Database URL configured: mysql+pymysql://{db_user}@{db_host}:{db_port}/{db_name}")
        return url
    
    def create_engine(self) -> Engine:
        """Create SQLAlchemy engine with connection pooling."""
        if self.engine is None:
            self.engine = create_engine(
                self.database_url,
                poolclass=QueuePool,
                pool_size=10,
                max_overflow=20,
                pool_pre_ping=True,
                pool_recycle=3600,
                echo=os.getenv("DB_ECHO", "false").lower() == "true"
            )
            logger.info("Database engine created successfully")
        return self.engine
    
    def create_session_factory(self) -> sessionmaker:
        """Create session factory for database operations."""
        if self.SessionLocal is None:
            engine = self.create_engine()
            self.SessionLocal = sessionmaker(
                autocommit=False,
                autoflush=False,
                bind=engine
            )
            logger.info("Database session factory created")
        return self.SessionLocal
    
    def get_session(self) -> Session:
        """Get a database session."""
        SessionLocal = self.create_session_factory()
        return SessionLocal()
    
    def close_engine(self):
        """Close database engine and connections."""
        if self.engine:
            self.engine.dispose()
            logger.info("Database engine closed")

# Global database configuration instance
db_config = DatabaseConfig()

def get_database_session():
    """Dependency function to get database session."""
    session = db_config.get_session()
    try:
        yield session
    finally:
        session.close()

def init_database():
    """Initialize database tables."""
    try:
        engine = db_config.create_engine()
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables initialized successfully")
        return True
    except Exception as e:
        logger.error(f"Failed to initialize database: {str(e)}")
        return False

def check_database_connection() -> bool:
    """Check if database connection is working."""
    try:
        engine = db_config.create_engine()
        with engine.connect() as connection:
            connection.execute("SELECT 1")
        logger.info("Database connection check successful")
        return True
    except Exception as e:
        logger.error(f"Database connection check failed: {str(e)}")
        return False