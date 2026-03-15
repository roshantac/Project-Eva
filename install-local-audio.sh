#!/bin/bash

# Eva AI - Local Audio Tools Installation Script
# Installs Whisper.cpp and eSpeak for FREE local audio

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

print_header() {
    echo -e "${BLUE}"
    echo "╔═══════════════════════════════════════════════════════════╗"
    echo "║                                                           ║"
    echo "║   🎤 Eva AI - Local Audio Setup                          ║"
    echo "║   FREE Voice Features!                                    ║"
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
    echo -e "${BLUE}ℹ️  $1${NC}"
}

print_header

# Detect OS
OS="unknown"
if [[ "$OSTYPE" == "darwin"* ]]; then
    OS="macos"
elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
    OS="linux"
else
    print_error "Unsupported operating system: $OSTYPE"
    exit 1
fi

print_info "Detected OS: $OS"
echo ""

# Install eSpeak (Simple TTS)
print_info "Installing eSpeak (Text-to-Speech)..."

if command -v espeak &> /dev/null; then
    print_success "eSpeak is already installed"
else
    if [ "$OS" == "macos" ]; then
        if command -v brew &> /dev/null; then
            brew install espeak
            print_success "eSpeak installed"
        else
            print_warning "Homebrew not found. Install from: https://brew.sh"
        fi
    elif [ "$OS" == "linux" ]; then
        sudo apt-get update
        sudo apt-get install -y espeak
        print_success "eSpeak installed"
    fi
fi

echo ""

# Ask about Whisper.cpp installation
print_info "Whisper.cpp Setup (Speech-to-Text)"
echo ""
echo "Whisper.cpp provides FREE local speech recognition."
echo "It requires ~1-5GB disk space depending on model size."
echo ""
read -p "Install Whisper.cpp? (y/n, default: y): " INSTALL_WHISPER

if [ "$INSTALL_WHISPER" != "n" ]; then
    print_info "Installing Whisper.cpp..."
    
    # Clone whisper.cpp
    WHISPER_DIR="$HOME/.whisper-cpp"
    
    if [ -d "$WHISPER_DIR" ]; then
        print_info "Whisper.cpp directory exists, updating..."
        cd "$WHISPER_DIR"
        git pull
    else
        print_info "Cloning Whisper.cpp..."
        git clone https://github.com/ggerganov/whisper.cpp.git "$WHISPER_DIR"
        cd "$WHISPER_DIR"
    fi
    
    # Build whisper.cpp
    print_info "Building Whisper.cpp..."
    make
    
    if [ $? -eq 0 ]; then
        print_success "Whisper.cpp built successfully"
        
        # Download model
        echo ""
        print_info "Downloading Whisper model..."
        echo ""
        echo "Available models:"
        echo "  1. tiny.en   - Fastest, 75MB (recommended for testing)"
        echo "  2. base.en   - Good balance, 142MB (recommended)"
        echo "  3. small.en  - Better quality, 466MB"
        echo "  4. medium.en - High quality, 1.5GB"
        echo ""
        read -p "Which model? (1-4, default: 2): " MODEL_CHOICE
        
        case $MODEL_CHOICE in
            1)
                MODEL="tiny.en"
                ;;
            3)
                MODEL="small.en"
                ;;
            4)
                MODEL="medium.en"
                ;;
            *)
                MODEL="base.en"
                ;;
        esac
        
        print_info "Downloading $MODEL model..."
        bash ./models/download-ggml-model.sh $MODEL
        
        if [ $? -eq 0 ]; then
            print_success "Model $MODEL downloaded"
            
            # Update .env
            if [ -f "$HOME/workspace/Projects/AI/Eva-AI/.env" ]; then
                cd "$HOME/workspace/Projects/AI/Eva-AI"
                
                if grep -q "WHISPER_CPP_PATH=" .env; then
                    sed -i.bak "s|WHISPER_CPP_PATH=.*|WHISPER_CPP_PATH=$WHISPER_DIR/main|" .env
                else
                    echo "WHISPER_CPP_PATH=$WHISPER_DIR/main" >> .env
                fi
                
                if grep -q "WHISPER_MODEL=" .env; then
                    sed -i.bak "s|WHISPER_MODEL=.*|WHISPER_MODEL=$MODEL|" .env
                else
                    echo "WHISPER_MODEL=$MODEL" >> .env
                fi
                
                rm -f .env.bak
                print_success "Updated .env configuration"
            fi
        else
            print_error "Failed to download model"
        fi
    else
        print_error "Failed to build Whisper.cpp"
    fi
else
    print_info "Skipping Whisper.cpp installation"
    print_info "You can use Groq's FREE Whisper API instead"
    print_info "Get a free key from: https://console.groq.com/"
fi

echo ""

# Configure Eva AI
print_info "Configuring Eva AI for local audio..."

if [ -f .env ]; then
    if grep -q "AUDIO_PROVIDER=" .env; then
        sed -i.bak "s/AUDIO_PROVIDER=.*/AUDIO_PROVIDER=local/" .env
    else
        echo "AUDIO_PROVIDER=local" >> .env
    fi
    
    if grep -q "AUDIO_ENABLED=" .env; then
        sed -i.bak "s/AUDIO_ENABLED=.*/AUDIO_ENABLED=true/" .env
    else
        echo "AUDIO_ENABLED=true" >> .env
    fi
    
    rm -f .env.bak
    print_success "Updated .env for local audio"
fi

echo ""
print_success "Local audio setup complete! 🎉"
echo ""

# Summary
echo -e "${BLUE}╔═══════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║                    Setup Summary                          ║${NC}"
echo -e "${BLUE}╚═══════════════════════════════════════════════════════════╝${NC}"
echo ""

if command -v espeak &> /dev/null; then
    echo "✅ eSpeak (TTS): Installed"
else
    echo "❌ eSpeak (TTS): Not installed"
fi

if [ -d "$WHISPER_DIR" ] && [ -f "$WHISPER_DIR/main" ]; then
    echo "✅ Whisper.cpp (STT): Installed"
else
    echo "⚠️  Whisper.cpp (STT): Not installed (will use Groq fallback)"
fi

echo ""
echo "Audio Provider: Local (FREE)"
echo ""

echo "Next steps:"
echo ""
echo "1. Start Eva AI:"
echo "   ${YELLOW}npm run dev${NC}"
echo ""
echo "2. Test voice features in the browser"
echo "   ${GREEN}http://localhost:5173${NC}"
echo ""
echo "3. Optional: Add Groq API key for better STT:"
echo "   Get free key: ${BLUE}https://console.groq.com/${NC}"
echo "   Add to .env: ${YELLOW}GROQ_API_KEY=your_key${NC}"
echo ""
echo "💡 Tips:"
echo "   - eSpeak voice is simple but works offline"
echo "   - Whisper.cpp provides excellent transcription"
echo "   - Groq Whisper is FREE and faster (cloud)"
echo "   - All options are 100% FREE!"
echo ""
echo -e "${GREEN}Enjoy FREE voice features! 🎤🔊${NC}"
