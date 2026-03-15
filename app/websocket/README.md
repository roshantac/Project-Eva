# WebSocket Module

## Overview
This module provides real-time WebSocket communication for Eva AI using python-socketio.

## Files
- `socket_handler.py` - Main WebSocket handler implementation
- `__init__.py` - Module initialization

## socket_handler.py

### Classes

#### SessionData
Data structure for managing active user sessions.

**Attributes:**
- `session_id: str` - Unique session identifier
- `user_id: str` - User identifier
- `persona: str` - Current persona (friend/mentor/advisor)
- `input_mode: str` - Input mode (text/voice)
- `output_mode: str` - Output mode (text/voice)
- `audio_disabled: bool` - Audio feature flag
- `is_processing: bool` - Processing state flag
- `conversation_created: bool` - Conversation creation flag

#### SocketHandler
Main handler for WebSocket connections and events.

**Constructor Parameters:**
- `sio: socketio.AsyncServer` - Socket.IO server instance
- `llm_service: LLMService` - LLM service for AI responses
- `stt_service: STTService` - Speech-to-text service
- `tts_service: TTSService` - Text-to-speech service
- `emotion_engine: EmotionEngine` - Emotion detection engine
- `persona_engine: PersonaEngine` - Persona management engine
- `memory_engine: MemoryEngine` - Memory operations engine
- `tool_engine: ToolEngine` - Tool execution engine

**Attributes:**
- `active_sessions: Dict[str, SessionData]` - Active sessions by socket ID
- `audio_buffers: Dict[str, List[bytes]]` - Audio buffers by socket ID
- `audio_enabled: bool` - Whether audio features are available

### Event Handlers

#### Connection Events
- `handle_connection(sid, environ)` - Initialize session
- `handle_disconnect(sid)` - Cleanup session

#### User Input Events
- `handle_user_text(sid, data)` - Process text input
- `handle_user_audio_chunk(sid, data)` - Buffer audio chunks
- `process_audio_buffer(sid)` - Transcribe and process audio

#### Configuration Events
- `handle_persona_change(sid, data)` - Change persona
- `handle_mode_change(sid, data)` - Change input/output modes

#### Memory Events
- `handle_memory_request(sid, data)` - Retrieve memories
- `handle_memory_add(sid, data)` - Add memory
- `handle_memory_update(sid, data)` - Update memory
- `handle_memory_delete(sid, data)` - Delete memory

#### Conversation Events
- `handle_conversations_request(sid, data)` - List conversations
- `handle_conversation_load(sid, data)` - Load conversation
- `handle_conversation_delete(sid, data)` - Delete conversation

#### Audio Control Events
- `handle_stop_audio(sid)` - Stop audio playback

### Core Methods

#### generate_response(session, user_message, emotion_data, tool_result)
Generate AI response with full context.

**Process:**
1. Generate emotional context
2. Get persona system prompt
3. Retrieve conversation history
4. Get relevant memories
5. Format tool results if any
6. Build message array
7. Call LLM service
8. Return response

**Returns:** `str` - Generated response text

#### generate_and_stream_audio(sid, text, emotion)
Generate and stream audio response.

**Process:**
1. Check audio enabled
2. Generate emotional speech
3. Split into 4096-byte chunks
4. Emit chunks with isLast flag

**Returns:** `None` (streams via WebSocket)

### Utility Methods

#### _check_audio_enabled()
Check if audio features are available.

**Returns:** `bool` - True if OpenAI API key is configured

#### _register_handlers()
Register all Socket.IO event handlers using decorators.

**Returns:** `None`

#### get_active_sessions_count()
Get count of active sessions.

**Returns:** `int` - Number of active sessions

## Usage

### Initialization
```python
from app.websocket.socket_handler import SocketHandler

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
```

Event handlers are automatically registered on initialization.

### Get Active Sessions
```python
count = socket_handler.get_active_sessions_count()
print(f"Active sessions: {count}")
```

## Event Flow

### Text Input Flow
```
Client: USER_TEXT
  ↓
Server: PROCESSING_START
  ↓
Server: EMOTION_DETECTED
  ↓
Server: TOOL_USED (optional)
  ↓
Server: BOT_TEXT_RESPONSE
  ↓
Server: BOT_AUDIO_STREAM (if voice mode)
  ↓
Server: PROCESSING_END
```

### Audio Input Flow
```
Client: USER_AUDIO_CHUNK (multiple)
  ↓
Client: USER_AUDIO_CHUNK (isFinal=true)
  ↓
Server: PROCESSING_START
  ↓
Server: TRANSCRIPTION_RESULT
  ↓
(Then follows text input flow)
```

### Connection Flow
```
Client: connect
  ↓
Server: Check for active conversation
  ↓
Server: Resume or create session
  ↓
Server: Initialize memory
  ↓
Server: CONNECTION_ESTABLISHED
```

### Disconnect Flow
```
Client: disconnect
  ↓
Server: Get session data
  ↓
Server: End/delete conversation
  ↓
Server: Log session end
  ↓
Server: Cleanup session and buffers
```

## Error Handling

All methods use try-catch blocks with:
1. Error logging
2. ERROR event emission to client
3. Processing state reset
4. Graceful degradation

**Example:**
```python
try:
    # ... operation ...
except Exception as error:
    logger.error(f"Error handling user text: {error}")
    await self.sio.emit(
        WebSocketEvents.ERROR,
        {
            'message': 'Failed to process your message',
            'error': str(error)
        },
        to=sid
    )
    session = self.active_sessions.get(sid)
    if session:
        session.is_processing = False
```

## Audio Handling

### Input
- Supports base64 and binary formats
- Buffers chunks until isFinal=true
- Validates chunk size and format
- Transcribes using STT service

### Output
- Generates emotional speech
- Streams in 4096-byte chunks
- Respects audioDisabled flag
- Only in voice output mode

## Logging

### Console Logging
```
═══════════════════════════════════════════════════════
💬 USER TEXT: "Hello Eva"
═══════════════════════════════════════════════════════

───────────────────────────────────────────────────────
🤖 EVA RESPONSE: "Hi there! How can I help you?"
   Emotion: happy | Persona: friend
───────────────────────────────────────────────────────
```

### File Logging
- Session events to `logs/conversations/conversation-YYYY-MM-DD.log`
- All events to `logs/combined.log`
- Errors to `logs/error.log`

## Dependencies

### Required Services
- LLMService - AI response generation
- STTService - Audio transcription (optional)
- TTSService - Speech synthesis (optional)
- ConversationService - Database operations

### Required Engines
- EmotionEngine - Emotion detection
- PersonaEngine - Persona management
- MemoryEngine - Memory operations
- ToolEngine - Tool execution

### Required Utilities
- helpers - Sanitization and validation
- logger - Structured logging
- conversation_logger - Event logging

## Configuration

### Environment Variables
- `OPENAI_API_KEY` - Required for audio features
- `LOG_CONVERSATIONS` - Enable conversation logging (default: true)
- `ALLOWED_ORIGINS` - CORS origins for Socket.IO

### Audio Settings
- Chunk size: 4096 bytes
- Validation: Minimum 100 bytes per chunk
- Formats: WebM, WAV, MP3, base64

### Processing Settings
- Max tokens: 500 (for responses)
- Temperature: 0.8 (for responses)
- Context: 10 messages + 3 memories

## Type Safety

All methods have complete type hints:
```python
async def handle_user_text(self, sid: str, data: dict):
async def generate_response(
    self,
    session: SessionData,
    user_message: str,
    emotion_data: Dict[str, Any],
    tool_result: Dict[str, Any]
) -> str:
async def handle_memory_request(self, sid: str, data: dict):
```

## Testing

### Manual Testing
```python
# Start server
python app/main.py

# Connect with Socket.IO client
# Send test events
# Verify responses
```

### Automated Testing
```python
import pytest
from app.websocket.socket_handler import SocketHandler

@pytest.mark.asyncio
async def test_handle_user_text():
    # Test implementation
    pass
```

## Troubleshooting

### Import Errors
- Ensure virtual environment is activated
- Install dependencies: `pip install -r requirements.txt`

### Connection Errors
- Check CORS origins configuration
- Verify Socket.IO server is running
- Check client connection URL

### Audio Errors
- Verify OpenAI API key is set
- Check audio provider configuration
- Validate audio format

### Database Errors
- Check MongoDB connection
- Verify database credentials
- Check network connectivity

## Performance Tips

1. **Session Cleanup**: Sessions are automatically cleaned up on disconnect
2. **Audio Buffers**: Cleared immediately after processing
3. **Processing State**: Prevents concurrent processing per session
4. **Memory Context**: Limited to 3 most relevant memories
5. **Conversation History**: Limited to last 10 messages

## Maintenance

### Adding New Event Handlers
1. Add event constant to `WebSocketEvents`
2. Add handler method to `SocketHandler`
3. Register in `_register_handlers()`
4. Add error handling
5. Add logging
6. Update documentation

### Modifying Event Flow
1. Update handler method
2. Maintain error handling
3. Update logging
4. Update documentation
5. Test thoroughly

## Version History

- **v1.0.0** (2026-03-07) - Initial Python conversion from Node.js
  - All event handlers implemented
  - Complete functional parity
  - Full type safety
  - Comprehensive documentation
