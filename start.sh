#!/bin/bash

# Eva AI - Startup Script
# Options: install or run only; with or without audio emotions mode
# - With emotions: Python 3.12 (venv-py312)
# - Without emotions: Python 3.14 (venv)

set -e

# Defaults
DO_INSTALL=false
WITH_EMOTIONS=false
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
        --help|-h)
            echo "Eva AI - Start client and server"
            echo ""
            echo "Usage: ./start.sh [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --install, -i       Run installation before starting (install.sh; with-emotions also runs install-audio-emotion.sh)"
            echo "  --with-emotions, -e Run with audio emotion detection (Python 3.12, venv-py312)"
            echo "  --no-emotions, -n   Run without audio emotion detection (Python 3.14, venv) [default]"
            echo "  --help, -h          Show this help"
            echo ""
            echo "Examples:"
            echo "  ./start.sh                      # Show interactive menu"
            echo "  ./start.sh --with-emotions      # Run only, with emotions (Python 3.12)"
            echo "  ./start.sh --install            # Install then run (no emotions)"
            echo "  ./start.sh --install -e         # Install (including audio emotion) then run with emotions"
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
    echo "  1) Run only (no audio emotions)     — Python 3.14, venv"
    echo "  2) Run only (with audio emotions)   — Python 3.12, venv-py312"
    echo "  3) Install then run (no emotions)   — install.sh + run"
    echo "  4) Install then run (with emotions) — install.sh + install-audio-emotion.sh + run"
    echo "  5) Help"
    echo "  6) Exit"
    echo ""
    read -p "Choose (1-6): " CHOICE
    echo ""

    case $CHOICE in
        1)
            DO_INSTALL=false
            WITH_EMOTIONS=false
            ;;
        2)
            DO_INSTALL=false
            WITH_EMOTIONS=true
            ;;
        3)
            DO_INSTALL=true
            WITH_EMOTIONS=false
            ;;
        4)
            DO_INSTALL=true
            WITH_EMOTIONS=true
            ;;
        5)
            ./start.sh --help
            exit 0
            ;;
        6)
            echo "Bye."
            exit 0
            ;;
        *)
            echo "Invalid choice. Exiting."
            exit 1
            ;;
    esac
fi

# If run mode still not set (e.g. only --install was passed), default to no-emotions
if [ "$RUN_MODE_SET" = false ]; then
    WITH_EMOTIONS=false
fi

echo "🚀 Eva AI"
echo "   Mode: $([ "$WITH_EMOTIONS" = true ] && echo 'with audio emotions (Python 3.12)' || echo 'without audio emotions (Python 3.14)')"
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

    echo "✅ Installation complete"
    echo ""
fi

# --- Pre-run checks ---
if [ ! -f ".env" ]; then
    echo "❌ .env not found. Run with --install or copy .env.example to .env"
    exit 1
fi

# Choose venv and set .env for emotions
if [ "$WITH_EMOTIONS" = true ]; then
    if [ ! -d "venv-py312" ]; then
        echo "❌ venv-py312 not found. Run: ./start.sh --install --with-emotions"
        exit 1
    fi
    VENV_ACTIVATE="venv-py312/bin/activate"
    # Ensure audio emotion enabled in .env
    if grep -q "AUDIO_EMOTION_ENABLED=" .env; then
        sed -i.bak 's/AUDIO_EMOTION_ENABLED=.*/AUDIO_EMOTION_ENABLED=true/' .env
    else
        echo "AUDIO_EMOTION_ENABLED=true" >> .env
    fi
    rm -f .env.bak
else
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

# Cleanup on exit
cleanup() {
    echo ""
    echo "🛑 Shutting down Eva AI..."
    kill $BACKEND_PID 2>/dev/null || true
    kill $FRONTEND_PID 2>/dev/null || true
    echo "✅ Shutdown complete"
    exit 0
}
trap cleanup SIGINT SIGTERM

# --- Start backend ---
echo "🔧 Starting backend ($([ "$WITH_EMOTIONS" = true ] && echo 'Python 3.12, emotions ON' || echo 'Python 3.14, emotions OFF'))..."
source "$VENV_ACTIVATE"
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
echo "✅ Eva AI is running!"
echo "========================================"
echo ""
echo "🌐 Frontend: http://localhost:5173"
echo "🔌 Backend:  http://localhost:3001"
echo "📊 Health:   http://localhost:3001/health"
echo "🎤 Audio emotions: $([ "$WITH_EMOTIONS" = true ] && echo 'enabled' || echo 'disabled')"
echo ""
echo "Press Ctrl+C to stop all servers"
echo ""

wait
