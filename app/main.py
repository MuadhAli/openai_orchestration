"""
FastAPI application for ChatGPT-like web UI.
"""
import os
from pathlib import Path
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
import logging

from app.services.chat_service import ChatService

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app instance
app = FastAPI(
    title="ChatGPT Web UI",
    description="A ChatGPT-like web interface using OpenAI API",
    version="1.0.0"
)

# Configure CORS middleware for frontend-backend communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize chat service
chat_service = ChatService()

# Get the directory where this file is located
BASE_DIR = Path(__file__).resolve().parent

# Mount static files
static_path = BASE_DIR / "static"
if static_path.exists():
    app.mount("/static", StaticFiles(directory=str(static_path)), name="static")
    logger.info(f"Static files mounted from: {static_path}")
else:
    logger.warning(f"Static directory not found: {static_path}")

# Include API routes
from app.routes.chat import router as chat_router
app.include_router(chat_router)

@app.get("/")
async def serve_index():
    """Serve the main HTML file."""
    index_path = static_path / "index.html"
    if index_path.exists():
        return FileResponse(str(index_path))
    else:
        raise HTTPException(status_code=404, detail="Index file not found")

@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler for unhandled errors."""
    logger.error(f"Unhandled exception: {str(exc)}")
    return HTTPException(
        status_code=500,
        detail="Internal server error occurred"
    )

@app.on_event("startup")
async def startup_event():
    """Application startup event."""
    logger.info("ChatGPT Web UI application starting up...")
    
    # Perform health check on chat service
    health_status = chat_service.health_check()
    if health_status["status"] == "healthy":
        logger.info("Chat service is healthy and ready")
    else:
        logger.warning(f"Chat service health check failed: {health_status}")

@app.on_event("shutdown")
async def shutdown_event():
    """Application shutdown event."""
    logger.info("ChatGPT Web UI application shutting down...")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )