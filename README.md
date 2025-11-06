# ChatGPT Web UI with RAG

A modern ChatGPT-like web interface with Retrieval Augmented Generation (RAG) capabilities.

## 🚀 Quick Start

1. **Set up environment:**
   ```bash
   cp .env.example .env
   # Edit .env and add your OpenAI API key
   ```

2. **Start the application:**
   ```bash
   docker compose up --build -d
   ```

3. **Access the application:**
   - Web Interface: http://localhost:8000

## 🎯 Features

- Modern ChatGPT-like interface
- RAG functionality with cross-session knowledge retrieval
- Multiple chat sessions with persistent history
- Fully containerized with Docker
- Mobile responsive design

## 🔧 Commands

```bash
# Start
docker compose up -d

# Stop
docker compose down

# View logs
docker compose logs -f

# Test
python tests/scripts/quick_test.py
```

## 📁 Structure

```
├── app/                    # Main application
├── tests/                  # All tests
├── docker-compose.yml      # Docker configuration
├── Dockerfile             # Container definition
├── requirements.txt       # Dependencies
└── .env                   # Environment variables
```

## ⚙️ Configuration

Edit `.env` file:
```
OPENAI_API_KEY=your_openai_api_key_here
```

---

**Ready to chat?** Open http://localhost:8000 🚀