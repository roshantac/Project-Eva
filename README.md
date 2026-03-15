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

EVA supports both **text** and **voice** input for all commands. Simply type or speak naturally, and EVA will understand your intent.

---

## 🛠️ Tool-Specific Prompts & Examples

### 📅 Calendar Management

**What it does**: Schedule meetings, view your calendar, and manage appointments with intelligent conflict detection.

**Scheduling Meetings:**
```
✅ Text/Voice Prompts:
"Schedule a meeting tomorrow at 3pm"
"Book a meeting called Project Review at 5pm for 2 hours"
"Set up a team standup tomorrow at 10am for 30 minutes"
"Schedule lunch with Sarah next Monday at 1pm"
"Book a dentist appointment on Friday at 2:30pm for 1 hour"
"Create a meeting titled Budget Discussion on March 20th at 4pm"
"Schedule a call with the client at 3:15pm tomorrow"

📝 What EVA extracts:
- Meeting title (defaults to "Meeting" if not specified)
- Date/time (supports relative: tomorrow, next week, etc.)
- Duration (defaults to 1 hour if not specified)
- Automatically detects conflicts with existing meetings
```

**Viewing Calendar:**
```
✅ Text/Voice Prompts:
"What's on my calendar today?"
"Show me today's calendar"
"Get today's schedule"
"What meetings do I have today?"
"Show my calendar for today"
"What's my schedule looking like?"

📝 Response format:
- Lists all meetings for today
- Shows time, title, and duration
- Displays in chronological order
- Indicates if calendar is empty
```

**Listing All Meetings:**
```
✅ Text/Voice Prompts:
"List all my meetings"
"Show all scheduled meetings"
"What meetings do I have scheduled?"
"Show me all upcoming meetings"
"Display my entire calendar"

📝 Response format:
- Groups meetings by date
- Shows past and future meetings
- Includes full details (time, title, duration)
```

---

### ⏰ Reminder Management

**What it does**: Set time-based reminders with voice notifications when they trigger.

**Setting Reminders:**
```
✅ Text/Voice Prompts:
"Remind me to call John in 30 minutes"
"Set a reminder for tomorrow at 9am to check emails"
"Remind me about the meeting at 5pm"
"Remind me to take medicine in 2 hours"
"Set a reminder to submit report by Friday 5pm"
"Remind me to call mom tomorrow at 7pm"
"Set a reminder for next Monday at 10am to review documents"

📝 What EVA extracts:
- Reminder message/task
- Time (relative: "in 30 minutes" or absolute: "tomorrow at 9am")
- Automatically schedules and notifies you
```

**Viewing Reminders:**
```
✅ Text/Voice Prompts:
"Show my reminders"
"What reminders do I have?"
"List all reminders"
"Show upcoming reminders"

📝 Response format:
- Lists all active reminders
- Shows time and message
- Displays in chronological order
```

**Managing Reminders:**
```
✅ Text/Voice Prompts:
"Delete reminder about calling John"
"Remove the 5pm reminder"
"Cancel my medicine reminder"

📝 Features:
- Voice notification when reminder triggers
- Persistent across sessions
- Automatic cleanup of past reminders
```

---

### 📝 Notes & Lists

**What it does**: Save, retrieve, and manage notes, lists, and important information.

**Creating Notes:**
```
✅ Text/Voice Prompts:
"Save a note called grocery list: milk, eggs, bread, cheese"
"Remember that my favorite color is blue"
"Create a note titled meeting notes: discuss budget, review timeline"
"Save a note called passwords: email is abc@example.com"
"Make a note: dentist appointment is on Friday"
"Remember my car license plate is ABC123"

📝 What EVA extracts:
- Note title (optional, auto-generated if not provided)
- Note content
- Automatically formats lists with bullet points
```

**Retrieving Notes:**
```
✅ Text/Voice Prompts:
"What's in my grocery list?"
"Show me my meeting notes"
"Read my passwords note"
"What did I save about my car?"
"Show all my notes"
"List my notes"

📝 Response format:
- Displays note title and content
- Lists formatted with bullet points
- Shows all notes if no specific title mentioned
```

**Updating Notes:**
```
✅ Text/Voice Prompts:
"Update grocery list: add tomatoes and onions"
"Change my meeting notes to include action items"
"Add to my todo list: finish report"

📝 Features:
- Overwrites existing note with same title
- Preserves formatting
- Supports multi-line content
```

---

### 🌤️ Weather Information

**What it does**: Get current weather, forecasts, and weather-based recommendations.

**Current Weather:**
```
✅ Text/Voice Prompts:
"What's the weather in London?"
"How's the weather today?"
"Tell me the weather in New York"
"What's the temperature in Tokyo?"
"Is it hot in Dubai?"
"Weather in San Francisco"

📝 Response includes:
- Current temperature
- Weather conditions (sunny, rainy, cloudy, etc.)
- Humidity and wind speed
- "Feels like" temperature
```

**Weather Forecasts:**
```
✅ Text/Voice Prompts:
"Will it rain tomorrow?"
"What's the weather forecast for this week?"
"Is it going to be sunny on Saturday?"
"Weather forecast for London next week"

📝 Response includes:
- Multi-day forecast
- Temperature highs and lows
- Precipitation chances
- Weather conditions
```

**Weather Advice:**
```
✅ Text/Voice Prompts:
"Should I carry an umbrella?"
"Do I need a jacket today?"
"Is it good weather for a picnic?"
"Should I go for a run outside?"

📝 EVA provides:
- Contextual advice based on weather
- Clothing recommendations
- Activity suggestions
```

---

### 🔍 Web Search

**What it does**: Search the internet for information and get summarized results.

**General Search:**
```
✅ Text/Voice Prompts:
"Search for latest AI news"
"Look up Python tutorials"
"Find information about climate change"
"Search for best restaurants in Paris"
"Look up how to fix a leaky faucet"
"Find the latest iPhone reviews"

📝 Response includes:
- Top search results with titles
- Brief snippets from each result
- Source URLs
- Summarized information
```

**Specific Queries:**
```
✅ Text/Voice Prompts:
"Who won the World Cup 2022?"
"What is the capital of Australia?"
"Search for SpaceX latest launch"
"Find the recipe for chocolate cake"
"Look up symptoms of flu"

📝 Features:
- Real-time web search
- Summarized answers
- Multiple sources
- Relevant snippets
```

---

### 💭 Memory Lane

**What it does**: Store and recall important personal memories and information.

**Storing Memories:**
```
✅ Text/Voice Prompts:
"Remember that I love Italian food"
"Save to memory: my anniversary is on June 15th"
"Remember my wife's favorite flower is roses"
"Store this memory: I graduated from MIT in 2020"
"Remember that I'm allergic to peanuts"

📝 What EVA stores:
- Personal preferences
- Important dates
- Facts about you
- Relationships and connections
```

**Recalling Memories:**
```
✅ Text/Voice Prompts:
"What do you remember about me?"
"Tell me what you know about my preferences"
"What's my anniversary date?"
"Do you remember my favorite food?"
"Show me my memories"

📝 Response includes:
- Relevant stored memories
- Contextual information
- Chronological history
```

---

## 🎭 Persona Switching

Choose from different AI personalities to match your needs:

**Available Personas:**

1. **Professional** 👔
   - Formal, business-oriented responses
   - Concise and to-the-point
   - Best for: Work meetings, professional emails, business planning

2. **Friendly** 😊
   - Casual, warm, and approachable
   - Conversational and empathetic
   - Best for: Daily conversations, personal tasks, casual planning

3. **Creative** 🎨
   - Imaginative and expressive
   - Storytelling and brainstorming
   - Best for: Creative projects, ideation, artistic discussions

**Switching Personas:**
```
Use the persona selector in the UI to switch between personalities.
EVA will adjust its tone, vocabulary, and response style accordingly.
```

---

## 💬 Natural Conversation

**EVA understands context and natural language:**

```
✅ You can ask follow-up questions:
You: "What's the weather in London?"
EVA: "It's 15°C and partly cloudy in London..."
You: "Should I bring an umbrella?"
EVA: "Based on the forecast, there's a 30% chance of rain..."

✅ You can combine multiple requests:
"Schedule a meeting tomorrow at 3pm and remind me 30 minutes before"
"Search for Italian restaurants and save the best one to my notes"

✅ You can be conversational:
"Hey, what's up?" → EVA responds naturally
"I'm feeling stressed" → EVA detects emotion and responds empathetically
"Tell me a joke" → EVA entertains you
```

---

## 🎤 Voice vs Text Input

**Both work identically!**

- **Voice**: Click the microphone button and speak naturally
- **Text**: Type your message in the chat box

EVA processes both the same way, so use whichever is more convenient for you.

**Voice Tips:**
- Speak clearly and at a normal pace
- Use natural language (no need for robotic commands)
- EVA detects emotion in your voice and responds accordingly
- Works in noisy environments with good microphone

**Text Tips:**
- Type naturally as you would in a conversation
- No special syntax required
- Supports emojis and casual language
- Great for detailed information or when in quiet environments

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
