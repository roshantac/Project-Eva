"""
Eva AI - Emotional Voice Assistant
Python FastAPI Implementation
"""

import os
import sys
import signal
import asyncio
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import socketio
from dotenv import load_dotenv

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

# Load environment variables
load_dotenv()


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
    tts_service = TTSService()
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
