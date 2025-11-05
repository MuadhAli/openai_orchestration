#!/usr/bin/env python3
"""
Database initialization script for RAG chat system.
"""
import sys
import os
import logging
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.database.migrations import migrate_database, reset_database, get_migration_status
from app.database.config import check_database_connection

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    """Main function to initialize database."""
    print("RAG Chat System - Database Initialization")
    print("=" * 50)
    
    # Check if reset flag is provided
    reset_flag = "--reset" in sys.argv
    force_flag = "--force" in sys.argv
    
    if reset_flag:
        print("⚠️  WARNING: This will delete all existing data!")
        if not force_flag:
            confirm = input("Are you sure you want to reset the database? (yes/no): ")
            if confirm.lower() != "yes":
                print("Database reset cancelled.")
                return
        
        print("Resetting database...")
        if reset_database():
            print("✅ Database reset successfully!")
        else:
            print("❌ Database reset failed!")
            sys.exit(1)
    else:
        # Check current migration status
        print("Checking current database status...")
        status = get_migration_status()
        
        if not status["database_connected"]:
            print("❌ Cannot connect to database. Please check your configuration.")
            print("Environment variables needed:")
            print("  - DB_HOST (default: localhost)")
            print("  - DB_PORT (default: 3306)")
            print("  - DB_USER (default: root)")
            print("  - DB_PASSWORD (default: empty)")
            print("  - DB_NAME (default: rag_chat_db)")
            sys.exit(1)
        
        print("✅ Database connection successful!")
        
        # Check if tables exist
        tables_exist = status["tables_exist"]
        missing_tables = [table for table, exists in tables_exist.items() if not exists]
        
        if missing_tables:
            print(f"Missing tables: {', '.join(missing_tables)}")
            print("Running database migration...")
            
            if migrate_database():
                print("✅ Database migration completed successfully!")
            else:
                print("❌ Database migration failed!")
                sys.exit(1)
        else:
            print("✅ All required tables already exist!")
        
        # Display table information
        print("\nDatabase Schema Information:")
        print("-" * 30)
        for table_name, info in status["table_info"].items():
            print(f"Table: {table_name}")
            print(f"  Columns: {len(info['columns'])}")
            print(f"  Indexes: {len(info['indexes'])}")
            print(f"  Foreign Keys: {len(info['foreign_keys'])}")
    
    print("\n🎉 Database initialization completed!")
    print("\nNext steps:")
    print("1. Start the application: python main.py")
    print("2. Access the web interface at: http://localhost:8000")

if __name__ == "__main__":
    main()