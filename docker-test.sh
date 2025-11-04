#!/bin/bash

# Docker Test Script for ChatGPT Web UI
# This script helps test the Docker setup

echo "🚀 Testing ChatGPT Web UI Docker Setup"
echo "======================================"

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker and try again."
    exit 1
fi

echo "✅ Docker is running"

# Check if .env file exists
if [ ! -f .env ]; then
    echo "⚠️  .env file not found. Creating example .env file..."
    cat > .env << EOF
OPENAI_API_KEY=your_openai_api_key_here
EOF
    echo "📝 Please edit .env file and add your OpenAI API key"
    exit 1
fi

echo "✅ .env file found"

# Build and start the application
echo "🔨 Building Docker image..."
docker-compose build

if [ $? -ne 0 ]; then
    echo "❌ Docker build failed"
    exit 1
fi

echo "✅ Docker image built successfully"

echo "🚀 Starting application..."
docker-compose up -d

if [ $? -ne 0 ]; then
    echo "❌ Failed to start application"
    exit 1
fi

echo "✅ Application started"

# Wait for application to be ready
echo "⏳ Waiting for application to be ready..."
sleep 10

# Test health endpoint
echo "🔍 Testing health endpoint..."
response=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/api/health)

if [ "$response" = "200" ]; then
    echo "✅ Health check passed"
    echo ""
    echo "🎉 SUCCESS! ChatGPT Web UI is running!"
    echo "📱 Open your browser and go to: http://localhost:8000"
    echo ""
    echo "📋 Useful commands:"
    echo "   View logs: docker-compose logs -f"
    echo "   Stop app:  docker-compose down"
    echo "   Restart:   docker-compose restart"
else
    echo "❌ Health check failed (HTTP $response)"
    echo "📋 Check logs with: docker-compose logs"
    exit 1
fi