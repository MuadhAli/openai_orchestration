#!/usr/bin/env python3
"""
Health check script for RAG chat system components.
"""
import sys
import os
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.database.config import check_database_connection
from app.database.migrations import get_migration_status

def check_database_health():
    """Check database connectivity and schema."""
    print("🔍 Checking database health...")
    
    # Test connection
    if not check_database_connection():
        print("❌ Database connection failed")
        return False
    
    print("✅ Database connection successful")
    
    # Check migration status
    status = get_migration_status()
    
    required_tables = ["sessions", "messages", "embeddings"]
    missing_tables = []
    
    for table in required_tables:
        if not status["tables_exist"].get(table, False):
            missing_tables.append(table)
    
    if missing_tables:
        print(f"❌ Missing tables: {', '.join(missing_tables)}")
        return False
    
    print("✅ All required tables exist")
    return True

def check_environment():
    """Check environment configuration."""
    print("🔍 Checking environment configuration...")
    
    required_env_vars = ["OPENAI_API_KEY"]
    optional_env_vars = ["DB_HOST", "DB_PORT", "DB_USER", "DB_PASSWORD", "DB_NAME"]
    
    missing_required = []
    for var in required_env_vars:
        if not os.getenv(var):
            missing_required.append(var)
    
    if missing_required:
        print(f"❌ Missing required environment variables: {', '.join(missing_required)}")
        return False
    
    print("✅ Required environment variables are set")
    
    # Show optional variables status
    print("Optional environment variables:")
    for var in optional_env_vars:
        value = os.getenv(var)
        if value:
            # Mask password
            if "PASSWORD" in var:
                value = "*" * len(value)
            print(f"  {var}: {value}")
        else:
            print(f"  {var}: (using default)")
    
    return True

def main():
    """Main health check function."""
    print("RAG Chat System - Health Check")
    print("=" * 40)
    
    all_healthy = True
    
    # Check environment
    if not check_environment():
        all_healthy = False
    
    print()
    
    # Check database
    if not check_database_health():
        all_healthy = False
    
    print()
    
    if all_healthy:
        print("🎉 All systems healthy!")
        sys.exit(0)
    else:
        print("⚠️  Some issues detected. Please resolve them before running the application.")
        sys.exit(1)

if __name__ == "__main__":
    main()