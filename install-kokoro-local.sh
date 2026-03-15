#!/bin/bash

# Eva AI - Kokoro-82M Local TTS Installation Script
# This script installs Kokoro-82M TTS model for high-quality local text-to-speech

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

print_header() {
    echo -e "${BLUE}"
    echo "╔═══════════════════════════════════════════════════════════╗"
    echo "║                                                           ║"
    echo "║   🎤 Eva AI - Kokoro-82M Local TTS Setup                 ║"
    echo "║   High-Quality Local Text-to-Speech (82M params)         ║"
    echo "║                                                           ║"
    echo "╚═══════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_info() {
    echo -e "${CYAN}ℹ️  $1${NC}"
}

print_step() {
    echo -e "${BLUE}▶ $1${NC}"
}

print_header

echo ""
print_info "This script will install Kokoro-82M TTS for high-quality local speech synthesis"
echo ""
echo "✨ Kokoro-82M Features:"
echo "   🎯 82 million parameters (lightweight)"
echo "   🏆 #1 ranked in TTS Arena (beats larger models)"
echo "   🎭 54 voices across 8 languages"
echo "   🌐 American & British English support"
echo "   💾 Runs 100% locally (no API costs)"
echo "   🆓 Apache 2.0 license (free for commercial use)"
echo "   ⚡ Fast generation on CPU or GPU"
echo ""

# Check Python version
CURRENT_PYTHON=$(python3 --version 2>&1 | cut -d' ' -f2)
CURRENT_MAJOR=$(echo $CURRENT_PYTHON | cut -d'.' -f1)
CURRENT_MINOR=$(echo $CURRENT_PYTHON | cut -d'.' -f2)

print_info "Current Python version: $CURRENT_PYTHON"
echo ""

if [ "$CURRENT_MAJOR" -eq 3 ] && [ "$CURRENT_MINOR" -ge 11 ]; then
    print_success "Python $CURRENT_PYTHON is compatible with Kokoro-82M"
else
    print_error "Python 3.11 or higher required for Kokoro-82M"
    print_info "Current version: $CURRENT_PYTHON"
    print_info "Install Python 3.12: brew install python@3.12"
    exit 1
fi

echo ""

# Determine which venv to use
if [ -d "venv-py312" ]; then
    VENV_PATH="venv-py312"
    print_info "Using Python 3.12 environment (venv-py312)"
elif [ -d "venv" ]; then
    VENV_PATH="venv"
    print_info "Using default environment (venv)"
else
    print_error "No virtual environment found"
    print_info "Run ./install.sh first to create base environment"
    exit 1
fi

echo ""
print_step "Step 1: Activating virtual environment..."
echo ""

source "$VENV_PATH/bin/activate"

VENV_PYTHON=$(python --version | cut -d' ' -f2)
print_success "Using Python $VENV_PYTHON"

echo ""
print_step "Step 2: Installing system dependencies..."
echo ""

# Check for espeak-ng (required by Kokoro)
if command -v espeak-ng &> /dev/null; then
    print_success "espeak-ng is already installed"
else
    print_info "Installing espeak-ng..."
    if [[ "$OSTYPE" == "darwin"* ]]; then
        if command -v brew &> /dev/null; then
            brew install espeak-ng
            print_success "espeak-ng installed via Homebrew"
        else
            print_error "Homebrew not found"
            print_info "Install Homebrew: /bin/bash -c \"\$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)\""
            exit 1
        fi
    elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
        sudo apt-get update
        sudo apt-get install -y espeak-ng
        print_success "espeak-ng installed"
    else
        print_error "Unsupported OS for automatic espeak-ng installation"
        print_info "Please install espeak-ng manually"
        exit 1
    fi
fi

echo ""
print_step "Step 3: Installing Kokoro-82M Python package..."
echo ""

print_info "Installing kokoro package (this may take a few minutes)..."
if [ -f "requirements-kokoro.txt" ]; then
    pip install -r requirements-kokoro.txt
else
    pip install "kokoro>=0.9.4" soundfile
fi

if [ $? -eq 0 ]; then
    print_success "Kokoro-82M package installed successfully!"
else
    print_error "Failed to install Kokoro-82M package"
    exit 1
fi

echo ""
print_step "Step 4: Testing Kokoro-82M installation..."
echo ""

# Test the installation
python3 << 'PYTHON_TEST'
import sys
print("Testing Kokoro-82M installation...")

try:
    from kokoro import KPipeline
    print("✅ Kokoro package imported successfully")
except ImportError as e:
    print(f"❌ Failed to import kokoro: {e}")
    sys.exit(1)

try:
    import soundfile
    print("✅ soundfile package available")
except ImportError as e:
    print(f"❌ Failed to import soundfile: {e}")
    sys.exit(1)

try:
    import torch
    print(f"✅ PyTorch {torch.__version__} available")
except ImportError:
    print("⚠️  PyTorch not found (optional, but recommended for GPU acceleration)")

print("")
print("✅ All Kokoro-82M dependencies are ready!")
PYTHON_TEST

if [ $? -ne 0 ]; then
    print_error "Installation test failed"
    exit 1
fi

echo ""
print_step "Step 5: Downloading Kokoro-82M model..."
echo ""

print_info "First use will download model files (~327 MB)"
print_info "Testing model download and generation..."

# Test model download and generation
python3 << 'PYTHON_DOWNLOAD'
import sys
from pathlib import Path

try:
    from kokoro import KPipeline
    import soundfile as sf
    
    print("Initializing Kokoro pipeline...")
    pipeline = KPipeline(lang_code='a')  # 'a' for American English
    
    print("Generating test audio...")
    text = "Hello, this is Eva AI with Kokoro TTS."
    generator = pipeline(text, voice='af_heart')
    
    # Generate audio
    audio_data = None
    for i, (gs, ps, audio) in enumerate(generator):
        audio_data = audio
        break
    
    if audio_data is not None:
        # Save test file
        test_path = Path('temp') / 'kokoro_test.wav'
        test_path.parent.mkdir(exist_ok=True)
        sf.write(str(test_path), audio_data, 24000)
        print(f"✅ Test audio generated: {test_path}")
        print(f"   Duration: {len(audio_data) / 24000:.2f} seconds")
    else:
        print("❌ Failed to generate audio")
        sys.exit(1)
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("")
print("✅ Kokoro-82M model downloaded and tested successfully!")
PYTHON_DOWNLOAD

if [ $? -ne 0 ]; then
    print_error "Model download or test failed"
    exit 1
fi

echo ""
print_step "Step 6: Configuring Eva AI..."
echo ""

# Configure client to use server-side TTS
print_info "Configuring client to receive audio from server..."
if [ -f "client/.env" ]; then
    if grep -q "VITE_TTS_PROVIDER=" client/.env; then
        sed -i.bak 's/VITE_TTS_PROVIDER=.*/VITE_TTS_PROVIDER=server/' client/.env
    else
        echo "VITE_TTS_PROVIDER=server" >> client/.env
    fi
    rm -f client/.env.bak
    print_success "Client configured to use server-side TTS"
else
    echo "VITE_TTS_PROVIDER=server" > client/.env
    print_success "Created client/.env with server-side TTS"
fi

# Update .env configuration
if [ ! -f ".env" ]; then
    print_error ".env not found. Please run ./install.sh first"
    exit 1
fi

# Backup .env
cp .env .env.backup.kokoro
print_info "Backed up .env to .env.backup.kokoro"

# Update or add AUDIO_PROVIDER
if grep -q "AUDIO_PROVIDER=" .env; then
    sed -i.bak 's/AUDIO_PROVIDER=.*/AUDIO_PROVIDER=kokoro/' .env
    print_success "Set AUDIO_PROVIDER=kokoro"
else
    echo "AUDIO_PROVIDER=kokoro" >> .env
    print_success "Added AUDIO_PROVIDER=kokoro"
fi

# Add Kokoro-specific settings
if ! grep -q "KOKORO_LANG_CODE=" .env; then
    echo "" >> .env
    echo "# Kokoro-82M TTS (Local - FREE, HIGH QUALITY)" >> .env
    echo "KOKORO_LANG_CODE=a" >> .env
    echo "KOKORO_DEFAULT_VOICE=af_heart" >> .env
    echo "KOKORO_SAMPLE_RATE=24000" >> .env
    print_success "Added Kokoro configuration to .env"
fi

# Disable CLIENT_TTS_ENABLED (we're using server-side Kokoro)
if grep -q "CLIENT_TTS_ENABLED=" .env; then
    sed -i.bak 's/CLIENT_TTS_ENABLED=.*/CLIENT_TTS_ENABLED=false/' .env
    print_success "Set CLIENT_TTS_ENABLED=false (using server-side Kokoro)"
fi

# Disable eSpeak (optional)
echo ""
print_info "Do you want to disable eSpeak (since Kokoro provides better quality)?"
read -p "Disable eSpeak? (y/n, default: y): " DISABLE_ESPEAK

if [ -z "$DISABLE_ESPEAK" ] || [ "$DISABLE_ESPEAK" = "y" ] || [ "$DISABLE_ESPEAK" = "Y" ]; then
    if grep -q "ESPEAK_ENABLED=" .env; then
        sed -i.bak 's/ESPEAK_ENABLED=.*/ESPEAK_ENABLED=false/' .env
    else
        echo "ESPEAK_ENABLED=false" >> .env
    fi
    print_success "eSpeak disabled (Kokoro will handle all TTS)"
else
    print_info "eSpeak remains enabled as fallback"
fi

# Clean up backup files
rm -f .env.bak

echo ""
echo -e "${GREEN}╔═══════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║              Kokoro-82M Installation Complete! 🎉         ║${NC}"
echo -e "${GREEN}╚═══════════════════════════════════════════════════════════╝${NC}"
echo ""

print_success "Kokoro-82M TTS is configured and ready to use!"
echo ""

echo "📝 What's Installed:"
echo "   ✅ Kokoro-82M Python package (v0.9.4+)"
echo "   ✅ espeak-ng (phoneme processing)"
echo "   ✅ soundfile (audio I/O)"
echo "   ✅ Model files downloaded (~327 MB)"
echo "   ✅ Server configured to use Kokoro-82M"
echo "   ✅ Client configured to receive audio from server"
echo ""

echo "🎭 Available Voices:"
echo "   • af_heart (female, clear, energetic) - Default"
echo "   • af_bella (female, warm, friendly)"
echo "   • af_sarah (female, thoughtful)"
echo "   • af_nicole (female, casual)"
echo "   • am_michael (male, professional)"
echo "   • am_adam (male, deep)"
echo "   • bf_emma (British female)"
echo "   • bm_george (British male)"
echo "   • ...and 46 more voices!"
echo ""

echo "⚙️  Configuration:"
echo "   • Audio Provider: Kokoro (local)"
echo "   • Language: American English"
echo "   • Default Voice: af_heart"
echo "   • Sample Rate: 24kHz"
if [ "$DISABLE_ESPEAK" = "y" ] || [ "$DISABLE_ESPEAK" = "Y" ] || [ -z "$DISABLE_ESPEAK" ]; then
    echo "   • eSpeak: Disabled"
else
    echo "   • eSpeak: Enabled (fallback)"
fi
echo ""

echo "🚀 Next Steps:"
echo ""
echo "1. Start Eva AI:"
echo "   ${YELLOW}./start.sh${NC}"
if [ -d "venv-py312" ]; then
    echo "   ${YELLOW}./start.sh --with-emotions${NC} (if using Python 3.12)"
fi
echo ""
echo "2. Or start manually:"
echo "   ${YELLOW}# Terminal 1: Backend${NC}"
if [ -d "venv-py312" ]; then
    echo "   ${YELLOW}source venv-py312/bin/activate${NC}"
else
    echo "   ${YELLOW}source venv/bin/activate${NC}"
fi
echo "   ${YELLOW}python -m uvicorn app.main:socket_app --reload --port 3001${NC}"
echo ""
echo "   ${YELLOW}# Terminal 2: Frontend${NC}"
echo "   ${YELLOW}cd client && npm run dev${NC}"
echo ""
echo "3. Open browser: ${GREEN}http://localhost:5173${NC}"
echo ""
echo "4. Enable audio output and send a message"
echo "   ${CYAN}High-quality Kokoro TTS will be used!${NC}"
echo ""

echo "💡 Performance:"
echo "   • First generation: 1-3 seconds (model loading)"
echo "   • Subsequent: 0.3-1 second per sentence"
echo "   • Quality: 24kHz, natural-sounding speech"
echo "   • GPU: Automatically used if available (faster)"
echo "   • CPU: Works great on modern CPUs"
echo ""

echo "📖 Documentation:"
echo "   • ${BLUE}KOKORO_LOCAL_SETUP.md${NC}    - Setup guide"
echo "   • ${BLUE}TTS_QUICK_SWITCH.md${NC}      - Switch between TTS providers"
echo ""

echo "🔧 Advanced Configuration:"
echo "   • Change voice: Edit KOKORO_DEFAULT_VOICE in .env"
echo "   • Available voices: af_heart, af_bella, af_sarah, am_michael, etc."
echo "   • Language codes: 'a' (American), 'b' (British)"
echo ""

echo -e "${GREEN}🎉 Enjoy high-quality local TTS with Eva AI!${NC}"
echo ""
