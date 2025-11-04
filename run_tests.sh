#!/bin/bash

# Test Runner Script for ChatGPT Web UI (WSL Ubuntu)
# This script runs all tests and generates coverage reports

echo "🧪 Running ChatGPT Web UI Tests"
echo "================================"

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed"
    exit 1
fi

echo "✅ Python 3 is available"

# Check if pip is available
if ! command -v pip3 &> /dev/null; then
    echo "❌ pip3 is not installed"
    exit 1
fi

echo "✅ pip3 is available"

# Install test dependencies if not already installed
echo "📦 Installing test dependencies..."
pip3 install -r requirements.txt

if [ $? -ne 0 ]; then
    echo "❌ Failed to install dependencies"
    exit 1
fi

echo "✅ Dependencies installed"

# Set PYTHONPATH
export PYTHONPATH="${PYTHONPATH}:$(pwd)"

# Run unit tests
echo "🔬 Running unit tests..."
python3 -m pytest tests/test_models.py tests/test_error_handling.py -v

if [ $? -ne 0 ]; then
    echo "❌ Unit tests failed"
    exit 1
fi

echo "✅ Unit tests passed"

# Run service tests
echo "🔧 Running service tests..."
python3 -m pytest tests/test_chat_service.py -v

if [ $? -ne 0 ]; then
    echo "❌ Service tests failed"
    exit 1
fi

echo "✅ Service tests passed"

# Run API tests
echo "🌐 Running API tests..."
python3 -m pytest tests/test_api_routes.py -v

if [ $? -ne 0 ]; then
    echo "❌ API tests failed"
    exit 1
fi

echo "✅ API tests passed"

# Run Docker tests (non-integration)
echo "🐳 Running Docker configuration tests..."
python3 -m pytest tests/test_docker_setup.py::TestDockerSetup -v

if [ $? -ne 0 ]; then
    echo "❌ Docker configuration tests failed"
    exit 1
fi

echo "✅ Docker configuration tests passed"

# Run all tests with coverage (optional)
if command -v coverage &> /dev/null; then
    echo "📊 Running tests with coverage..."
    coverage run -m pytest tests/ -v --tb=short
    coverage report
    coverage html
    echo "📈 Coverage report generated in htmlcov/"
else
    echo "ℹ️  Coverage not available (install with: pip3 install coverage)"
fi

echo ""
echo "🎉 All tests passed successfully!"
echo ""
echo "📋 Test Summary:"
echo "   ✅ Unit tests (models, error handling)"
echo "   ✅ Service tests (chat service)"
echo "   ✅ API tests (routes, endpoints)"
echo "   ✅ Docker configuration tests"
echo ""
echo "🚀 Your ChatGPT Web UI is ready for deployment!"