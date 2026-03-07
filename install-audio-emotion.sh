#!/bin/bash

# Eva AI - Audio Emotion Detection Setup
# This script installs Python 3.12 and audio emotion detection dependencies

set -e

echo "🎤 Eva AI - Audio Emotion Detection Setup"
echo "=========================================="
echo ""

# Check current Python version
CURRENT_PYTHON=$(python3 --version 2>&1 | cut -d' ' -f2)
CURRENT_MAJOR=$(echo $CURRENT_PYTHON | cut -d'.' -f1)
CURRENT_MINOR=$(echo $CURRENT_PYTHON | cut -d'.' -f2)

echo "Current Python version: $CURRENT_PYTHON"
echo ""

if [ "$CURRENT_MAJOR" -eq 3 ] && [ "$CURRENT_MINOR" -ge 13 ]; then
    echo "⚠️  Python 3.13+ detected - PyTorch has limited support"
    echo "   Installing Python 3.12 for audio emotion detection..."
    echo ""
    
    # Check if Python 3.12 is already installed
    if command -v python3.12 &> /dev/null; then
        echo "✅ Python 3.12 already installed"
    else
        echo "📦 Installing Python 3.12..."
        if command -v brew &> /dev/null; then
            brew install python@3.12
            echo "✅ Python 3.12 installed via Homebrew"
        else
            echo "❌ Homebrew not found"
            echo "   Install Homebrew: /bin/bash -c \"\$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)\""
            echo "   Then run: brew install python@3.12"
            exit 1
        fi
    fi
    echo ""
    
    # Create Python 3.12 virtual environment
    echo "🔧 Creating Python 3.12 virtual environment..."
    if [ -d "venv-py312" ]; then
        echo "⚠️  venv-py312 already exists"
        read -p "Remove and recreate? (y/n) " -n 1 -r
        echo ""
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            rm -rf venv-py312
            echo "✅ Removed old venv-py312"
        else
            echo "Using existing venv-py312"
        fi
    fi
    
    if [ ! -d "venv-py312" ]; then
        python3.12 -m venv venv-py312
        echo "✅ Python 3.12 virtual environment created"
    fi
    echo ""
    
    # Activate Python 3.12 environment
    echo "🔧 Activating Python 3.12 environment..."
    source venv-py312/bin/activate
    
    VENV_PYTHON=$(python --version | cut -d' ' -f2)
    echo "✅ Using Python $VENV_PYTHON"
    echo ""
    
elif [ "$CURRENT_MAJOR" -eq 3 ] && [ "$CURRENT_MINOR" -ge 11 ]; then
    echo "✅ Python $CURRENT_PYTHON is compatible with audio emotion detection"
    echo ""
    
    # Use existing venv
    if [ -d "venv" ]; then
        echo "🔧 Activating existing virtual environment..."
        source venv/bin/activate
    else
        echo "❌ Virtual environment not found"
        echo "   Run ./install.sh first to create base environment"
        exit 1
    fi
    echo ""
else
    echo "❌ Python 3.11 or higher required for audio emotion detection"
    echo "   Current version: $CURRENT_PYTHON"
    echo "   Install Python 3.12: brew install python@3.12"
    exit 1
fi

# Upgrade pip
echo "🔧 Upgrading pip..."
pip install --upgrade pip
echo "✅ pip upgraded"
echo ""

# Install base dependencies if needed
echo "📦 Installing base dependencies..."
pip install -r requirements.txt
echo "✅ Base dependencies installed"
echo ""

# Install audio emotion detection dependencies
echo "📦 Installing audio emotion detection dependencies..."
echo "   This will download:"
echo "   - PyTorch (~150 MB)"
echo "   - transformers (~500 MB)"
echo "   - wav2vec2 model (~1.2 GB, first run only)"
echo ""
echo "   Total download: ~1.8 GB"
echo "   This may take 5-10 minutes..."
echo ""

pip install 'transformers<5.0' 'torch>=2.2.0,<2.3.0' 'torchaudio>=2.2.0,<2.3.0' 'numpy<2.0' protobuf

if [ $? -eq 0 ]; then
    echo "✅ Audio emotion dependencies installed successfully!"
    echo ""
    
    # Update .env to enable audio emotion
    echo "🔧 Enabling audio emotion detection in .env..."
    if grep -q "AUDIO_EMOTION_ENABLED=false" .env; then
        sed -i.bak 's/AUDIO_EMOTION_ENABLED=false/AUDIO_EMOTION_ENABLED=true/' .env
        echo "✅ AUDIO_EMOTION_ENABLED=true"
    elif grep -q "AUDIO_EMOTION_ENABLED=true" .env; then
        echo "✅ Already enabled"
    else
        echo "AUDIO_EMOTION_ENABLED=true" >> .env
        echo "AUDIO_EMOTION_MODEL=ehcalabres/wav2vec2-lg-xlsr-en-speech-emotion-recognition" >> .env
        echo "✅ Added to .env"
    fi
    echo ""
    
    # Test the installation
    echo "🧪 Testing audio emotion detection..."
    python -c "
import sys
print(f'Python version: {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}')

try:
    import torch
    print(f'✅ PyTorch {torch.__version__}')
    print(f'   Device: {\"CUDA\" if torch.cuda.is_available() else \"CPU\"}')
except ImportError as e:
    print(f'❌ PyTorch: {e}')
    sys.exit(1)

try:
    import transformers
    print(f'✅ transformers {transformers.__version__}')
except ImportError as e:
    print(f'❌ transformers: {e}')
    sys.exit(1)

try:
    import torchaudio
    print(f'✅ torchaudio {torchaudio.__version__}')
except ImportError as e:
    print(f'❌ torchaudio: {e}')
    sys.exit(1)

try:
    import numpy
    print(f'✅ numpy {numpy.__version__}')
except ImportError as e:
    print(f'❌ numpy: {e}')
    sys.exit(1)

print('')
print('✅ All dependencies installed successfully!')
print('   Audio emotion detection is ready to use!')
"
    
    if [ $? -eq 0 ]; then
        echo ""
        echo "========================================"
        echo "✅ Audio Emotion Detection Ready!"
        echo "========================================"
        echo ""
        echo "📝 What's Enabled:"
        echo "✅ Text emotion detection (keywords + LLM)"
        echo "✅ Audio emotion detection (wav2vec2)"
        echo "✅ Voice input (Whisper transcription)"
        echo "✅ Voice output (eSpeak TTS)"
        echo "✅ Multi-modal emotion (text + voice)"
        echo ""
        echo "📝 Next Steps:"
        if [ -d "venv-py312" ]; then
            echo "1. Activate Python 3.12 environment: source venv-py312/bin/activate"
        else
            echo "1. Environment already activated"
        fi
        echo "2. Start backend: python -m uvicorn app.main:socket_app --reload --port 3001"
        echo "3. Start frontend: cd client && npm run dev"
        echo "4. Test voice input - emotions will be detected from voice tone!"
        echo ""
        echo "📚 Documentation:"
        echo "- AUDIO_EMOTION_DETECTION.md - Feature overview"
        echo "- AUDIO_EMOTION_SETUP.md - Setup guide"
        echo ""
        echo "🎉 Audio emotion detection is ready!"
        echo ""
        echo "Note: First run will download wav2vec2 model (~1.2 GB)"
        echo "      This happens automatically when you first use voice input"
    else
        echo ""
        echo "❌ Installation test failed"
        echo "   Check error messages above"
    fi
else
    echo "❌ Failed to install audio emotion dependencies"
    echo "   Text emotion detection will still work"
    echo ""
    echo "Troubleshooting:"
    echo "1. Check internet connection"
    echo "2. Try: pip install --upgrade pip"
    echo "3. Try: pip install torch --index-url https://download.pytorch.org/whl/cpu"
fi
