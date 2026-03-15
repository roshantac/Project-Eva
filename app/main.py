"""
Eva AI - Emotional Voice Assistant
Python FastAPI Implementation
"""

import os
import sys
import signal
import asyncio
import logging
from pathlib import Path
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import socketio
from dotenv import load_dotenv

# Load .env first, before any app imports that read os.getenv (e.g. audio_emotion_service, tts_service).
# Prefer cwd (where start.sh / uvicorn was started) so we use the correct project .env.
_cwd_env = Path(os.getcwd()) / '.env'
_file_root = Path(__file__).resolve().parent.parent
_file_env = _file_root / '.env'
_env_path = _cwd_env if _cwd_env.exists() else _file_env
# override=True so this project's .env wins over any existing env (e.g. from another directory/shell)
load_dotenv(dotenv_path=_env_path, override=True)

from app.config.database import connect_database, connect_redis, disconnect_databases
from app.config.constants import WebSocketEvents
from app.websocket.socket_handler import SocketHandler
from app.services.llm_service import LLMService
from app.services.stt_service import STTService
from app.services.tts_service import TTSService
from app.services.weather_service import WeatherService
from app.services.audio_emotion_service import audio_emotion_service
from app.engines.emotion_engine import EmotionEngine
from app.engines.persona_engine import PersonaEngine
from app.engines.memory_engine import MemoryEngine
from app.engines.tool_engine import ToolEngine
from app.utils.logger import logger

# Debug (after logger is available)
logger.info(f'🔍 DEBUG: Loaded .env from: {_env_path}')
logger.info(f'🔍 DEBUG: AUDIO_PROVIDER="{os.getenv("AUDIO_PROVIDER", "NOT_SET")}", AUDIO_EMOTION_ENABLED="{os.getenv("AUDIO_EMOTION_ENABLED", "NOT_SET")}"')


def _suppress_cancelled_error_in_uvicorn(record: logging.LogRecord) -> bool:
    """Don't log CancelledError as ERROR during shutdown (Ctrl+C)."""
    if record.levelno != logging.ERROR:
        return True
    if record.exc_info and record.exc_info[0] is not None:
        if record.exc_info[0] is asyncio.CancelledError:
            return False
    return True


# Suppress ERROR traceback for asyncio.CancelledError during lifespan shutdown (Ctrl+C)
logging.getLogger("uvicorn.error").addFilter(_suppress_cancelled_error_in_uvicorn)


def _install_signal_handlers():
    """Install SIGINT/SIGTERM handlers so Ctrl+C stops the server (including with uvicorn --reload)."""
    def shutdown(signum, frame):
        logger.info("Shutting down (Ctrl+C)...")
        sys.exit(0)

    try:
        if hasattr(signal, "SIGINT"):
            signal.signal(signal.SIGINT, shutdown)
        if getattr(signal, "SIGTERM", None) is not None:
            signal.signal(signal.SIGTERM, shutdown)
    except (ValueError, OSError):
        pass  # Ignore if not in main thread or unsupported


_install_signal_handlers()

# Initialize Socket.IO server
sio = socketio.AsyncServer(
    async_mode='asgi',
    cors_allowed_origins=os.getenv('ALLOWED_ORIGINS', 'http://localhost:5173').split(','),
    ping_timeout=20,
    ping_interval=10,
    logger=False,
    engineio_logger=False
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup and shutdown"""
    # Startup
    logger.info("🚀 Starting Eva AI Server...")
    
    # Connect to databases
    await connect_database()  # MongoDB or File-based
    await connect_redis()
    
    # Initialize services
    llm_service = LLMService()
    stt_service = STTService()
    logger.info("🔧 Initializing TTS Service...")
    tts_service = TTSService()
    logger.info(f"✅ TTS Service initialized with provider: {tts_service.provider.name}")
    weather_service = WeatherService()
    
    # Initialize engines
    emotion_engine = EmotionEngine(llm_service, audio_emotion_service)
    persona_engine = PersonaEngine()
    memory_engine = MemoryEngine(llm_service)
    tool_engine = ToolEngine()
    
    # Initialize WebSocket handler
    socket_handler = SocketHandler(
        sio=sio,
        llm_service=llm_service,
        stt_service=stt_service,
        tts_service=tts_service,
        emotion_engine=emotion_engine,
        persona_engine=persona_engine,
        memory_engine=memory_engine,
        tool_engine=tool_engine
    )
    
    # Connect reminder service to socket handler and TTS
    tool_engine.reminder_service.set_services(socket_handler, tts_service)
    
    # Store in app state
    app.state.socket_handler = socket_handler
    app.state.llm_service = llm_service
    
    logger.info(f"✅ Eva AI Server started on port {os.getenv('PORT', 3001)}")
    logger.info(f"🤖 LLM Provider: {os.getenv('LLM_PROVIDER', 'ollama')}")
    logger.info(f"🎤 Audio Provider: {os.getenv('AUDIO_PROVIDER', 'local')}")
    
    yield
    
    # Shutdown
    logger.info("🛑 Shutting down Eva AI Server...")
    await disconnect_databases()
    logger.info("✅ Eva AI Server stopped")


# Create FastAPI app
app = FastAPI(
    title="Eva AI",
    description="Emotional Voice Assistant with AI",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv('ALLOWED_ORIGINS', 'http://localhost:5173').split(','),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount Socket.IO
socket_app = socketio.ASGIApp(sio, app)

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "Eva AI",
        "version": "1.0.0"
    }

# Root endpoint
@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Eva AI Server",
        "version": "1.0.0",
        "status": "running"
    }


if __name__ == "__main__":
    import uvicorn

    port = int(os.getenv("PORT", 3001))
    host = os.getenv("HOST", "0.0.0.0")

    uvicorn.run(
        socket_app,
        host=host,
        port=port,
        log_level="info",
        access_log=True,
    )
