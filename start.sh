#!/bin/bash

# Eva AI - Startup Script
# Options: install or run only; with or without audio emotions mode
# - With emotions OR Kokoro-82M: Python 3.12 (venv-py312)
# - Basic mode (no emotions, no Kokoro): Python 3.14 (venv)
# - MAX MODE: Emotions + Kokoro-82M (Python 3.12, best quality)

set -e

# Defaults
DO_INSTALL=false
WITH_EMOTIONS=false
WITH_KOKORO=false
RUN_MODE_SET=false
SHOW_MENU=false

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --install|-i)
            DO_INSTALL=true
            shift
            ;;
        --with-emotions|--emotions|-e)
            WITH_EMOTIONS=true
            RUN_MODE_SET=true
            shift
            ;;
        --no-emotions|-n)
            WITH_EMOTIONS=false
            RUN_MODE_SET=true
            shift
            ;;
        --with-kokoro|--kokoro|-k)
            WITH_KOKORO=true
            shift
            ;;
        --help|-h)
            echo "Eva AI - Start client and server"
            echo ""
            echo "Usage: ./start.sh [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --install, -i       Run installation before starting (install.sh; with-emotions also runs install-audio-emotion.sh)"
            echo "  --with-emotions, -e Run with audio emotion detection (Python 3.12, venv-py312)"
            echo "  --no-emotions, -n   Run without audio emotion detection (Python 3.14, venv) [default]"
            echo "  --with-kokoro, -k   Install Kokoro-82M TTS (high-quality local Python TTS)"
            echo "  --help, -h          Show this help"
            echo ""
            echo "Examples:"
            echo "  ./start.sh                      # Show interactive menu (option 3 = MAX MODE)"
            echo "  ./start.sh --with-emotions      # Run only, with emotions (Python 3.12)"
            echo "  ./start.sh -e -k                # Run MAX MODE: emotions + Kokoro-82M (best quality)"
            echo "  ./start.sh --install            # Install then run (no emotions)"
            echo "  ./start.sh --install -e         # Install (including audio emotion) then run with emotions"
            echo "  ./start.sh --install -k         # Install with Kokoro-82M local TTS"
            echo "  ./start.sh --install -e -k      # Install with emotions and Kokoro-82M TTS (full setup)"
            exit 0
            ;;
        *)
            echo "Unknown option: $1 (use --help)"
            exit 1
            ;;
    esac
done

# No args: show interactive menu
if [ "$RUN_MODE_SET" = false ] && [ "$DO_INSTALL" = false ]; then
    SHOW_MENU=true
fi

if [ "$SHOW_MENU" = true ]; then
    echo ""
    echo "╔═══════════════════════════════════════════════════════════╗"
    echo "║                    Eva AI - Start                         ║"
    echo "╚═══════════════════════════════════════════════════════════╝"
    echo ""
    echo "  1) Run only (basic mode)            — Python 3.14, no emotions"
    echo "  2) Run only (with audio emotions)   — Python 3.12, venv-py312"
    echo "  3) Run MAX MODE (all features)      — Emotions + Kokoro-82M TTS (best quality)"
    echo "  4) Install then run (no emotions)   — install.sh + run"
    echo "  5) Install then run (with emotions) — install.sh + install-audio-emotion.sh + run"
    echo "  6) Install Kokoro-82M TTS (local)   — install-kokoro-local.sh + run"
    echo "  7) Install ALL (emotions + Kokoro)  — Full setup with best features"
    echo "  8) Install MAX MODE then run         — Full install + run in MAX MODE ⭐"
    echo "  9) Help"
    echo " 10) Exit"
    echo ""
    read -p "Choose (1-10): " CHOICE
    echo ""

    case $CHOICE in
        1)
            DO_INSTALL=false
            WITH_EMOTIONS=false
            WITH_KOKORO=false
            RUN_MODE_SET=true
            ;;
        2)
            DO_INSTALL=false
            WITH_EMOTIONS=true
            WITH_KOKORO=false
            RUN_MODE_SET=true
            ;;
        3)
            # MAX MODE - Run with all features (no install)
            DO_INSTALL=false
            WITH_EMOTIONS=true
            WITH_KOKORO=true
            RUN_MODE_SET=true
            echo "🚀 MAX MODE: Running with emotions + Kokoro-82M TTS"
            ;;
        4)
            DO_INSTALL=true
            WITH_EMOTIONS=false
            WITH_KOKORO=false
            RUN_MODE_SET=true
            ;;
        5)
            DO_INSTALL=true
            WITH_EMOTIONS=true
            WITH_KOKORO=false
            RUN_MODE_SET=true
            ;;
        6)
            DO_INSTALL=true
            WITH_EMOTIONS=false
            WITH_KOKORO=true
            RUN_MODE_SET=true
            ;;
        7)
            DO_INSTALL=true
            WITH_EMOTIONS=true
            WITH_KOKORO=true
            RUN_MODE_SET=true
            ;;
        8)
            # MAX MODE install - full install then run with emotions + Kokoro
            DO_INSTALL=true
            WITH_EMOTIONS=true
            WITH_KOKORO=true
            RUN_MODE_SET=true
            echo "🚀 MAX MODE install: Installing all components, then running with emotions + Kokoro-82M TTS"
            ;;
        9)
            ./start.sh --help
            exit 0
            ;;
        10)
            echo "Bye."
            exit 0
            ;;
        *)
            echo "Invalid choice. Exiting."
            exit 1
            ;;
    esac
fi

# If run mode still not set (e.g. only --install was passed, no menu), default to no-emotions
if [ "$RUN_MODE_SET" = false ]; then
    WITH_EMOTIONS=false
fi

echo "🚀 Eva AI"
# Determine Python version based on features
if [ "$WITH_EMOTIONS" = true ] || [ "$WITH_KOKORO" = true ]; then
    PYTHON_VERSION="Python 3.12"
else
    PYTHON_VERSION="Python 3.14"
fi

# Display mode
if [ "$WITH_EMOTIONS" = true ] && [ "$WITH_KOKORO" = true ]; then
    echo "   Mode: MAX MODE - Emotions + Kokoro-82M ($PYTHON_VERSION)"
elif [ "$WITH_EMOTIONS" = true ]; then
    echo "   Mode: with audio emotions ($PYTHON_VERSION)"
elif [ "$WITH_KOKORO" = true ]; then
    echo "   Mode: with Kokoro-82M TTS ($PYTHON_VERSION)"
else
    echo "   Mode: basic ($PYTHON_VERSION)"
fi
echo "   Install: $DO_INSTALL"
echo ""

# --- Installation phase ---
if [ "$DO_INSTALL" = true ]; then
    echo "========================================"
    echo "📦 Installation phase"
    echo "========================================"
    echo ""

    if [ ! -f "install.sh" ]; then
        echo "❌ install.sh not found"
        exit 1
    fi
    ./install.sh
    echo ""

    if [ "$WITH_EMOTIONS" = true ]; then
        echo "========================================"
        echo "🎤 Audio emotion installation"
        echo "========================================"
        echo ""
        if [ -f "install-audio-emotion.sh" ]; then
            ./install-audio-emotion.sh
        else
            echo "⚠️  install-audio-emotion.sh not found, skipping audio emotion install"
        fi
        echo ""
    fi

    if [ "$WITH_KOKORO" = true ]; then
        echo "========================================"
        echo "🎤 Kokoro-82M Local TTS installation"
        echo "========================================"
        echo ""
        if [ -f "install-kokoro-local.sh" ]; then
            ./install-kokoro-local.sh
        else
            echo "⚠️  install-kokoro-local.sh not found, skipping Kokoro TTS install"
        fi
        echo ""
    fi

    echo "✅ Installation complete"
    echo ""
fi

# --- Pre-run checks ---
if [ ! -f ".env" ]; then
    echo "❌ .env not found. Run with --install or copy .env.example to .env"
    exit 1
fi

# Choose venv and set .env for emotions
# Note: Kokoro-82M also requires Python 3.12 (venv-py312)
if [ "$WITH_EMOTIONS" = true ] || [ "$WITH_KOKORO" = true ]; then
    if [ ! -d "venv-py312" ]; then
        echo "❌ venv-py312 not found. Run: ./start.sh --install --with-emotions"
        exit 1
    fi
    VENV_ACTIVATE="venv-py312/bin/activate"
    
    # Set audio emotion based on WITH_EMOTIONS flag
    if [ "$WITH_EMOTIONS" = true ]; then
        # Ensure audio emotion enabled in .env
        if grep -q "AUDIO_EMOTION_ENABLED=" .env; then
            sed -i.bak 's/AUDIO_EMOTION_ENABLED=.*/AUDIO_EMOTION_ENABLED=true/' .env
        else
            echo "AUDIO_EMOTION_ENABLED=true" >> .env
        fi
        rm -f .env.bak
    else
        # Kokoro without emotions - disable audio emotion detection
        if grep -q "AUDIO_EMOTION_ENABLED=" .env; then
            sed -i.bak 's/AUDIO_EMOTION_ENABLED=.*/AUDIO_EMOTION_ENABLED=false/' .env
        else
            echo "AUDIO_EMOTION_ENABLED=false" >> .env
        fi
        rm -f .env.bak
    fi
else
    # Basic mode - Python 3.14
    if [ ! -d "venv" ]; then
        echo "❌ venv not found. Run: ./start.sh --install"
        exit 1
    fi
    VENV_ACTIVATE="venv/bin/activate"
    # Ensure audio emotion disabled in .env
    if grep -q "AUDIO_EMOTION_ENABLED=" .env; then
        sed -i.bak 's/AUDIO_EMOTION_ENABLED=.*/AUDIO_EMOTION_ENABLED=false/' .env
    else
        echo "AUDIO_EMOTION_ENABLED=false" >> .env
    fi
    rm -f .env.bak
fi

# Ensure Kokoro is configured if WITH_KOKORO is true
if [ "$WITH_KOKORO" = true ]; then
    echo "🔧 Verifying Kokoro-82M configuration..."
    
    # Check if AUDIO_PROVIDER is set to kokoro
    if ! grep -q "^AUDIO_PROVIDER=kokoro" .env; then
        echo "   Setting AUDIO_PROVIDER=kokoro in .env"
        if grep -q "^AUDIO_PROVIDER=" .env; then
            sed -i.bak 's/^AUDIO_PROVIDER=.*/AUDIO_PROVIDER=kokoro/' .env
        else
            echo "AUDIO_PROVIDER=kokoro" >> .env
        fi
        rm -f .env.bak
    fi
    
    # Verify kokoro package is installed in the active venv
    source "$VENV_ACTIVATE"
    if ! python -c "import kokoro" 2>/dev/null; then
        echo "⚠️  Kokoro package not found. Installing..."
        pip install -q "kokoro>=0.9.4" soundfile
        echo "✅ Kokoro installed"
    else
        echo "✅ Kokoro-82M is configured and installed"
    fi
    deactivate
    echo ""
fi

# Check and start Ollama if using ollama provider
LLM_PROVIDER=$(grep "^LLM_PROVIDER=" .env | cut -d'=' -f2)
if [ "$LLM_PROVIDER" = "ollama" ]; then
    echo "🔧 Checking Ollama server..."
    if ! pgrep -x "ollama" > /dev/null 2>&1; then
        echo "   Starting Ollama server..."
        if command -v ollama &> /dev/null; then
            nohup ollama serve > /tmp/ollama.log 2>&1 &
            sleep 2
            if pgrep -x "ollama" > /dev/null 2>&1; then
                echo "✅ Ollama server started"
            else
                echo "⚠️  Failed to start Ollama automatically"
                echo "   Please run 'ollama serve' in a separate terminal"
            fi
        else
            echo "⚠️  Ollama not installed. Run: ./install-ollama.sh"
        fi
    else
        echo "✅ Ollama server is already running"
    fi
    echo ""
fi

# Optional: MongoDB
if ! pgrep -x "mongod" > /dev/null 2>&1; then
    echo "⚠️  MongoDB is not running (optional). Start with: mongod --fork --logpath /tmp/mongodb.log"
fi

# Optional: Redis
if ! pgrep -x "redis-server" > /dev/null 2>&1; then
    echo "⚠️  Redis is not running (optional)"
fi

echo "✅ Prerequisites checked"
echo ""

# Cleanup on exit - kill backend (reloader + worker), frontend, and anything on port 3001
cleanup() {
    echo ""
    echo "🛑 Shutting down Eva AI..."
    kill $BACKEND_PID 2>/dev/null || true
    kill $FRONTEND_PID 2>/dev/null || true
    sleep 1
    # Uvicorn --reload leaves a worker holding port 3001; ensure it's freed
    if command -v lsof >/dev/null 2>&1; then
        lsof -ti:3001 | xargs kill -9 2>/dev/null || true
    fi
    pkill -9 -f "uvicorn.*3001" 2>/dev/null || true
    sleep 1
    echo "✅ Shutdown complete"
    exit 0
}
trap cleanup SIGINT SIGTERM

# --- Start backend ---
echo "🔧 Starting backend ($([ "$WITH_EMOTIONS" = true ] && echo 'Python 3.12, emotions ON' || echo 'Python 3.14, emotions OFF'))..."
source "$VENV_ACTIVATE"
# Export key .env vars so the backend always sees them
if [ "$WITH_EMOTIONS" = true ]; then
    export AUDIO_EMOTION_ENABLED=true
fi
if [ "$WITH_KOKORO" = true ]; then
    export AUDIO_PROVIDER=kokoro
fi
# Force .env on disk to match selected mode (backend loads this file with override=True)
if [ "$WITH_EMOTIONS" = true ] && [ -f ".env" ]; then
    sed -i.bak 's/^AUDIO_EMOTION_ENABLED=.*/AUDIO_EMOTION_ENABLED=true/' .env
    rm -f .env.bak
fi
if [ "$WITH_KOKORO" = true ] && [ -f ".env" ]; then
    sed -i.bak 's/^AUDIO_PROVIDER=.*/AUDIO_PROVIDER=kokoro/' .env
    rm -f .env.bak
fi
python -m uvicorn app.main:socket_app --reload --port 3001 &
BACKEND_PID=$!
echo "✅ Backend started (PID: $BACKEND_PID)"
echo ""

sleep 3

# --- Start frontend ---
echo "🔧 Starting frontend..."
cd client
if [ ! -d "node_modules" ]; then
    echo "   Installing client dependencies..."
    npm install
fi
npm run dev &
FRONTEND_PID=$!
cd ..
echo "✅ Frontend started (PID: $FRONTEND_PID)"
echo ""

echo "========================================"
if [ "$WITH_EMOTIONS" = true ] && [ "$WITH_KOKORO" = true ]; then
    echo "✅ Eva AI is running in MAX MODE! 🚀"
    echo "   (Audio Emotions + Kokoro-82M TTS)"
else
    echo "✅ Eva AI is running!"
fi
echo "========================================"
echo ""
echo "🌐 Frontend: http://localhost:5173"
echo "🔌 Backend:  http://localhost:3001"
echo "📊 Health:   http://localhost:3001/health"
echo "🎤 Audio emotions: $([ "$WITH_EMOTIONS" = true ] && echo 'enabled' || echo 'disabled')"
if [ -f "client/.env" ] && grep -q "VITE_TTS_PROVIDER=kokoro" client/.env; then
    echo "🎵 TTS: Kokoro (browser-based)"
elif grep -q "AUDIO_PROVIDER=kokoro" .env; then
    echo "🎵 TTS: Kokoro-82M (local Python, high-quality)"
else
    echo "🎵 TTS: eSpeak (server-side)"
fi
echo ""
echo "Press Ctrl+C to stop all servers"
echo ""

wait
