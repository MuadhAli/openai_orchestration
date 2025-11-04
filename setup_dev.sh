#!/bin/bash

# Developer Setup Script for ChatGPT Web UI (WSL Ubuntu)
# This script sets up the development environment

echo "🚀 Setting up ChatGPT Web UI Development Environment"
echo "=================================================="

# Check if we're in WSL Ubuntu
if [[ ! -f /proc/version ]] || ! grep -q "microsoft" /proc/version 2>/dev/null; then
    echo "⚠️  This script is optimized for WSL Ubuntu"
    echo "   It should work on regular Ubuntu too, but may need adjustments"
fi

# Check Python version
python_version=$(python3 --version 2>&1 | grep -oP '\d+\.\d+' | head -1)
required_version="3.11"

if [[ $(echo "$python_version >= $required_version" | bc -l 2>/dev/null || echo "0") -eq 1 ]]; then
    echo "✅ Python $python_version is installed (>= $required_version required)"
else
    echo "❌ Python $required_version or higher is required"
    echo "   Current version: $python_version"
    echo "   Install with: sudo apt update && sudo apt install python3.11 python3.11-venv python3.11-dev"
    exit 1
fi

# Check if pip is available
if ! command -v pip3 &> /dev/null; then
    echo "❌ pip3 is not installed"
    echo "   Install with: sudo apt install python3-pip"
    exit 1
fi

echo "✅ pip3 is available"

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
    
    if [ $? -ne 0 ]; then
        echo "❌ Failed to create virtual environment"
        echo "   Try: sudo apt install python3-venv"
        exit 1
    fi
    
    echo "✅ Virtual environment created"
else
    echo "✅ Virtual environment already exists"
fi

# Activate virtual environment
echo "🔄 Activating virtual environment..."
source venv/bin/activate

if [ $? -ne 0 ]; then
    echo "❌ Failed to activate virtual environment"
    exit 1
fi

echo "✅ Virtual environment activated"

# Upgrade pip
echo "⬆️  Upgrading pip..."
pip install --upgrade pip

# Install dependencies
echo "📦 Installing dependencies..."
pip install -r requirements.txt

if [ $? -ne 0 ]; then
    echo "❌ Failed to install dependencies"
    exit 1
fi

echo "✅ Dependencies installed successfully"

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "📝 Creating .env file..."
    cat > .env << EOF
# OpenAI API Configuration
OPENAI_API_KEY=your_openai_api_key_here

# Application Configuration
PYTHONPATH=/app
PYTHONUNBUFFERED=1
EOF
    
    echo "⚠️  Please edit .env file and add your OpenAI API key:"
    echo "   OPENAI_API_KEY=sk-your-actual-api-key-here"
    echo ""
else
    echo "✅ .env file already exists"
fi

# Make scripts executable
echo "🔧 Making scripts executable..."
chmod +x run_tests.sh 2>/dev/null || true
chmod +x docker-test.sh 2>/dev/null || true
chmod +x setup_dev.sh 2>/dev/null || true

# Test the installation
echo "🧪 Testing installation..."
python -c "import fastapi, openai, pydantic; print('✅ Core dependencies imported successfully')"

if [ $? -ne 0 ]; then
    echo "❌ Installation test failed"
    exit 1
fi

# Run a quick test
echo "🔍 Running quick test..."
python -m pytest tests/test_models.py::TestMessage::test_message_creation_success -v --tb=short

if [ $? -ne 0 ]; then
    echo "⚠️  Quick test failed, but installation seems OK"
    echo "   You may need to set PYTHONPATH or check your .env file"
else
    echo "✅ Quick test passed"
fi

echo ""
echo "🎉 Development environment setup complete!"
echo ""
echo "📋 Next steps:"
echo "   1. Edit .env file and add your OpenAI API key"
echo "   2. Run the application:"
echo "      source venv/bin/activate"
echo "      uvicorn app.main:app --reload --host 0.0.0.0 --port 8000"
echo "   3. Open http://localhost:8000 in your browser"
echo ""
echo "🔧 Useful commands:"
echo "   • Run tests: ./run_tests.sh"
echo "   • Start dev server: uvicorn app.main:app --reload"
echo "   • Docker setup: docker-compose up --build"
echo "   • Test Docker: ./docker-test.sh"
echo ""
echo "📚 Documentation:"
echo "   • README.md - Complete developer guide"
echo "   • DOCKER.md - Docker deployment guide"
echo "   • http://localhost:8000/docs - API documentation (when running)"
echo ""
echo "Happy coding! 🚀"