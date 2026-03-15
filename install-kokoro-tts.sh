#!/bin/bash

# Eva AI - Kokoro TTS Installation Script
# This script configures high-quality client-side TTS using kokoro-js

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
    echo "║   🎤 Eva AI - Kokoro TTS Setup                           ║"
    echo "║   High-Quality Client-Side Text-to-Speech                ║"
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
print_info "This script will configure Eva AI to use Kokoro TTS"
echo ""
echo "Benefits of Kokoro TTS:"
echo "  ✨ High-quality natural-sounding speech"
echo "  🎭 28+ voices with different accents and characteristics"
echo "  🎯 Emotion-aware voice selection"
echo "  🌐 Runs 100% in the browser (no server load)"
echo "  💾 Works offline after initial download (~2MB)"
echo "  🆓 Completely free (Apache 2.0 license)"
echo ""

# Check if client directory exists
if [ ! -d "client" ]; then
    print_error "Client directory not found. Are you in the project root?"
    exit 1
fi

# Check if package.json exists
if [ ! -f "client/package.json" ]; then
    print_error "client/package.json not found"
    exit 1
fi

echo ""
print_step "Step 1: Installing kokoro-js package..."
echo ""

cd client

# Check if kokoro-js is already installed
if grep -q '"kokoro-js"' package.json; then
    print_success "kokoro-js is already installed"
else
    print_info "Installing kokoro-js and dependencies..."
    npm install kokoro-js
    
    if [ $? -eq 0 ]; then
        print_success "kokoro-js installed successfully!"
    else
        print_error "Failed to install kokoro-js"
        exit 1
    fi
fi

echo ""
print_step "Step 2: Configuring client environment..."
echo ""

# Create client/.env with Kokoro configuration
cat > .env << 'EOF'
# Client TTS Configuration
# Options: 'server' (use server-side TTS with eSpeak/Piper) or 'kokoro' (use client-side Kokoro TTS)
VITE_TTS_PROVIDER=kokoro

# Kokoro TTS Settings (only used when VITE_TTS_PROVIDER=kokoro)
VITE_KOKORO_MODEL=onnx-community/Kokoro-82M-v1.0-ONNX
VITE_KOKORO_DTYPE=q8
VITE_KOKORO_DEVICE=wasm
EOF

print_success "Created client/.env with Kokoro configuration"

cd ..

echo ""
print_step "Step 3: Configuring server environment..."
echo ""

# Update server .env
if [ ! -f ".env" ]; then
    print_error ".env not found. Please run ./install.sh first"
    exit 1
fi

# Backup .env
cp .env .env.backup
print_info "Backed up .env to .env.backup"

# Update CLIENT_TTS_ENABLED
if grep -q "CLIENT_TTS_ENABLED=" .env; then
    sed -i.bak 's/CLIENT_TTS_ENABLED=.*/CLIENT_TTS_ENABLED=true/' .env
    print_success "Set CLIENT_TTS_ENABLED=true"
else
    echo "CLIENT_TTS_ENABLED=true" >> .env
    print_success "Added CLIENT_TTS_ENABLED=true"
fi

# Ask user if they want to disable eSpeak
echo ""
print_info "Do you want to disable eSpeak (server-side TTS)?"
echo "   This is recommended when using Kokoro TTS"
echo "   You can always re-enable it later"
echo ""
read -p "Disable eSpeak? (y/n, default: y): " DISABLE_ESPEAK

if [ -z "$DISABLE_ESPEAK" ] || [ "$DISABLE_ESPEAK" = "y" ] || [ "$DISABLE_ESPEAK" = "Y" ]; then
    if grep -q "ESPEAK_ENABLED=" .env; then
        sed -i.bak 's/ESPEAK_ENABLED=.*/ESPEAK_ENABLED=false/' .env
        print_success "Set ESPEAK_ENABLED=false"
    else
        echo "ESPEAK_ENABLED=false" >> .env
        print_success "Added ESPEAK_ENABLED=false"
    fi
else
    if grep -q "ESPEAK_ENABLED=" .env; then
        sed -i.bak 's/ESPEAK_ENABLED=.*/ESPEAK_ENABLED=true/' .env
        print_success "Set ESPEAK_ENABLED=true (eSpeak remains enabled)"
    else
        echo "ESPEAK_ENABLED=true" >> .env
        print_success "Added ESPEAK_ENABLED=true (eSpeak remains enabled)"
    fi
fi

# Clean up backup files
rm -f .env.bak

echo ""
print_step "Step 4: Verifying installation..."
echo ""

# Check if kokoro-js is in node_modules
if [ -d "client/node_modules/kokoro-js" ]; then
    print_success "kokoro-js package verified"
else
    print_error "kokoro-js not found in node_modules"
    exit 1
fi

# Check if service file exists
if [ -f "client/src/services/kokoroTTSService.js" ]; then
    print_success "Kokoro TTS service found"
else
    print_error "Kokoro TTS service not found"
    exit 1
fi

# Check configuration
if [ -f "client/.env" ] && grep -q "VITE_TTS_PROVIDER=kokoro" client/.env; then
    print_success "Client configuration verified"
else
    print_error "Client configuration not found"
    exit 1
fi

echo ""
echo -e "${GREEN}╔═══════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║                  Installation Complete! 🎉                ║${NC}"
echo -e "${GREEN}╚═══════════════════════════════════════════════════════════╝${NC}"
echo ""

print_success "Kokoro TTS is configured and ready to use!"
echo ""

echo "📝 What's Configured:"
echo "   ✅ kokoro-js package installed"
echo "   ✅ Client TTS provider set to Kokoro"
echo "   ✅ Server configured to skip TTS generation"
if [ "$DISABLE_ESPEAK" = "y" ] || [ "$DISABLE_ESPEAK" = "Y" ] || [ -z "$DISABLE_ESPEAK" ]; then
    echo "   ✅ eSpeak disabled (Kokoro handles all TTS)"
else
    echo "   ✅ eSpeak enabled (available as fallback)"
fi
echo ""

echo "📚 Configuration Files:"
echo "   • client/.env         - Client TTS settings"
echo "   • .env                - Server TTS settings"
echo "   • .env.backup         - Backup of original .env"
echo ""

echo "🚀 Next Steps:"
echo ""
echo "1. Start Eva AI:"
echo "   ${YELLOW}./start.sh${NC}"
echo ""
echo "2. Or start manually:"
echo "   ${YELLOW}# Terminal 1: Backend${NC}"
echo "   ${YELLOW}python -m uvicorn app.main:socket_app --reload --port 3001${NC}"
echo ""
echo "   ${YELLOW}# Terminal 2: Frontend${NC}"
echo "   ${YELLOW}cd client && npm run dev${NC}"
echo ""
echo "3. Open browser: ${GREEN}http://localhost:5173${NC}"
echo ""
echo "4. Enable audio output and send a message"
echo "   ${CYAN}First time: Model downloads (~2MB, 5-30 seconds)${NC}"
echo "   ${CYAN}After that: Instant high-quality audio!${NC}"
echo ""

echo "📖 Documentation:"
echo "   • ${BLUE}ENABLE_KOKORO_TTS.md${NC}         - Quick start (3 steps)"
echo "   • ${BLUE}KOKORO_TTS_SETUP.md${NC}          - Full setup guide"
echo "   • ${BLUE}TTS_QUICK_SWITCH.md${NC}          - Switch between providers"
echo "   • ${BLUE}KOKORO_TTS_IMPLEMENTATION.md${NC} - Technical details"
echo ""

echo "💡 Tips:"
echo "   • First audio generation takes 2-5 seconds (model loading)"
echo "   • Subsequent generations are fast (0.5-2 seconds)"
echo "   • Model is cached in browser (works offline after download)"
echo "   • 28+ voices available with emotion-based selection"
echo "   • To switch back to eSpeak: see TTS_QUICK_SWITCH.md"
echo ""

echo "🎭 Emotional Voices:"
echo "   • Happy/Grateful: af_bella (warm, friendly)"
echo "   • Excited: af_heart (energetic, clear)"
echo "   • Sad: af_sky (soft, gentle)"
echo "   • Neutral: af_heart (default)"
echo ""

echo "🔧 Advanced Configuration:"
echo "   • Faster (lower quality): VITE_KOKORO_DTYPE=q4"
echo "   • Best quality: VITE_KOKORO_DTYPE=fp32"
echo "   • GPU acceleration: VITE_KOKORO_DEVICE=webgpu"
echo "   • Edit: client/.env"
echo ""

echo -e "${GREEN}🎉 Enjoy high-quality audio with Eva AI!${NC}"
echo ""
