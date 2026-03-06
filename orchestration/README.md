# EVA - Emotional Virtual Assistant

An audio-first agentic AI personal assistant that understands emotions, remembers what matters, and acts proactively.

## 🎯 Overview

EVA is designed to be more than just a voice assistant - it's a companion that:
- **Understands emotions** and adapts its responses accordingly
- **Remembers conversations** and important information
- **Acts proactively** based on your needs and patterns
- **Switches roles** between Friend, Advisor, and Assistant modes
- **Integrates tools** for scheduling, reminders, web search, and more

## 🏗️ Architecture

EVA uses a custom agentic AI architecture with specialized agents:

1. **Audio Correction Agent** - Fixes transcription errors from speech-to-text
2. **Intent Classification Agent** - Understands what you want to accomplish
3. **Emotional Detection Agent** - Detects your emotional state from conversation
4. **Memory Classification Agent** - Determines what to remember (short/long-term)
5. **Conversation Manager Agent** - Generates natural, personality-driven responses
6. **Agent Orchestrator** - Coordinates all agents and manages conversation flow

## 📁 Project Structure

```
project-eva/
├── agents/                      # Agent implementations
│   ├── base_agent.py           # Base agent class
│   ├── audio_correction_agent.py
│   ├── intent_classifier_agent.py
│   ├── emotional_detector_agent.py
│   ├── memory_classifier_agent.py
│   ├── conversation_manager_agent.py
│   └── orchestrator.py         # Agent coordinator
├── tools/                       # Tool integrations
│   ├── memory_tools.py         # Memory storage (dummy)
│   ├── action_tools.py         # Scheduling & actions (dummy)
│   └── web_search_tool.py      # Web search integration
├── prompts/                     # Prompt templates
│   └── system_prompts.py       # All system prompts
├── utils/                       # Utilities
│   ├── logger.py               # Logging system
│   ├── ollama_client.py        # Ollama/LLM integration
│   ├── config_manager.py       # Configuration management
│   └── state_manager.py        # Conversation state
├── config/                      # Configuration files
│   └── config.yaml             # Main configuration
├── tests/                       # Test files
├── main.py                      # Main entry point
└── requirements.txt             # Python dependencies
```

## 🚀 Getting Started

### Prerequisites

1. **Python 3.8+**
2. **Ollama** installed and running locally
   ```bash
   # Install Ollama from https://ollama.ai
   # Pull the Gemma model
   ollama pull gemma:7b
   ```

### Installation

1. Clone the repository:
   ```bash
   cd "Project Eva"
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Verify Ollama is running:
   ```bash
   curl http://localhost:11434/api/tags
   ```

### Running EVA

#### Interactive Mode (for testing)

```bash
python main.py --interactive
```

This launches an interactive chat interface where you can:
- Chat with EVA naturally
- Change roles: "act as my advisor"
- Test memory: "remember that I like coffee"
- Request actions: "remind me to call John tomorrow"
- Check state: type `state`
- Reset conversation: type `reset`

#### Integration with Audio Service

```python
from main import EVA

# Initialize EVA
eva = EVA()

# Process audio input (JSON from your audio service)
audio_json = '{"transcribed_text": "Hey EVA, how are you?"}'
response_json = eva.process_audio_input(audio_json)

# Parse response
import json
response = json.loads(response_json)
print(response["response"])
```

## 🎭 EVA's Personality Modes

EVA can operate in three different roles:

### 1. Friend Mode (Default)
- Casual and conversational
- Emotionally supportive
- Uses friendly language
- Shows genuine interest

**Example:**
```
You: I'm feeling stressed about work
EVA: I hear you - work stress is tough. Want to talk about what's going on?
```

### 2. Advisor Mode
- Thoughtful and analytical
- Provides structured guidance
- Asks clarifying questions
- Offers frameworks for thinking

**Example:**
```
You: Should I take this new job?
EVA: That's a significant decision. Let's think through this systematically. 
     What are the key factors you're considering?
```

### 3. Assistant Mode
- Professional and efficient
- Task-focused
- Clear and concise
- Action-oriented

**Example:**
```
You: Schedule a meeting with the team
EVA: I'll schedule that meeting. What time works best for you?
```

**Switch modes by saying:**
- "Act as my friend"
- "Be my advisor"
- "Switch to assistant mode"

## 🧠 Memory System

EVA has two types of memory:

### Short-Term Memory
- Lasts for current session (24 hours)
- Stores temporary context
- Used for conversation continuity

### Long-Term Memory
- Permanent storage
- Categories: People, Promises, Events, Notes, Goals, Preferences
- Importance-based (1-10 scale)

**Examples:**
```
You: Remember that my sister's birthday is March 15th
EVA: Got it! I'll remember your sister's birthday is March 15th.

You: I prefer morning meetings
EVA: Noted - you prefer morning meetings. I'll keep that in mind.
```

## 🔧 Configuration

Edit `config/config.yaml` to customize:

```yaml
model:
  name: "gemma:7b"              # Change model
  base_url: "http://localhost:11434"
  
agents:
  conversation_manager:
    temperature: 0.7            # Adjust creativity
    max_tokens: 2048
    
conversation:
  default_role: "friend"        # Default personality
  enable_emotional_tracking: true
```

## 🛠️ Tools & Integrations

### Current Tools (Dummy Implementations)

These are placeholder implementations. Your teammates will replace them with actual functionality:

1. **Memory Tools** (`tools/memory_tools.py`)
   - `store_short_term_memory()`
   - `store_long_term_memory()`
   - `retrieve_relevant_memories()`

2. **Action Tools** (`tools/action_tools.py`)
   - `schedule_meeting()`
   - `set_reminder()`
   - `create_task()`
   - `make_call_request()`

3. **Web Search** (`tools/web_search_tool.py`)
   - Uses DuckDuckGo for web search
   - Personalizes results based on user context

### Adding New Tools

1. Create tool in `tools/` directory
2. Import in agent that needs it
3. Call tool from agent's `process()` method

## 📊 Conversation Flow

```
Audio Input (JSON)
    ↓
Audio Correction Agent (fix transcription errors)
    ↓
Intent Classification Agent (understand request)
    ↓
Emotional Detection Agent (detect user's emotion)
    ↓
[Conditional Branches]
    ├─→ Memory Classification (if memory request)
    ├─→ Web Search (if information query)
    └─→ Action Tools (if action request)
    ↓
Conversation Manager Agent (generate response)
    ↓
Update Conversation State
    ↓
JSON Response
```

## 🧪 Testing

### Manual Testing

```bash
# Interactive mode
python main.py --interactive

# Test different scenarios:
# 1. Casual chat
You: Hey, how's it going?

# 2. Memory storage
You: Remember that I have a meeting with John tomorrow at 2pm

# 3. Web search
You: What's the weather like in New York?

# 4. Role change
You: Act as my advisor

# 5. Emotional expression
You: I'm really excited about my new project!
```

### Integration Testing

Create test files in `tests/` directory:

```python
from main import EVA

def test_basic_conversation():
    eva = EVA()
    result = eva.process_text_input("Hello EVA")
    assert result["success"] == True
    assert len(result["response"]) > 0
```

## 📝 API Reference

### EVA Class

#### `process_audio_input(audio_json: str) -> str`
Process audio input from audio service.

**Input:**
```json
{
  "transcribed_text": "user message"
}
```

**Output:**
```json
{
  "success": true,
  "response": "EVA's response",
  "metadata": {
    "intent": "CASUAL_CHAT",
    "emotion": "happy",
    "role": "friend"
  },
  "conversation_id": "conv_user_20240315_143022",
  "current_role": "friend",
  "emotional_state": {
    "emotion": "happy",
    "intensity": 7
  }
}
```

#### `process_text_input(text: str) -> Dict[str, Any]`
Process direct text input (for testing).

#### `get_conversation_state() -> Dict[str, Any]`
Get current conversation state.

#### `reset_conversation() -> None`
Reset conversation state.

## 🔍 Logging

EVA provides detailed logging for debugging:

- **Console**: Colored output for easy reading
- **File**: `logs/eva.log` with full details
- **Agent Decisions**: Track what each agent decides

View logs:
```bash
tail -f logs/eva.log
```

## 🤝 Integration Points

### With Audio Service (Your Teammate)

**Expected Input Format:**
```json
{
  "transcribed_text": "user's spoken message"
}
```

**Your Code:**
```python
# In your audio service
transcribed_text = audio_to_text(audio_data)
input_json = json.dumps({"transcribed_text": transcribed_text})

# Send to EVA
response_json = eva.process_audio_input(input_json)
response = json.loads(response_json)

# Convert response to speech
text_to_speech(response["response"])
```

### With Memory Tools (Your Teammate)

Replace dummy implementations in `tools/memory_tools.py`:

```python
def store_long_term_memory(content, category, importance, metadata):
    # Your actual implementation
    # Store in vector database, etc.
    pass
```

### With Micro-Actions (Your Teammate)

Replace dummy implementations in `tools/action_tools.py`:

```python
def schedule_meeting(title, datetime_str, participants, notes, duration_minutes):
    # Your actual implementation
    # Integrate with calendar API, etc.
    pass
```

## 🐛 Troubleshooting

### Ollama Connection Issues

```bash
# Check if Ollama is running
curl http://localhost:11434/api/tags

# Start Ollama
ollama serve

# Pull model if not available
ollama pull gemma:7b
```

### Import Errors

```bash
# Reinstall dependencies
pip install -r requirements.txt --upgrade
```

### Slow Responses

- Use smaller model: `gemma:2b` instead of `gemma:7b`
- Reduce `max_tokens` in config
- Adjust `temperature` for faster generation

## 📚 Key Features Implemented

✅ Audio transcription correction  
✅ Intent classification (7 intent types)  
✅ Emotional state detection (8 emotions)  
✅ Memory classification (short/long-term)  
✅ Three personality modes (Friend/Advisor/Assistant)  
✅ Web search integration  
✅ Action tools (scheduling, reminders, tasks, calls)  
✅ Conversation state management  
✅ Context-aware responses  
✅ Proactive suggestions  
✅ Natural dialogue flow  

## 🚧 Future Enhancements

- [ ] Voice activity detection
- [ ] Multi-language support
- [ ] Personality customization
- [ ] Advanced memory retrieval (vector search)
- [ ] Calendar integration
- [ ] Email integration
- [ ] Proactive notifications
- [ ] User preference learning
- [ ] Conversation summarization

## 📄 License

This project is part of Project EVA.

## 👥 Team

- **Audio Service**: [Teammate 1]
- **Memory & Micro-Actions**: [Teammate 2]
- **Agentic AI & Prompts**: [You]

---

**Built with ❤️ for natural, emotional, and intelligent conversations**