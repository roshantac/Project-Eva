#!/bin/bash

# Eva AI - Ollama Local Model Installation Script
# This script installs Ollama and sets up a local model

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
    echo "║   🤖 Eva AI - Local Model Setup (Ollama)                ║"
    echo "║   100% FREE - No API Costs!                              ║"
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

# Check if Ollama is already installed
if command -v ollama &> /dev/null; then
    print_success "Ollama is already installed"
    OLLAMA_VERSION=$(ollama --version 2>&1 | head -n 1)
    print_info "Version: $OLLAMA_VERSION"
else
    print_info "Installing Ollama..."
    
    if [ "$OS" == "macos" ]; then
        # Check if Homebrew is available
        if command -v brew &> /dev/null; then
            print_info "Installing via Homebrew..."
            brew install ollama
        else
            print_warning "Homebrew not found. Please install from: https://ollama.ai/download"
            print_info "Or install Homebrew first: /bin/bash -c \"\$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)\""
            exit 1
        fi
    elif [ "$OS" == "linux" ]; then
        print_info "Installing via official script..."
        curl -fsSL https://ollama.ai/install.sh | sh
    fi
    
    if command -v ollama &> /dev/null; then
        print_success "Ollama installed successfully!"
    else
        print_error "Ollama installation failed"
        exit 1
    fi
fi

echo ""

# Start Ollama service
print_info "Starting Ollama service..."

if [ "$OS" == "macos" ]; then
    # On macOS, start as background service
    if pgrep -x "ollama" > /dev/null; then
        print_success "Ollama is already running"
    else
        print_info "Starting Ollama in background..."
        nohup ollama serve > /dev/null 2>&1 &
        sleep 3
        
        if pgrep -x "ollama" > /dev/null; then
            print_success "Ollama service started"
        else
            print_warning "Failed to start Ollama automatically"
            print_info "Please run 'ollama serve' in a separate terminal"
        fi
    fi
elif [ "$OS" == "linux" ]; then
    # On Linux, check if systemd service is running
    if systemctl is-active --quiet ollama; then
        print_success "Ollama service is running"
    else
        print_info "Starting Ollama service..."
        sudo systemctl start ollama
        sudo systemctl enable ollama
        print_success "Ollama service started and enabled"
    fi
fi

echo ""

# Wait for Ollama to be ready
print_info "Waiting for Ollama to be ready..."
MAX_RETRIES=10
RETRY=0

while [ $RETRY -lt $MAX_RETRIES ]; do
    if curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
        print_success "Ollama is ready!"
        break
    fi
    RETRY=$((RETRY + 1))
    sleep 1
done

if [ $RETRY -eq $MAX_RETRIES ]; then
    print_error "Ollama is not responding. Please start it manually with: ollama serve"
    exit 1
fi

echo ""

# Show model selection
print_info "Available models to install:"
echo ""
echo "  1. llama3.1:8b (Recommended) - 4.7GB"
echo "     Fast, good quality, works on most systems"
echo ""
echo "  2. phi3:mini - 2.3GB"
echo "     Smallest, fastest, good for low-end systems"
echo ""
echo "  3. mistral:7b - 4.1GB"
echo "     Good balance, fast responses"
echo ""
echo "  4. llama3.1:70b - 40GB"
echo "     Best quality, needs 32GB+ RAM"
echo ""

# Ask user which model to install
read -p "Which model would you like to install? (1-4, default: 1): " MODEL_CHOICE

case $MODEL_CHOICE in
    2)
        MODEL_NAME="phi3:mini"
        MODEL_SIZE="2.3GB"
        ;;
    3)
        MODEL_NAME="mistral:7b"
        MODEL_SIZE="4.1GB"
        ;;
    4)
        MODEL_NAME="llama3.1:70b"
        MODEL_SIZE="40GB"
        print_warning "This model requires at least 32GB RAM!"
        read -p "Continue? (y/n): " CONFIRM
        if [ "$CONFIRM" != "y" ]; then
            MODEL_NAME="llama3.1:8b"
            MODEL_SIZE="4.7GB"
        fi
        ;;
    *)
        MODEL_NAME="llama3.1:8b"
        MODEL_SIZE="4.7GB"
        ;;
esac

echo ""
print_info "Installing model: $MODEL_NAME ($MODEL_SIZE)"
print_warning "This may take several minutes depending on your internet speed..."
echo ""

# Pull the model
ollama pull $MODEL_NAME

if [ $? -eq 0 ]; then
    print_success "Model $MODEL_NAME installed successfully!"
else
    print_error "Failed to install model"
    exit 1
fi

echo ""

# Test the model
print_info "Testing the model..."
TEST_RESPONSE=$(ollama run $MODEL_NAME "Say hello in one sentence" 2>&1 | head -n 1)

if [ ! -z "$TEST_RESPONSE" ]; then
    print_success "Model is working!"
    print_info "Response: $TEST_RESPONSE"
else
    print_warning "Model test failed, but installation completed"
fi

echo ""

# Configure Eva AI
print_info "Configuring Eva AI to use Ollama..."

if [ -f .env ]; then
    # Update existing .env
    if grep -q "LLM_PROVIDER=" .env; then
        sed -i.bak "s/LLM_PROVIDER=.*/LLM_PROVIDER=ollama/" .env
    else
        echo "LLM_PROVIDER=ollama" >> .env
    fi
    
    if grep -q "OLLAMA_MODEL=" .env; then
        sed -i.bak "s/OLLAMA_MODEL=.*/OLLAMA_MODEL=$MODEL_NAME/" .env
    else
        echo "OLLAMA_MODEL=$MODEL_NAME" >> .env
    fi
    
    rm -f .env.bak
    print_success "Updated .env configuration"
else
    # Create new .env from example
    if [ -f .env.example ]; then
        cp .env.example .env
        sed -i.bak "s/LLM_PROVIDER=.*/LLM_PROVIDER=ollama/" .env
        sed -i.bak "s/OLLAMA_MODEL=.*/OLLAMA_MODEL=$MODEL_NAME/" .env
        rm -f .env.bak
        print_success "Created .env with Ollama configuration"
    else
        print_warning ".env.example not found, please configure manually"
    fi
fi

echo ""
print_success "Setup complete! 🎉"
echo ""

# Final instructions
echo -e "${BLUE}╔═══════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║                    You're All Set!                        ║${NC}"
echo -e "${BLUE}╚═══════════════════════════════════════════════════════════╝${NC}"
echo ""
echo "✅ Ollama installed and running"
echo "✅ Model $MODEL_NAME ready to use"
echo "✅ Eva AI configured to use local model"
echo ""
echo "Next steps:"
echo ""
echo "1. Make sure MongoDB is running:"
echo "   ${YELLOW}brew services start mongodb-community${NC} (macOS)"
echo "   ${YELLOW}sudo systemctl start mongod${NC} (Linux)"
echo ""
echo "2. Start Eva AI:"
echo "   ${YELLOW}npm run dev${NC}"
echo ""
echo "3. Open your browser:"
echo "   ${GREEN}http://localhost:5173${NC}"
echo ""
echo "💡 Tips:"
echo "   - No API costs! Everything runs locally"
echo "   - Works offline once model is downloaded"
echo "   - To change models: ollama pull <model-name>"
echo "   - To list models: ollama list"
echo ""
echo "📚 Documentation:"
echo "   - Local Models Guide: ${BLUE}INSTALL_LOCAL_MODELS.md${NC}"
echo "   - Quick Start: ${BLUE}QUICKSTART.md${NC}"
echo ""
echo -e "${GREEN}Enjoy your FREE AI assistant! 🚀${NC}"
