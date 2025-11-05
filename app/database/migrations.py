"""
Database migration utilities for RAG chat system.
"""
import logging
from sqlalchemy import text, inspect
from sqlalchemy.exc import SQLAlchemyError

from app.database.config import db_config, Base
from app.database.models import Session, Message, Embedding

logger = logging.getLogger(__name__)

class DatabaseMigrator:
    """Handles database migrations and schema updates."""
    
    def __init__(self):
        self.engine = db_config.create_engine()
    
    def create_database_if_not_exists(self, database_name: str = None) -> bool:
        """Create database if it doesn't exist."""
        if database_name is None:
            # Extract database name from URL
            url_parts = self.engine.url.database
            database_name = url_parts
        
        try:
            # Connect without specifying database
            temp_url = str(self.engine.url).replace(f"/{database_name}", "")
            temp_engine = db_config.create_engine.__class__(temp_url)
            
            with temp_engine.connect() as connection:
                # Check if database exists
                result = connection.execute(
                    text(f"SELECT SCHEMA_NAME FROM INFORMATION_SCHEMA.SCHEMATA WHERE SCHEMA_NAME = '{database_name}'")
                )
                
                if not result.fetchone():
                    # Create database
                    connection.execute(text(f"CREATE DATABASE {database_name}"))
                    connection.commit()
                    logger.info(f"Database '{database_name}' created successfully")
                else:
                    logger.info(f"Database '{database_name}' already exists")
            
            temp_engine.dispose()
            return True
            
        except SQLAlchemyError as e:
            logger.error(f"Failed to create database: {str(e)}")
            return False
    
    def create_tables(self) -> bool:
        """Create all tables defined in models."""
        try:
            Base.metadata.create_all(bind=self.engine)
            logger.info("All database tables created successfully")
            return True
        except SQLAlchemyError as e:
            logger.error(f"Failed to create tables: {str(e)}")
            return False
    
    def drop_tables(self) -> bool:
        """Drop all tables (use with caution)."""
        try:
            Base.metadata.drop_all(bind=self.engine)
            logger.info("All database tables dropped successfully")
            return True
        except SQLAlchemyError as e:
            logger.error(f"Failed to drop tables: {str(e)}")
            return False
    
    def check_table_exists(self, table_name: str) -> bool:
        """Check if a specific table exists."""
        try:
            inspector = inspect(self.engine)
            tables = inspector.get_table_names()
            return table_name in tables
        except SQLAlchemyError as e:
            logger.error(f"Failed to check table existence: {str(e)}")
            return False
    
    def get_table_info(self) -> dict:
        """Get information about existing tables."""
        try:
            inspector = inspect(self.engine)
            tables = inspector.get_table_names()
            
            table_info = {}
            for table in tables:
                columns = inspector.get_columns(table)
                indexes = inspector.get_indexes(table)
                foreign_keys = inspector.get_foreign_keys(table)
                
                table_info[table] = {
                    "columns": [col["name"] for col in columns],
                    "indexes": [idx["name"] for idx in indexes],
                    "foreign_keys": [fk["name"] for fk in foreign_keys]
                }
            
            return table_info
        except SQLAlchemyError as e:
            logger.error(f"Failed to get table info: {str(e)}")
            return {}
    
    def run_migration(self) -> bool:
        """Run complete migration process."""
        logger.info("Starting database migration...")
        
        # Step 1: Create database if needed
        if not self.create_database_if_not_exists():
            return False
        
        # Step 2: Create tables
        if not self.create_tables():
            return False
        
        # Step 3: Verify tables were created
        required_tables = ["sessions", "messages", "embeddings"]
        for table in required_tables:
            if not self.check_table_exists(table):
                logger.error(f"Required table '{table}' was not created")
                return False
        
        logger.info("Database migration completed successfully")
        return True
    
    def reset_database(self) -> bool:
        """Reset database by dropping and recreating all tables."""
        logger.warning("Resetting database - all data will be lost!")
        
        if not self.drop_tables():
            return False
        
        return self.run_migration()

def migrate_database() -> bool:
    """Convenience function to run database migration."""
    migrator = DatabaseMigrator()
    return migrator.run_migration()

def reset_database() -> bool:
    """Convenience function to reset database."""
    migrator = DatabaseMigrator()
    return migrator.reset_database()

def get_migration_status() -> dict:
    """Get current migration status."""
    migrator = DatabaseMigrator()
    
    status = {
        "database_connected": False,
        "tables_exist": {},
        "table_info": {}
    }
    
    try:
        # Check database connection
        with migrator.engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        status["database_connected"] = True
        
        # Check required tables
        required_tables = ["sessions", "messages", "embeddings"]
        for table in required_tables:
            status["tables_exist"][table] = migrator.check_table_exists(table)
        
        # Get table information
        status["table_info"] = migrator.get_table_info()
        
    except Exception as e:
        logger.error(f"Failed to get migration status: {str(e)}")
    
    return status