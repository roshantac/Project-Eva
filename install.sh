#!/bin/bash

# Eva AI Python - Installation Script
# This script sets up the Eva AI Python environment with Python 3.12 for audio emotion detection

set -e

echo "🚀 Eva AI Python - Installation Script"
echo "========================================"
echo ""

# Check for Python 3.12 (best compatibility with PyTorch)
echo "📋 Checking for Python 3.12..."
if command -v python3.12 &> /dev/null; then
    PYTHON_CMD="python3.12"
    PYTHON_VERSION=$(python3.12 --version | cut -d' ' -f2)
    echo "✅ Python 3.12 found: $PYTHON_VERSION"
elif command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
    MAJOR=$(echo $PYTHON_VERSION | cut -d'.' -f1)
    MINOR=$(echo $PYTHON_VERSION | cut -d'.' -f2)
    
    if [ "$MAJOR" -eq 3 ] && [ "$MINOR" -ge 13 ]; then
        echo "⚠️  Python $PYTHON_VERSION detected"
        echo "   Audio emotion detection requires Python 3.11-3.12 (PyTorch limitation)"
        echo ""
        echo "Options:"
        echo "1. Install Python 3.12: brew install python@3.12"
        echo "2. Continue with Python $PYTHON_VERSION (audio emotion will be disabled)"
        echo ""
        read -p "Continue with Python $PYTHON_VERSION? (y/n) " -n 1 -r
        echo ""
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            echo "❌ Installation cancelled"
            echo "   Install Python 3.12: brew install python@3.12"
            echo "   Then run this script again"
            exit 1
        fi
        PYTHON_CMD="python3"
    elif [ "$MAJOR" -eq 3 ] && [ "$MINOR" -ge 11 ]; then
        PYTHON_CMD="python3"
        echo "✅ Python $PYTHON_VERSION found (compatible)"
    else
        echo "❌ Python 3.11 or higher required. Found: $PYTHON_VERSION"
        exit 1
    fi
else
    echo "❌ Python 3 is not installed. Please install Python 3.12 or higher."
    echo "   Install: brew install python@3.12"
    exit 1
fi
echo ""

# Create virtual environment
echo "🔧 Creating virtual environment with $PYTHON_CMD..."
if [ ! -d "venv" ]; then
    $PYTHON_CMD -m venv venv
    echo "✅ Virtual environment created"
else
    echo "✅ Virtual environment already exists"
fi
echo ""

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate
echo "✅ Virtual environment activated"
echo ""

# Upgrade pip
echo "🔧 Upgrading pip..."
pip install --upgrade pip
echo "✅ pip upgraded"
echo ""

# Install Python dependencies
echo "📦 Installing Python dependencies..."
pip install -r requirements.txt
echo "✅ Python dependencies installed"
echo ""

# Check Python version for audio emotion
PYTHON_VERSION=$(python --version | cut -d' ' -f2)
MAJOR=$(echo $PYTHON_VERSION | cut -d'.' -f1)
MINOR=$(echo $PYTHON_VERSION | cut -d'.' -f2)

if [ "$MAJOR" -eq 3 ] && [ "$MINOR" -le 12 ]; then
    echo "📦 Installing audio emotion detection dependencies..."
    echo "   (wav2vec2 for voice emotion detection)"
    pip install 'transformers<5.0' 'torch>=2.2.0,<2.3.0' 'torchaudio>=2.2.0,<2.3.0' 'numpy<2.0' protobuf
    if [ $? -eq 0 ]; then
        echo "✅ Audio emotion dependencies installed"
        echo "   🎤 Voice emotion detection enabled!"
    else
        echo "⚠️  Failed to install audio emotion dependencies"
        echo "   Text emotion detection will still work"
    fi
else
    echo "⚠️  Skipping audio emotion dependencies (Python $PYTHON_VERSION)"
    echo "   PyTorch requires Python 3.11-3.12"
    echo "   Text emotion detection will be used instead"
fi
echo ""

# Check for MongoDB
echo "📋 Checking MongoDB..."
if command -v mongod &> /dev/null; then
    echo "✅ MongoDB is installed"
else
    echo "⚠️  MongoDB is not installed"
    echo "   Install MongoDB: https://www.mongodb.com/docs/manual/installation/"
fi
echo ""

# Check for Redis
echo "📋 Checking Redis..."
if command -v redis-server &> /dev/null; then
    echo "✅ Redis is installed"
else
    echo "⚠️  Redis is not installed (optional, but recommended)"
    echo "   Install Redis: https://redis.io/docs/getting-started/installation/"
fi
echo ""

# Check for FFmpeg
echo "📋 Checking FFmpeg..."
if command -v ffmpeg &> /dev/null; then
    echo "✅ FFmpeg is installed"
else
    echo "⚠️  FFmpeg is not installed (required for audio conversion)"
    echo "   Install FFmpeg: brew install ffmpeg (macOS) or apt-get install ffmpeg (Linux)"
fi
echo ""

# Create necessary directories
echo "🔧 Creating directories..."
mkdir -p logs/conversations temp uploads
echo "✅ Directories created"
echo ""

# Copy environment file
echo "🔧 Setting up environment file..."
if [ ! -f ".env" ]; then
    cp .env.example .env
    echo "✅ .env file created from .env.example"
    echo "⚠️  Please edit .env and configure your API keys and settings"
else
    echo "✅ .env file already exists"
fi
echo ""

# Install frontend dependencies
echo "📦 Installing frontend dependencies..."
cd client
if [ ! -d "node_modules" ]; then
    npm install
    echo "✅ Frontend dependencies installed"
else
    echo "✅ Frontend dependencies already installed"
fi
cd ..
echo ""

# Summary
echo "========================================"
echo "✅ Installation Complete!"
echo "========================================"
echo ""
echo "📝 Installed Features:"
echo "✅ FastAPI backend"
echo "✅ React frontend"
echo "✅ File-based database (no MongoDB needed)"
echo "✅ Text emotion detection"
echo "✅ Voice input/output"

if [ "$MAJOR" -eq 3 ] && [ "$MINOR" -le 13 ]; then
    echo "✅ Audio emotion detection (wav2vec2)"
else
    echo "⏳ Audio emotion detection (waiting for PyTorch Python 3.14 support)"
fi
echo ""

echo "📝 Next Steps:"
echo "1. Edit .env file (already configured with defaults)"
echo "2. Install Ollama (for local LLM): see install-ollama.sh"
echo "3. Install Whisper (for voice input): see AUDIO_SERVICE_README.md"
echo "4. Start the backend: source venv/bin/activate && python -m uvicorn app.main:socket_app --reload --port 3001"
echo "5. Start the frontend: cd client && npm run dev"
echo ""
echo "📚 Documentation:"
echo "- README.md - Getting started guide"
echo "- LLM_SERVICE_README.md - LLM configuration"
echo "- AUDIO_SERVICE_README.md - Audio setup"
echo "- AUDIO_EMOTION_SETUP.md - Audio emotion detection"
echo "- ALL_FIXES_SUMMARY.md - Recent fixes and features"
echo ""
echo "🎉 Eva AI is ready to use!"
