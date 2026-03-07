# Eva AI - Python Edition 🤖🎙️

**Emotional Voice Assistant with AI** - A real-time conversational AI with emotional intelligence, voice capabilities, and persistent memory.

This is the Python implementation of Eva AI, converted from the original Node.js version. It uses FastAPI, python-socketio, and async/await for high-performance real-time communication.

## ✨ Features

### 🎭 Emotional Intelligence
- **8 Emotion Types**: Happy, Sad, Anxious, Excited, Angry, Neutral, Confused, Grateful
- **Sentiment Analysis**: Positive, Negative, Neutral
- **Emotion-Aware Responses**: AI adapts tone based on detected emotions
- **Emotional Voice Modulation**: TTS voice selection based on emotion

### 👥 Persona Modes
- **Friend**: Warm, casual, emotionally supportive
- **Mentor**: Encouraging, wise, growth-focused
- **Advisor**: Professional, clear, solution-oriented

### 🧠 Memory System
- **Short-Term Memory**: Last 20 messages per session (in-memory + Redis cache)
- **Long-Term Memory**: Persistent storage (MongoDB or local files)
- **Automatic Memory Saving**: Important moments detected and saved
- **Context-Aware**: Past memories injected into conversations
- **Memory Tags**: Goal, Achievement, Emotional Moment, Important, Casual

### 🎙️ Voice Capabilities
- **Speech-to-Text (STT)**:
  - OpenAI Whisper (cloud, paid)
  - Whisper.cpp (local, free)
  - Groq Whisper API (cloud, free with limits)
- **Text-to-Speech (TTS)**:
  - OpenAI TTS (cloud, paid, 6 voices)
  - Piper (local, free, high quality)
  - eSpeak (local, free, fallback)

### 🤖 Multiple LLM Support
- **OpenAI**: GPT-4 Turbo (paid, cloud)
- **Ollama**: Llama 3.1 (free, local)
- **LM Studio**: Custom models (free, local)
- **Groq**: Llama 3.1 70B (free with limits, cloud)
- **Hugging Face**: Mistral 7B (free with limits, cloud)

### 🛠️ Real-Time Tools
- **Weather**: Current weather, 5-day forecast, weather advice
- **Extensible**: Easy to add new tools

### 💬 Conversation Management
- **Persistent Conversations**: All chats saved (MongoDB or local files)
- **Resume Conversations**: Continue from where you left off
- **Conversation History**: Sidebar with past conversations
- **Search**: Find conversations by content
- **Auto-Titles**: Generated from first message

### 💾 Database Options
- **File-based (JSON)**: Zero setup, perfect for development (default)
- **MongoDB**: Production-ready, scalable, advanced queries
- **Easy switching**: Just change `DB_PROVIDER` in `.env`

## 🏗️ Architecture

### Backend (Python)
```
app/
├── main.py                 # FastAPI + Socket.IO server
├── config/
│   ├── constants.py        # Constants and enums
│   └── database.py         # Database abstraction (MongoDB/File)
├── database/
│   ├── file_db.py          # File-based database implementation
│   └── __init__.py
├── engines/
│   ├── emotion_engine.py   # Emotion detection
│   ├── persona_engine.py   # Persona management
│   ├── memory_engine.py    # Memory system
│   └── tool_engine.py      # Tool integration
├── services/
│   ├── llm_service.py      # LLM abstraction layer
│   ├── stt_service.py      # Speech-to-Text
│   ├── tts_service.py      # Text-to-Speech
│   ├── weather_service.py  # Weather API
│   └── conversation_service.py  # Conversation CRUD
├── models/
│   ├── conversation.py     # Conversation schema
│   └── memory.py           # Memory schema
├── websocket/
│   └── socket_handler.py   # WebSocket event handlers
└── utils/
    ├── logger.py           # Logging configuration
    ├── helpers.py          # Utility functions
    └── conversation_logger.py  # Conversation logging
```

### Frontend (React)
```
client/
├── src/
│   ├── App.jsx             # Main application
│   ├── components/         # React components
│   ├── hooks/              # Custom hooks
│   └── services/           # Socket service
└── package.json
```

## 🚀 Quick Start

### Prerequisites

**Required:**
- **Python 3.9+** (3.12 for audio emotions, 3.14 for run-without-emotions)
- **Node.js 18+** (for frontend)
- **FFmpeg** (for audio conversion)

**Optional:**
- **MongoDB** (or use file-based DB - no setup needed!)
- **Redis** (for caching)
- **Ollama** (for free local LLM)

### Starting with start.sh (recommended)

The easiest way to run Eva AI is the **start script**, which can install dependencies and start both backend and frontend.

From the project root:

```bash
./start.sh
```

With **no arguments**, the script shows an **interactive menu**:

```
╔═══════════════════════════════════════════════════════════╗
║                    Eva AI - Start                         ║
╚═══════════════════════════════════════════════════════════╝

  1) Run only (no audio emotions)     — Python 3.14, venv
  2) Run only (with audio emotions)   — Python 3.12, venv-py312
  3) Install then run (no emotions)   — install.sh + run
  4) Install then run (with emotions) — install.sh + install-audio-emotion.sh + run
  5) Help
  6) Exit

Choose (1-6):
```

#### start.sh — Options and behavior

| Option | Description |
|--------|-------------|
| **1** | Run backend + frontend only, **no** audio emotion detection. Uses **Python 3.14** and `venv`. Sets `AUDIO_EMOTION_ENABLED=false` in `.env`. |
| **2** | Run backend + frontend **with** audio emotion detection. Uses **Python 3.12** and `venv-py312`. Sets `AUDIO_EMOTION_ENABLED=true` in `.env`. Requires `venv-py312` (e.g. from `install-audio-emotion.sh`). |
| **3** | Run `./install.sh` (create venv, install deps, client npm install), then run as in option 1 (no emotions). |
| **4** | Run `./install.sh`, then `./install-audio-emotion.sh` (Python 3.12 venv + audio emotion deps), then run as in option 2 (with emotions). |
| **5** | Show CLI help (same as `./start.sh --help`). |
| **6** | Exit without starting. |

#### start.sh — Command-line flags

You can skip the menu by passing flags:

```bash
./start.sh --help              # Show help and exit
./start.sh --with-emotions     # Run only, with audio emotions (Python 3.12)
./start.sh --no-emotions       # Run only, no emotions (Python 3.14) [default when combined with install]
./start.sh --install           # Install (install.sh) then run without emotions
./start.sh --install -e        # Install (install.sh + install-audio-emotion.sh) then run with emotions
```

| Flag | Short | Meaning |
|------|--------|--------|
| `--install` | `-i` | Run installation before starting. With emotions, also runs `install-audio-emotion.sh`. |
| `--with-emotions` | `-e` | Use **Python 3.12** and `venv-py312`; enable audio emotion detection. |
| `--no-emotions` | `-n` | Use **Python 3.14** and `venv`; disable audio emotion detection. |
| `--help` | `-h` | Print usage and exit. |

#### start.sh — What it does when running

1. **If `--install`** was chosen: runs `./install.sh`, and if emotions are enabled, runs `./install-audio-emotion.sh`.
2. **Checks**: `.env` exists; required venv exists (`venv` or `venv-py312`); optionally warns if MongoDB/Redis are not running.
3. **Updates `.env`**: Sets `AUDIO_EMOTION_ENABLED=true` or `false` according to the chosen mode.
4. **Starts backend**: Activates the correct venv and runs `uvicorn app.main:socket_app --reload --port 3001`.
5. **Starts frontend**: `cd client`, runs `npm install` if needed, then `npm run dev`.
6. **Cleanup**: Ctrl+C stops both backend and frontend.

**URLs when running:**

- Frontend: http://localhost:5173  
- Backend: http://localhost:3001  
- Health: http://localhost:3001/health  

---

### Manual installation (without start.sh)

1. **Navigate to the project**:
```bash
cd /path/to/Project-Eva
```

2. **Run the installation script**:
```bash
./install.sh
```

This will:
- Create a Python virtual environment
- Install all Python dependencies
- Install frontend dependencies
- Create necessary directories
- Copy .env.example to .env

3. **Configure environment variables**:
```bash
# Edit .env file
nano .env

# Required settings:
LLM_PROVIDER=ollama  # or openai, groq, etc.
AUDIO_PROVIDER=local  # or openai
MONGODB_URI=mongodb://localhost:27017/eva-ai

# Add API keys if using cloud services
OPENAI_API_KEY=your_key
GROQ_API_KEY=your_key
OPENWEATHER_API_KEY=your_key
```

4. **Start MongoDB** (if local):
```bash
mongod
```

5. **Start Redis** (optional):
```bash
redis-server
```

6. **Start the backend**:
```bash
source venv/bin/activate
python -m uvicorn app.main:socket_app --reload --port 3001
```

7. **Start the frontend** (in a new terminal):
```bash
cd client
npm run dev
```

8. **Open your browser**:
```
http://localhost:5173
```

## 🔧 Configuration

### LLM Providers

#### Ollama (Local, Free) - Recommended for Development
```bash
# Install Ollama
curl -fsSL https://ollama.com/install.sh | sh

# Pull model
ollama pull llama3.1:8b

# Configure .env
LLM_PROVIDER=ollama
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3.1:8b
```

#### OpenAI (Cloud, Paid)
```bash
# Configure .env
LLM_PROVIDER=openai
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4-turbo-preview
```

#### Groq (Cloud, Free with Limits)
```bash
# Get API key from https://console.groq.com
LLM_PROVIDER=groq
GROQ_API_KEY=gsk_...
GROQ_MODEL=llama-3.1-70b-versatile
```

### Audio Providers

#### Local Audio (Free, Offline) - Recommended
```bash
# Install Whisper.cpp
git clone https://github.com/ggerganov/whisper.cpp
cd whisper.cpp
make
./models/download-ggml-model.sh base.en

# Install Piper TTS
wget https://github.com/rhasspy/piper/releases/download/v1.2.0/piper_amd64.tar.gz
tar -xzf piper_amd64.tar.gz
mv piper /usr/local/bin/

# Configure .env
AUDIO_PROVIDER=local
WHISPER_CPP_PATH=/usr/local/bin/whisper-cli
WHISPER_MODEL=base.en
PIPER_PATH=/usr/local/bin/piper
```

#### OpenAI Audio (Cloud, Paid)
```bash
# Configure .env
AUDIO_PROVIDER=openai
OPENAI_API_KEY=sk-...
```

## 📖 Usage

### Text Chat
1. Type your message in the input box
2. Press Enter or click Send
3. Eva responds with emotion-aware text

### Voice Chat
1. Click the microphone button
2. Speak your message
3. Click again to stop recording
4. Eva transcribes and responds (with voice if enabled)

### Change Persona
- Click the persona selector in the control panel
- Choose: Friend, Mentor, or Advisor

### View Memory Lane
- Click "Memory Lane" in the header
- Browse your conversation memories
- Search, edit, or delete memories

### Conversation History
- View past conversations in the left sidebar
- Click to resume a conversation
- Delete conversations you no longer need
- Collapse sidebar for more space

## 🔌 WebSocket Events

### Client → Server
- `USER_TEXT` - Send text message
- `USER_AUDIO_CHUNK` - Send audio data
- `PERSONA_CHANGED` - Change persona
- `MODE_CHANGED` - Change input/output modes
- `MEMORY_REQUEST` - Request memories
- `CONVERSATIONS_REQUEST` - List conversations
- `CONVERSATION_LOAD` - Load conversation
- `CONVERSATION_DELETE` - Delete conversation

### Server → Client
- `CONNECTION_ESTABLISHED` - Connection successful
- `BOT_TEXT_RESPONSE` - Text response
- `BOT_AUDIO_STREAM` - Audio response
- `TRANSCRIPTION_RESULT` - STT result
- `EMOTION_DETECTED` - Detected emotion
- `TOOL_USED` - Tool executed
- `CONVERSATIONS_LIST` - Conversation list
- `ERROR` - Error occurred

## 🧪 Development

### Run Backend in Development Mode
```bash
source venv/bin/activate
python -m uvicorn app.main:socket_app --reload --port 3001 --log-level debug
```

### Run Frontend in Development Mode
```bash
cd client
npm run dev
```

### Run Tests
```bash
# Backend tests
pytest

# Frontend tests
cd client
npm test
```

### Format Code
```bash
# Python
black app/
flake8 app/

# JavaScript
cd client
npm run lint
```

## 📚 Documentation

- **[API Reference](API_REFERENCE.md)** - API documentation
- **[LLM Service README](../LLM_SERVICE_README.md)** - LLM configuration and usage (if present)
- **[Audio Service README](../AUDIO_SERVICE_README.md)** - Audio setup and configuration (if present)

## 🐛 Troubleshooting

### MongoDB Connection Error
```bash
# Check if MongoDB is running
pgrep mongod

# Start MongoDB
mongod
```

### Redis Connection Warning
```bash
# Redis is optional - the app will work without it
# To enable Redis caching:
redis-server
```

### Audio Not Working
```bash
# Check FFmpeg
ffmpeg -version

# Install FFmpeg
brew install ffmpeg  # macOS
apt-get install ffmpeg  # Linux
```

### Whisper.cpp Not Found
```bash
# Check path
which whisper-cli

# Update .env with correct path
WHISPER_CPP_PATH=/path/to/whisper-cli
```

### Port Already in Use
```bash
# Kill process on port 3001
lsof -ti:3001 | xargs kill -9

# Or use a different port
python -m uvicorn app.main:socket_app --reload --port 3002
```

### venv or venv-py312 not found
```bash
# No emotions (Python 3.14):
./start.sh --install

# With emotions (Python 3.12):
./start.sh --install --with-emotions
```

## 🔐 Security

- **API Keys**: Never commit .env file
- **CORS**: Configure ALLOWED_ORIGINS in .env
- **Session Secret**: Use strong random string
- **Input Sanitization**: All user inputs are sanitized
- **Rate Limiting**: Consider adding rate limiting for production

## 📝 Environment Variables

See `.env.example` for all available configuration options.

**Required:**
- `LLM_PROVIDER` - LLM service to use
- `MONGODB_URI` - MongoDB connection string (or use file DB)

**Optional:**
- `REDIS_URL` - Redis connection (for caching)
- `OPENWEATHER_API_KEY` - Weather functionality
- `AUDIO_PROVIDER` - Audio service to use
- `AUDIO_EMOTION_ENABLED` - Set by start.sh; use `true` for voice emotion detection
- API keys for cloud services

## 🚢 Deployment

### Using Docker (Coming Soon)
```bash
docker-compose up
```

### Manual Deployment
1. Set up MongoDB and Redis
2. Configure production .env
3. Install dependencies
4. Run with gunicorn:
```bash
gunicorn app.main:socket_app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:3001
```

## 🤝 Contributing

This is a conversion of the Node.js Eva AI project. For contributions:
1. Follow Python PEP 8 style guide
2. Add type hints to all functions
3. Write tests for new features
4. Update documentation

## 📄 License

MIT License - see [LICENSE](../LICENSE) in the project root.

## 🙏 Acknowledgments

- Original Node.js implementation
- OpenAI for GPT and Whisper
- Ollama for local LLM support
- FastAPI and python-socketio communities

## 📞 Support

For issues or questions:
1. Check the documentation in `/docs`
2. Review troubleshooting section above
3. Check logs in `/logs` directory

---

**Built with ❤️ using Python, FastAPI, and React**
