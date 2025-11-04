@echo off
REM Docker Test Script for ChatGPT Web UI (Windows)
REM This script helps test the Docker setup

echo 🚀 Testing ChatGPT Web UI Docker Setup
echo ======================================

REM Check if Docker is running
docker info >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Docker is not running. Please start Docker and try again.
    exit /b 1
)

echo ✅ Docker is running

REM Check if .env file exists
if not exist .env (
    echo ⚠️  .env file not found. Creating example .env file...
    echo OPENAI_API_KEY=your_openai_api_key_here > .env
    echo 📝 Please edit .env file and add your OpenAI API key
    exit /b 1
)

echo ✅ .env file found

REM Build and start the application
echo 🔨 Building Docker image...
docker-compose build

if %errorlevel% neq 0 (
    echo ❌ Docker build failed
    exit /b 1
)

echo ✅ Docker image built successfully

echo 🚀 Starting application...
docker-compose up -d

if %errorlevel% neq 0 (
    echo ❌ Failed to start application
    exit /b 1
)

echo ✅ Application started

REM Wait for application to be ready
echo ⏳ Waiting for application to be ready...
timeout /t 10 /nobreak >nul

REM Test health endpoint
echo 🔍 Testing health endpoint...
curl -s -o nul -w "%%{http_code}" http://localhost:8000/api/health > temp_response.txt
set /p response=<temp_response.txt
del temp_response.txt

if "%response%"=="200" (
    echo ✅ Health check passed
    echo.
    echo 🎉 SUCCESS! ChatGPT Web UI is running!
    echo 📱 Open your browser and go to: http://localhost:8000
    echo.
    echo 📋 Useful commands:
    echo    View logs: docker-compose logs -f
    echo    Stop app:  docker-compose down
    echo    Restart:   docker-compose restart
) else (
    echo ❌ Health check failed ^(HTTP %response%^)
    echo 📋 Check logs with: docker-compose logs
    exit /b 1
)