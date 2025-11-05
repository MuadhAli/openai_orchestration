# Database Setup Documentation

## Overview

This document describes the database infrastructure setup for the RAG Chat System, including SQLAlchemy models, configuration, and migration utilities.

## Components

### 1. Database Configuration (`app/database/config.py`)

- **DatabaseConfig**: Main configuration class for database connections
- **Connection Management**: Handles MySQL connection with connection pooling
- **Environment Variables**: Configurable database settings via environment variables
- **Session Management**: SQLAlchemy session factory and dependency injection

### 2. Database Models (`app/database/models.py`)

#### Session Model
- Stores chat session information
- Fields: id, name, created_at, updated_at, session_metadata
- Relationships: One-to-many with messages

#### Message Model  
- Stores individual chat messages
- Fields: id, session_id, content, role, timestamp, token_count, processing_time_ms, message_metadata
- Relationships: Many-to-one with sessions
- Indexes: Optimized for session_id and timestamp queries

#### Embedding Model
- Stores vector embeddings for RAG functionality (fallback storage)
- Fields: id, content, embedding (binary), embedding_metadata, created_at
- Indexes: Optimized for content-based lookups

### 3. Database Migrations (`app/database/migrations.py`)

- **DatabaseMigrator**: Handles schema creation and updates
- **Migration Functions**: Create/drop tables, check table existence
- **Status Reporting**: Get current migration status and table information

### 4. Initialization Scripts

#### `scripts/init_database.py`
- Interactive database initialization
- Supports reset functionality with `--reset` flag
- Validates database connection and schema

#### `scripts/health_check.py`
- Comprehensive system health check
- Validates environment configuration
- Tests database connectivity

#### `scripts/demo_database.py`
- Demonstrates database operations with SQLite
- Shows all CRUD operations and relationships
- Useful for testing without MySQL

## Environment Configuration

Required environment variables (with defaults):

```bash
DB_HOST=localhost          # Database host
DB_PORT=3306              # Database port  
DB_USER=root              # Database username
DB_PASSWORD=              # Database password (empty by default)
DB_NAME=rag_chat_db       # Database name
DB_ECHO=false             # Enable SQL query logging
```

## Installation

1. Install required dependencies:
```bash
pip install -r requirements.txt
```

2. Set up environment variables in `.env` file

3. Initialize the database:
```bash
python scripts/init_database.py
```

## Usage Examples

### Basic Database Operations

```python
from app.database.config import db_config
from app.database.models import Session, Message, MessageRole

# Get database session
session = db_config.get_session()

# Create a chat session
chat_session = Session(name="My Chat")
session.add(chat_session)
session.commit()

# Add a message
message = Message(
    session_id=chat_session.id,
    content="Hello!",
    role=MessageRole.USER
)
session.add(message)
session.commit()

session.close()
```

### Migration Operations

```python
from app.database.migrations import migrate_database, get_migration_status

# Run migration
success = migrate_database()

# Check status
status = get_migration_status()
print(f"Database connected: {status['database_connected']}")
print(f"Tables exist: {status['tables_exist']}")
```

## Testing

The database setup includes comprehensive tests:

- **Unit Tests**: `tests/test_database_setup.py`
- **Integration Tests**: `tests/test_database_integration.py`

Run tests with:
```bash
python -m pytest tests/test_database_setup.py tests/test_database_integration.py -v
```

## Database Schema

### Sessions Table
```sql
CREATE TABLE sessions (
    id VARCHAR(36) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    metadata JSON
);
```

### Messages Table
```sql
CREATE TABLE messages (
    id VARCHAR(36) PRIMARY KEY,
    session_id VARCHAR(36) NOT NULL,
    content TEXT NOT NULL,
    role ENUM('user', 'assistant') NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    token_count INT,
    processing_time_ms INT,
    metadata JSON,
    FOREIGN KEY (session_id) REFERENCES sessions(id) ON DELETE CASCADE,
    INDEX idx_session_timestamp (session_id, timestamp)
);
```

### Embeddings Table
```sql
CREATE TABLE embeddings (
    id VARCHAR(36) PRIMARY KEY,
    content TEXT NOT NULL,
    embedding BLOB NOT NULL,
    metadata JSON,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_content_hash (content(255))
);
```

## Features

- ✅ **Connection Pooling**: Optimized database connections
- ✅ **UUID Generation**: Automatic UUID generation for all records
- ✅ **Timestamp Management**: Automatic timestamp handling
- ✅ **Relationship Management**: Proper foreign key relationships with cascade delete
- ✅ **Migration Support**: Schema creation and validation
- ✅ **Health Monitoring**: Connection and schema health checks
- ✅ **Test Coverage**: Comprehensive unit and integration tests
- ✅ **Environment Configuration**: Flexible configuration via environment variables
- ✅ **Error Handling**: Graceful error handling and logging

## Troubleshooting

### Common Issues

1. **Connection Failed**: Check MySQL service is running and credentials are correct
2. **Missing Tables**: Run `python scripts/init_database.py` to create schema
3. **Permission Denied**: Ensure database user has proper permissions
4. **Import Errors**: Verify all dependencies are installed with `pip install -r requirements.txt`

### Health Check

Run the health check to diagnose issues:
```bash
python scripts/health_check.py
```

### Demo Mode

Test database functionality without MySQL:
```bash
python scripts/demo_database.py
```

This uses SQLite in-memory database to verify all operations work correctly.