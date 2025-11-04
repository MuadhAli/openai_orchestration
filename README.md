# ChatGPT Web UI - Developer Guide

A modern, responsive web interface for ChatGPT using FastAPI and OpenAI API. This project provides a clean, ChatGPT-like experience with robust error handling, comprehensive testing, and Docker deployment support.

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- OpenAI API Key
- Docker & Docker Compose (optional)
- WSL Ubuntu (if on Windows)

### 1. Environment Setup

```bash
# Clone or navigate to the project directory
cd chatgpt-web-ui

# Create virtual environment (recommended)
python3 -m venv venv
source venv/bin/activate  # On WSL Ubuntu

# Install dependencies
pip install -r requirements.txt

# Create environment file
cp .env.example .env
# Edit .env and add your OpenAI API key:
# OPENAI_API_KEY=sk-your-api-key-here
```

### 2. Run the Application

**Option A: Direct Python**
```bash
# Run with uvicorn
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# Or run the main file directly
python -m app.main
```

**Option B: Docker (Recommended)**
```bash
# Development mode with hot reload
docker-compose up --build

# Production mode
docker-compose -f docker-compose.prod.yml up --build -d

# Test Docker setup
./docker-test.sh  # Linux/WSL
# or
docker-test.bat   # Windows
```

### 3. Access the Application

- **Web Interface**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/api/health

## 📁 Project Structure

```
chatgpt-web-ui/
├── 📁 app/                     # Main application package
│   ├── 📄 __init__.py         # Package initialization
│   ├── 📄 main.py             # FastAPI application entry point
│   ├── 📄 exceptions.py       # Custom exception classes
│   │
│   ├── 📁 models/             # Pydantic data models
│   │   ├── 📄 __init__.py
│   │   └── 📄 chat.py         # Chat request/response models
│   │
│   ├── 📁 routes/             # API route handlers
│   │   ├── 📄 __init__.py
│   │   └── 📄 chat.py         # Chat API endpoints
│   │
│   ├── 📁 services/           # Business logic layer
│   │   ├── 📄 __init__.py
│   │   └── 📄 chat_service.py # OpenAI integration service
│   │
│   ├── 📁 static/             # Frontend files
│   │   ├── 📄 index.html      # Main web interface
│   │   ├── 📄 style.css       # Styling and animations
│   │   └── 📄 script.js       # Frontend JavaScript logic
│   │
│   └── 📁 utils/              # Utility modules
│       ├── 📄 __init__.py
│       └── 📄 error_handler.py # Error handling utilities
│
├── 📁 tests/                  # Test suite
│   ├── 📄 __init__.py
│   ├── 📄 test_models.py      # Model validation tests
│   ├── 📄 test_chat_service.py # Service layer tests
│   ├── 📄 test_api_routes.py  # API endpoint tests
│   ├── 📄 test_error_handling.py # Error handling tests
│   └── 📄 test_docker_setup.py # Docker configuration tests
│
├── 📁 .kiro/                  # Kiro IDE specifications
│   └── 📁 specs/
│       └── 📁 chatgpt-web-ui/
│           ├── 📄 requirements.md # Project requirements
│           ├── 📄 design.md      # System design document
│           └── 📄 tasks.md       # Implementation tasks
│
├── 📄 requirements.txt        # Python dependencies
├── 📄 Dockerfile            # Docker image configuration
├── 📄 docker-compose.yml    # Development Docker setup
├── 📄 docker-compose.prod.yml # Production Docker setup
├── 📄 .dockerignore         # Docker build exclusions
├── 📄 pytest.ini           # Test configuration
├── 📄 run_tests.sh          # Test runner script (WSL)
├── 📄 docker-test.sh        # Docker test script (Linux)
├── 📄 docker-test.bat       # Docker test script (Windows)
├── 📄 DOCKER.md             # Docker deployment guide
└── 📄 README.md             # This file
```

## 🏗️ Architecture Overview

### Backend Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │   FastAPI       │    │   OpenAI API    │
│   (HTML/CSS/JS) │◄──►│   Backend       │◄──►│   Service       │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                              │
                              ▼
                       ┌─────────────────┐
                       │   In-Memory     │
                       │   Conversation  │
                       │   Storage       │
                       └─────────────────┘
```

### Request Flow

1. **User Input** → Frontend JavaScript captures message
2. **API Request** → POST to `/api/chat` with message data
3. **Validation** → Pydantic models validate request
4. **Service Layer** → ChatService processes message
5. **OpenAI API** → External API call with retry logic
6. **Response** → Formatted response back to frontend
7. **UI Update** → JavaScript updates chat interface

## 📋 File Descriptions

### Core Application Files

#### `app/main.py` - Application Entry Point
- FastAPI application initialization
- CORS middleware configuration
- Static file serving setup
- Global exception handling
- Startup/shutdown event handlers
- Route registration

#### `app/models/chat.py` - Data Models
- **Message**: Individual chat message with validation
- **ChatRequest**: API request structure
- **ChatResponse**: API response structure
- **ConversationHistory**: Conversation management
- **ErrorResponse**: Standardized error format

#### `app/services/chat_service.py` - Business Logic
- OpenAI API integration with retry logic
- Conversation management (create, store, retrieve)
- Message processing and validation
- Health check functionality
- Error handling and logging

#### `app/routes/chat.py` - API Endpoints
- `POST /api/chat` - Send message to AI
- `POST /api/chat/new` - Start new conversation
- `GET /api/health` - Service health check
- Request validation and error handling
- Response formatting

#### `app/exceptions.py` - Custom Exceptions
- Application-specific exception hierarchy
- Error codes for different failure types
- Structured error information

#### `app/utils/error_handler.py` - Error Utilities
- Centralized error handling logic
- OpenAI error conversion
- HTTP exception mapping
- Safe execution wrappers

### Frontend Files

#### `app/static/index.html` - Web Interface
- Semantic HTML structure
- Accessibility features (ARIA labels, keyboard navigation)
- Responsive design elements
- Chat interface components
- Error modal and success toast

#### `app/static/style.css` - Styling
- Modern, ChatGPT-like design
- CSS custom properties for theming
- Responsive breakpoints
- Smooth animations and transitions
- Dark mode support
- Loading and typing indicators

#### `app/static/script.js` - Frontend Logic
- Chat functionality (send/receive messages)
- DOM manipulation and event handling
- API communication with error handling
- Real-time UI updates
- Keyboard shortcuts and UX enhancements
- Local storage for conversation persistence

### Configuration Files

#### `requirements.txt` - Dependencies
```
openai              # OpenAI API client
python-dotenv       # Environment variable management
fastapi             # Web framework
uvicorn[standard]   # ASGI server
pydantic            # Data validation
pytest              # Testing framework
pytest-asyncio     # Async test support
httpx               # HTTP client for tests
pytest-mock        # Mocking utilities
```

#### `Dockerfile` - Container Configuration
- Multi-stage Python build
- Security hardening (non-root user)
- Health check integration
- Production optimizations

#### `docker-compose.yml` - Development Setup
- Hot reload for development
- Port mapping (8000:8000)
- Volume mounting for live updates
- Environment variable support

#### `docker-compose.prod.yml` - Production Setup
- Optimized for production deployment
- No development volumes
- Logging configuration
- Resource constraints

## 🧪 Testing

### Test Structure

- **Unit Tests**: Individual component testing
- **Integration Tests**: API endpoint testing
- **Service Tests**: Business logic testing
- **Docker Tests**: Deployment configuration testing

### Running Tests

```bash
# Run all tests
python -m pytest

# Run specific test file
python -m pytest tests/test_models.py -v

# Run with coverage
coverage run -m pytest
coverage report
coverage html

# Use the test runner script (WSL Ubuntu)
./run_tests.sh
```

### Test Categories

- `tests/test_models.py` - Pydantic model validation
- `tests/test_chat_service.py` - Service layer functionality
- `tests/test_api_routes.py` - API endpoint behavior
- `tests/test_error_handling.py` - Error handling logic
- `tests/test_docker_setup.py` - Docker configuration

## 🔧 Development Workflow

### 1. Setting Up Development Environment

```bash
# Activate virtual environment
source venv/bin/activate

# Install development dependencies
pip install -r requirements.txt

# Set up pre-commit hooks (optional)
pre-commit install
```

### 2. Making Changes

1. **Backend Changes**: Modify files in `app/` directory
2. **Frontend Changes**: Edit files in `app/static/`
3. **Tests**: Add/update tests in `tests/` directory
4. **Documentation**: Update relevant `.md` files

### 3. Testing Changes

```bash
# Run relevant tests
python -m pytest tests/test_your_changes.py -v

# Run full test suite
./run_tests.sh

# Test Docker setup
./docker-test.sh
```

### 4. Running in Development Mode

```bash
# With auto-reload
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Or with Docker
docker-compose up --build
```

## 🚀 Deployment

### Local Development
```bash
uvicorn app.main:app --reload
```

### Docker Development
```bash
docker-compose up --build
```

### Docker Production
```bash
docker-compose -f docker-compose.prod.yml up -d --build
```

### Environment Variables

Create a `.env` file with:
```env
OPENAI_API_KEY=sk-your-openai-api-key-here
```

## 🐛 Troubleshooting

### Common Issues

1. **Import Errors**
   ```bash
   export PYTHONPATH="${PYTHONPATH}:$(pwd)"
   ```

2. **OpenAI API Key Issues**
   - Verify `.env` file exists and contains valid API key
   - Check API key format starts with `sk-`
   - Ensure API key has sufficient credits

3. **Port Already in Use**
   ```bash
   # Find process using port 8000
   lsof -i :8000
   # Kill the process or use different port
   uvicorn app.main:app --port 8001
   ```

4. **Docker Issues**
   ```bash
   # Clean up Docker
   docker-compose down
   docker system prune -f
   docker-compose up --build
   ```

### Debugging

1. **Enable Debug Logging**
   ```python
   import logging
   logging.basicConfig(level=logging.DEBUG)
   ```

2. **Check Health Endpoint**
   ```bash
   curl http://localhost:8000/api/health
   ```

3. **View Docker Logs**
   ```bash
   docker-compose logs -f
   ```

## 📚 API Documentation

Once running, visit:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### Key Endpoints

- `GET /` - Web interface
- `POST /api/chat` - Send message
- `POST /api/chat/new` - New conversation
- `GET /api/health` - Health check

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add/update tests
5. Run the test suite
6. Submit a pull request

## 📄 License

This project is open source and available under the MIT License.

---

**Happy Coding! 🎉**

For more detailed information, check out:
- [Docker Deployment Guide](DOCKER.md)
- [Project Specifications](.kiro/specs/chatgpt-web-ui/)
- [API Documentation](http://localhost:8000/docs) (when running)