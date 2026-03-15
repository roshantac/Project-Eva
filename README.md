# EVA - Emotional Voice Assistant 🤖🎙️

EVA is an intelligent, emotion-aware voice assistant that combines natural language processing, emotion detection, and voice synthesis to create a more human-like conversational experience. Built with Python (FastAPI) backend and React frontend, EVA can understand context, remember conversations, and respond with appropriate emotional tones.

## 👥 Developers
- **Muhammed Roshan P**
- **Tushar Gupta**
- **Athvaith**

## Architecture Diagram
<img width="1523" height="1071" alt="image" src="https://github.com/user-attachments/assets/eb79e02e-e52b-4c20-a680-f26d89ea52e6" />

## ✨ Features

### 🎯 Core Capabilities
- **Voice Interaction**: Speak naturally with EVA using voice input and receive voice responses
- **Text Chat**: Type messages for text-based conversations
- **Emotion Detection**: Analyzes emotional tone in both text and audio
- **Contextual Memory**: Remembers past conversations and user preferences
- **Multiple Personas**: Switch between different AI personalities (Professional, Friendly, Creative)

### 🛠️ Smart Tools
- **📅 Calendar Management**: Schedule meetings, view today's calendar, list all meetings
- **⏰ Reminders**: Set time-based reminders with voice notifications
- **📝 Notes**: Save, retrieve, and manage notes and lists
- **🌤️ Weather**: Get current weather, forecasts, and weather-based advice
- **🔍 Web Search**: Search the internet for information
- **💭 Memory Lane**: Store and recall important memories

### 🎨 Advanced Features
- **Multi-Provider Support**: Works with OpenAI, Ollama, Groq, and more
- **Flexible Audio**: Local TTS or cloud-based (OpenAI)
- **Real-time Communication**: WebSocket-based for instant responses
- **Conversation History**: Browse and resume past conversations
- **Emotion-Aware Responses**: Adjusts tone and voice based on detected emotions

## 🚀 Quick Start

### Prerequisites
- Python 3.11 or 3.12 (for audio emotion detection) or Python 3.14+ (without audio emotions)
- Node.js 16+ and npm
- Ollama (for local LLM) or OpenAI API key (optional)
- FFmpeg (for audio conversion)

### Easy Installation & Startup

EVA provides an interactive startup script that handles everything:

```bash
# Make the script executable (first time only)
chmod +x start.sh

# Run the interactive menu
./start.sh
```

**Interactive Menu Options:**
1. **Run only (no audio emotions)** - Quick start with Python 3.14
2. **Run only (with audio emotions)** - Start with Python 3.12 + emotion detection
3. **Install then run (no emotions)** - Full setup + start
4. **Install then run (with emotions)** - Full setup with audio emotions + start

### Command Line Options

```bash
# Quick start (no installation)
./start.sh

# Install and run without audio emotions
./start.sh --install

# Install and run with audio emotions (Python 3.12)
./start.sh --install --with-emotions

# Run with audio emotions (already installed)
./start.sh --with-emotions

# Show help
./start.sh --help
```

### Manual Installation (Alternative)

If you prefer manual setup:

1. **Clone the repository**
```bash
git clone https://github.com/yourusername/eva-ai.git
cd eva-ai
```

2. **Run installation script**
```bash
./install.sh
```

3. **Install Ollama (for local LLM)**
```bash
./install-ollama.sh
```

4. **Configure environment**
```bash
cp .env.example .env
# Edit .env and add your API keys (optional)
```

5. **Start EVA**
```bash
./start.sh
```

### Access EVA
- **Frontend**: http://localhost:5173
- **Backend API**: http://localhost:3001
- **Health Check**: http://localhost:3001/health

## ⚙️ Configuration

### Environment Variables

Create a `.env` file in the root directory:

```bash
# Server Configuration
PORT=3001
HOST=0.0.0.0
ALLOWED_ORIGINS=http://localhost:5173

# Database (file-based by default)
DB_PROVIDER=file

# LLM Provider (choose one)
LLM_PROVIDER=ollama
# LLM_PROVIDER=openai
# LLM_PROVIDER=groq

# OpenAI Configuration (if using OpenAI)
# OPENAI_API_KEY=your_openai_api_key_here
# OPENAI_MODEL=gpt-4-turbo-preview

# Groq Configuration (if using Groq)
# GROQ_API_KEY=your_groq_api_key_here
# GROQ_MODEL=mixtral-8x7b-32768

# Ollama Configuration (local)
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama2

# Audio Provider
AUDIO_PROVIDER=local
# AUDIO_PROVIDER=openai

# Weather API (optional)
# OPENWEATHER_API_KEY=your_openweather_api_key_here

# Search API (optional)
# SERPAPI_KEY=your_serpapi_key_here
```

### Provider Options

#### LLM Providers
- **Ollama** (Local, Free): Best for privacy and offline use
- **OpenAI** (Cloud, Paid): Best quality and features
- **Groq** (Cloud, Free tier): Fast inference
- **LM Studio** (Local, Free): Alternative local option

#### Audio Providers
- **Local** (Free): Uses system TTS, works offline
- **OpenAI** (Paid): High-quality voice synthesis

## 📖 Usage Guide

### Voice Commands

#### Calendar Management
```
"Schedule a meeting tomorrow at 3pm"
"Book a meeting called Project Review at 5pm for 2 hours"
"What's on my calendar today?"
"List all my meetings"
"Show all scheduled meetings"
```

#### Reminders
```
"Remind me to call John in 30 minutes"
"Set a reminder for tomorrow at 9am to check emails"
"Remind me about the meeting at 5pm"
```

#### Notes
```
"Save a note called grocery list: milk, eggs, bread"
"Remember that my favorite color is blue"
"What's in my grocery list?"
"Show me all my notes"
```

#### Weather
```
"What's the weather in London?"
"Will it rain tomorrow?"
"Should I carry an umbrella?"
```

#### Web Search
```
"Search for latest AI news"
"Look up Python tutorials"
"Find information about climate change"
```

### Text Chat

Simply type your message in the chat interface. EVA understands natural language and will respond appropriately.

### Persona Switching

Choose from different AI personalities:
- **Professional**: Formal, business-oriented responses
- **Friendly**: Casual, warm, and approachable
- **Creative**: Imaginative and expressive

## 🏗️ Project Structure

```
eva-ai/
├── app/                      # Backend application
│   ├── config/              # Configuration files
│   ├── database/            # Database handlers
│   ├── engines/             # Core engines (emotion, memory, tools)
│   ├── models/              # Data models
│   ├── services/            # Business logic services
│   │   ├── calendar_service.py
│   │   ├── reminder_service.py
│   │   ├── notes_service.py
│   │   ├── llm_service.py
│   │   ├── tts_service.py
│   │   └── stt_service.py
│   ├── websocket/           # WebSocket handlers
│   └── main.py              # Application entry point
├── client/                   # Frontend React application
│   ├── src/
│   │   ├── components/      # React components
│   │   ├── hooks/           # Custom React hooks
│   │   └── services/        # API services
│   └── public/              # Static assets
├── data/                     # User data storage
├── docs/                     # Documentation
├── logs/                     # Application logs
├── .env.example             # Environment template
├── .gitignore               # Git ignore rules
├── requirements.txt         # Python dependencies
├── package.json             # Node.js dependencies
└── README.md                # This file
```

## 🔧 Development

### Running Tests
```bash
# Test calendar service
python test_calendar_service.py

# Test LLM service
python test_llm_service.py

# Test audio services
python test_audio_services.py
```

### Adding New Features

1. **New Service**: Create in `app/services/`
2. **New Tool**: Add to `app/engines/tool_engine.py`
3. **New API Endpoint**: Add to `app/main.py`
4. **Frontend Component**: Add to `client/src/components/`

## 📚 Documentation

- [Calendar Feature Guide](docs/CALENDAR_FEATURE.md)
- [API Reference](docs/API_REFERENCE.md)
- [Project Details](docs/PROJECT.md)
- [Implementation Guide](IMPLEMENTATION_EVA.md)

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 🐛 Troubleshooting

### Common Issues

**Issue**: "Module not found" errors
```bash
# Solution: Reinstall dependencies
pip install -r requirements.txt
cd client && npm install
```

**Issue**: Ollama connection failed
```bash
# Solution: Make sure Ollama is running
ollama serve
```

**Issue**: Audio not working
```bash
# Solution: Check audio provider configuration in .env
AUDIO_PROVIDER=local  # or openai
```

**Issue**: Port already in use
```bash
# Solution: Change port in .env
PORT=3002
```

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- OpenAI for GPT models and TTS
- Ollama for local LLM support
- FastAPI for the excellent web framework
- React for the frontend framework

## 📧 Contact

For questions or support, please open an issue on GitHub.

---

**Made with ❤️ by the EVA Team**

## 👥 Development Team
- **Muhammed Roshan P** - Core Development
- **Tushar Gupta** - Core Development
- **Athvaith** - Core Development

## 🎯 Roadmap

- [ ] Multi-language support
- [ ] Mobile app (React Native)
- [ ] Voice cloning
- [ ] Custom wake word
- [ ] Integration with smart home devices
- [ ] Calendar sync with Google/Outlook
- [ ] Team collaboration features
- [ ] Plugin system for extensions

## ⭐ Star History

If you find EVA useful, please consider giving it a star on GitHub!
