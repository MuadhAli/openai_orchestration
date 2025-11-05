# Design Document: Simple RAG Chat System

## Overview

A simple RAG-based chat application with session management. Users can create multiple chat sessions, each with its own conversation history. The AI uses both chat history and a knowledge base (via RAG) to generate responses. Everything is stored in MySQL.

## Architecture

### Simple Architecture
```
Frontend (HTML/CSS/JS) ←→ FastAPI Backend ←→ OpenAI API
                                ↓
                          MySQL Database
                          (sessions, messages, documents, embeddings)
```

### Technology Stack
- **Backend**: FastAPI (existing)
- **Database**: MySQL 
- **Vector Search**: Simple cosine similarity in MySQL
- **Embeddings**: OpenAI text-embedding-ada-002
- **Frontend**: Enhanced existing HTML/CSS/JavaScript

## Database Schema

### Sessions Table
```sql
CREATE TABLE sessions (
    id VARCHAR(36) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
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
    FOREIGN KEY (session_id) REFERENCES sessions(id) ON DELETE CASCADE
);
```

### Message Embeddings Table
```sql
CREATE TABLE message_embeddings (
    id VARCHAR(36) PRIMARY KEY,
    message_id VARCHAR(36) NOT NULL,
    session_id VARCHAR(36) NOT NULL,
    content TEXT NOT NULL,
    role ENUM('user', 'assistant') NOT NULL,
    embedding JSON NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (message_id) REFERENCES messages(id) ON DELETE CASCADE,
    FOREIGN KEY (session_id) REFERENCES sessions(id) ON DELETE CASCADE
);
```

## Components

### 1. Session Service
- Create/delete sessions
- List all sessions
- Get session messages

### 2. Chat Service
- Process user messages
- Retrieve relevant context from knowledge base
- Generate AI responses using chat history + RAG context
- Store messages in database

### 3. RAG Service
- Create embeddings for documents
- Search for similar content using cosine similarity
- Return relevant chunks for context

### 4. Database Service
- MySQL connection management
- CRUD operations for all tables
- Simple vector similarity search

## API Endpoints

### Session Management
- `GET /api/sessions` - List all sessions
- `POST /api/sessions` - Create new session
- `DELETE /api/sessions/{id}` - Delete session
- `GET /api/sessions/{id}/messages` - Get session messages

### Chat
- `POST /api/sessions/{id}/chat` - Send message and get AI response

### Conversational Knowledge
- `GET /api/conversations/search?q={query}` - Search past conversations
- `GET /api/conversations/stats` - Get conversation statistics

## Conversational RAG Implementation

### Message Embedding Process
1. When user sends a message → create embedding and store in message_embeddings table
2. When AI responds → create embedding for response and store in message_embeddings table
3. Each message becomes searchable context for future conversations

### Conversational Search
1. User sends new message → create embedding for the query
2. Search all previous message embeddings using cosine similarity
3. Retrieve top 5-10 most relevant past messages (from any session)
4. Filter out messages from current session (to avoid redundancy with chat history)
5. Return relevant conversation snippets as context

### Response Generation
1. Get current session chat history
2. Search for relevant past conversations across all sessions
3. Combine into prompt: "Relevant past conversations: {past_context}\n\nCurrent conversation: {session_history}\n\nUser: {new_message}"
4. Send to OpenAI API
5. Store both user message and AI response with embeddings

## Frontend Updates

### Session Sidebar
- List of sessions with names
- "New Session" button
- Delete session option
- Active session highlighting

### Chat Interface
- Same chat UI but session-aware
- Load messages when switching sessions
- Clear chat area when creating new session

This design keeps everything simple while providing the core functionality you requested: sessions with RAG-based chatting connected to SQL database.