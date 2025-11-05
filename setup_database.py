#!/usr/bin/env python3
"""
Database setup script for RAG chat system.
This script helps set up the MySQL database and create necessary tables.
"""
import os
import sys
import logging
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def create_env_file():
    """Create .env file with database configuration."""
    env_path = project_root / ".env"
    
    if env_path.exists():
        print("✓ .env file already exists")
        return
    
    print("Creating .env file with database configuration...")
    
    # Get OpenAI API key if it exists
    openai_key = os.getenv("OPENAI_API_KEY", "")
    
    env_content = f"""# OpenAI API Configuration
OPENAI_API_KEY={openai_key}

# Database Configuration
DB_HOST=localhost
DB_PORT=3306
DB_USER=root
DB_PASSWORD=
DB_NAME=rag_chat_db
DB_ECHO=false
"""
    
    with open(env_path, "w") as f:
        f.write(env_content)
    
    print("✓ .env file created")
    print("Please update the database credentials in .env file if needed")

def setup_database():
    """Set up the database."""
    try:
        from app.database.init_db import check_database_connection, init_database
        
        print("Checking database connection...")
        if check_database_connection():
            print("✓ Database connection successful")
            
            print("Creating database tables...")
            if init_database():
                print("✓ Database setup complete!")
                return True
            else:
                print("✗ Failed to create database tables")
                return False
        else:
            print("✗ Database connection failed")
            print("\nTroubleshooting tips:")
            print("1. Make sure MySQL is running")
            print("2. Check database credentials in .env file")
            print("3. Create the database manually: CREATE DATABASE rag_chat_db;")
            print("4. Grant permissions: GRANT ALL ON rag_chat_db.* TO 'root'@'localhost';")
            return False
            
    except Exception as e:
        print(f"✗ Error during database setup: {e}")
        return False

def main():
    """Main setup function."""
    print("=== RAG Chat System Database Setup ===\n")
    
    # Create .env file
    create_env_file()
    
    # Load environment variables
    try:
        from dotenv import load_dotenv
        load_dotenv()
        print("✓ Environment variables loaded")
    except ImportError:
        print("⚠ python-dotenv not installed, using system environment")
    
    # Setup database
    if setup_database():
        print("\n🎉 Database setup completed successfully!")
        print("You can now run the application with: uvicorn app.main:app --reload")
    else:
        print("\n❌ Database setup failed")
        print("Please check the error messages above and try again")

if __name__ == "__main__":
    main()