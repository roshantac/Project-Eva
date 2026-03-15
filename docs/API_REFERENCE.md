# Eva AI - API Reference

Complete reference for Eva AI WebSocket API and HTTP endpoints.

## HTTP Endpoints

### Health Check
```http
GET /health
```

**Response:**
```json
{
  "status": "healthy",
  "service": "Eva AI",
  "version": "1.0.0"
}
```

### Root
```http
GET /
```

**Response:**
```json
{
  "message": "Eva AI Server",
  "version": "1.0.0",
  "status": "running"
}
```

## WebSocket Connection

### Connect
```javascript
import io from 'socket.io-client';

const socket = io('http://localhost:3001', {
  query: { userId: 'user_001' },
  transports: ['websocket', 'polling']
});
```

### Connection Event
```javascript
socket.on('CONNECTION_ESTABLISHED', (data) => {
  console.log('Connected:', data);
  // data = { sessionId, userId, isResumed }
});
```

## WebSocket Events

### Client → Server

#### USER_TEXT
Send a text message to Eva.

**Payload:**
```typescript
{
  message: string  // User's text message
}
```

**Example:**
```javascript
socket.emit('USER_TEXT', { message: 'Hello Eva!' });
```

---

#### USER_AUDIO_CHUNK
Send audio data for transcription.

**Payload:**
```typescript
{
  audio: string | ArrayBuffer,  // Audio data (base64 or binary)
  isFinal: boolean              // True when recording stops
}
```

**Example:**
```javascript
// Streaming chunks
socket.emit('USER_AUDIO_CHUNK', { 
  audio: audioChunk, 
  isFinal: false 
});

// Final chunk
socket.emit('USER_AUDIO_CHUNK', { 
  audio: lastChunk, 
  isFinal: true 
});
```

---

#### PERSONA_CHANGED
Change Eva's personality mode.

**Payload:**
```typescript
{
  persona: 'friend' | 'mentor' | 'advisor'
}
```

**Example:**
```javascript
socket.emit('PERSONA_CHANGED', { persona: 'mentor' });
```

---

#### MODE_CHANGED
Change input/output communication modes.

**Payload:**
```typescript
{
  inputMode: 'text' | 'voice',
  outputMode: 'text' | 'voice',
  audioDisabled: boolean
}
```

**Example:**
```javascript
socket.emit('MODE_CHANGED', { 
  inputMode: 'voice', 
  outputMode: 'voice',
  audioDisabled: false
});
```

---

#### MEMORY_REQUEST
Request user's long-term memories.

**Payload:**
```typescript
{
  limit?: number  // Max memories to return (default: 50)
}
```

**Example:**
```javascript
socket.emit('MEMORY_REQUEST', { limit: 20 });
```

---

#### MEMORY_ADD
Add a new memory manually.

**Payload:**
```typescript
{
  title: string,
  content: string,
  tags: string[],      // ['goal', 'achievement', etc.]
  importance: number   // 0-10
}
```

**Example:**
```javascript
socket.emit('MEMORY_ADD', {
  title: 'Career Goal',
  content: 'Want to become a senior developer',
  tags: ['goal'],
  importance: 9
});
```

---

#### MEMORY_UPDATE
Update an existing memory.

**Payload:**
```typescript
{
  memoryId: string,
  updates: {
    title?: string,
    content?: string,
    tags?: string[],
    importance?: number
  }
}
```

**Example:**
```javascript
socket.emit('MEMORY_UPDATE', {
  memoryId: '507f1f77bcf86cd799439011',
  updates: { importance: 10 }
});
```

---

#### MEMORY_DELETE
Delete a memory.

**Payload:**
```typescript
{
  memoryId: string
}
```

**Example:**
```javascript
socket.emit('MEMORY_DELETE', { memoryId: '507f1f77bcf86cd799439011' });
```

---

#### CONVERSATIONS_REQUEST
Request list of user's conversations.

**Payload:**
```typescript
{
  limit?: number  // Max conversations to return (default: 50)
}
```

**Example:**
```javascript
socket.emit('CONVERSATIONS_REQUEST', { limit: 20 });
```

---

#### CONVERSATION_LOAD
Load a specific conversation.

**Payload:**
```typescript
{
  sessionId: string
}
```

**Example:**
```javascript
socket.emit('CONVERSATION_LOAD', { sessionId: 'abc-123-def-456' });
```

---

#### CONVERSATION_DELETE
Delete a conversation.

**Payload:**
```typescript
{
  sessionId: string
}
```

**Example:**
```javascript
socket.emit('CONVERSATION_DELETE', { sessionId: 'abc-123-def-456' });
```

---

#### STOP_AUDIO
Stop audio playback.

**Payload:**
```typescript
{}
```

**Example:**
```javascript
socket.emit('STOP_AUDIO');
```

---

### Server → Client

#### CONNECTION_ESTABLISHED
Sent when client connects successfully.

**Payload:**
```typescript
{
  sessionId: string,
  userId: string,
  isResumed: boolean  // True if resuming existing conversation
}
```

---

#### BOT_TEXT_RESPONSE
Eva's text response.

**Payload:**
```typescript
{
  text: string,
  emotion: string,
  persona: string
}
```

---

#### BOT_AUDIO_STREAM
Eva's audio response (streamed in chunks).

**Payload:**
```typescript
{
  audio: ArrayBuffer,  // Audio chunk
  isLast: boolean      // True for final chunk
}
```

---

#### TRANSCRIPTION_RESULT
Result of speech-to-text transcription.

**Payload:**
```typescript
{
  text: string  // Transcribed text
}
```

---

#### EMOTION_DETECTED
Detected emotion from user input.

**Payload:**
```typescript
{
  emotion: string,      // 'happy', 'sad', etc.
  sentiment: string,    // 'positive', 'negative', 'neutral'
  confidence: number,   // 0-1
  intensity: string,    // 'low', 'medium', 'high'
  details?: object
}
```

---

#### TOOL_USED
Notification that a tool was executed.

**Payload:**
```typescript
{
  toolName: string,
  result: object
}
```

---

#### MEMORY_DATA
List of user's memories.

**Payload:**
```typescript
{
  memories: Array<{
    _id: string,
    title: string,
    content: string,
    summary: string,
    emotion: string,
    sentiment: string,
    tags: string[],
    importance: number,
    context: object,
    metadata: {
      createdAt: string,
      accessCount: number
    }
  }>
}
```

---

#### MEMORY_UPDATED
Confirmation of memory operation.

**Payload:**
```typescript
{
  action: 'added' | 'updated' | 'deleted',
  memory?: object,
  memoryId?: string
}
```

---

#### CONVERSATIONS_LIST
List of user's conversations.

**Payload:**
```typescript
{
  conversations: Array<{
    sessionId: string,
    title: string,
    messageCount: number,
    persona: string,
    lastMessageAt: string,
    createdAt: string,
    isActive: boolean
  }>
}
```

---

#### CONVERSATION_LOADED
Loaded conversation with messages.

**Payload:**
```typescript
{
  sessionId: string,
  messages: Array<{
    role: string,
    content: string,
    isTranscribed: boolean,
    emotion?: string,
    persona?: string,
    timestamp: string
  }>
}
```

---

#### CONVERSATION_DELETED
Confirmation of conversation deletion.

**Payload:**
```typescript
{
  sessionId: string
}
```

---

#### PROCESSING_START
Eva started processing your message.

**Payload:**
```typescript
{}
```

---

#### PROCESSING_END
Eva finished processing.

**Payload:**
```typescript
{}
```

---

#### ERROR
An error occurred.

**Payload:**
```typescript
{
  message: string,
  error?: string
}
```

---

## Data Models

### Emotion Data
```typescript
{
  emotion: 'happy' | 'sad' | 'anxious' | 'excited' | 'angry' | 'neutral' | 'confused' | 'grateful',
  sentiment: 'positive' | 'negative' | 'neutral',
  confidence: number,  // 0-1
  intensity: 'low' | 'medium' | 'high',
  details?: {
    reasoning: string
  }
}
```

### Message
```typescript
{
  role: 'user' | 'assistant',
  content: string,
  isTranscribed: boolean,
  emotion?: string,
  persona?: string,
  timestamp: string  // ISO 8601
}
```

### Memory
```typescript
{
  _id: string,
  sessionId: string,
  userId: string,
  title: string,
  content: string,
  summary: string,
  emotion: string,
  sentiment: 'positive' | 'negative' | 'neutral',
  tags: ('goal' | 'achievement' | 'emotional_moment' | 'important' | 'casual')[],
  importance: number,  // 0-10
  context: {
    persona: string,
    relatedTopics: string[],
    conversationSnippet: string
  },
  metadata: {
    createdAt: string,
    updatedAt: string,
    accessCount: number,
    lastAccessed?: string
  }
}
```

### Conversation
```typescript
{
  sessionId: string,
  userId: string,
  title: string,
  messages: Message[],
  persona: string,
  isActive: boolean,
  lastMessageAt: string,
  createdAt: string,
  updatedAt: string
}
```

## Usage Examples

### Complete Chat Flow

```javascript
import io from 'socket.io-client';

const socket = io('http://localhost:3001', {
  query: { userId: 'user_001' }
});

// Wait for connection
socket.on('CONNECTION_ESTABLISHED', (data) => {
  console.log('Session:', data.sessionId);
  
  // Send message
  socket.emit('USER_TEXT', { message: 'Hello!' });
});

// Handle response
socket.on('BOT_TEXT_RESPONSE', (data) => {
  console.log('Eva:', data.text);
  console.log('Emotion:', data.emotion);
});

// Handle emotion
socket.on('EMOTION_DETECTED', (data) => {
  console.log('Your emotion:', data.emotion);
});

// Handle errors
socket.on('ERROR', (data) => {
  console.error('Error:', data.message);
});
```

### Voice Chat Flow

```javascript
// Start recording
const mediaRecorder = new MediaRecorder(stream);

mediaRecorder.ondataavailable = (event) => {
  socket.emit('USER_AUDIO_CHUNK', {
    audio: event.data,
    isFinal: false
  });
};

// Stop recording
mediaRecorder.stop();
socket.emit('USER_AUDIO_CHUNK', {
  audio: finalChunk,
  isFinal: true
});

// Handle transcription
socket.on('TRANSCRIPTION_RESULT', (data) => {
  console.log('You said:', data.text);
});

// Handle audio response
socket.on('BOT_AUDIO_STREAM', (data) => {
  // Play audio chunk
  audioPlayer.play(data.audio);
  
  if (data.isLast) {
    console.log('Audio complete');
  }
});
```

### Memory Management

```javascript
// Request memories
socket.emit('MEMORY_REQUEST', { limit: 10 });

// Handle memories
socket.on('MEMORY_DATA', (data) => {
  data.memories.forEach(memory => {
    console.log(memory.title, memory.importance);
  });
});

// Add memory
socket.emit('MEMORY_ADD', {
  title: 'Important Goal',
  content: 'Learn Python',
  tags: ['goal'],
  importance: 8
});

// Update memory
socket.emit('MEMORY_UPDATE', {
  memoryId: 'abc123',
  updates: { importance: 10 }
});

// Delete memory
socket.emit('MEMORY_DELETE', { memoryId: 'abc123' });
```

### Conversation History

```javascript
// List conversations
socket.emit('CONVERSATIONS_REQUEST', { limit: 20 });

// Handle list
socket.on('CONVERSATIONS_LIST', (data) => {
  data.conversations.forEach(conv => {
    console.log(conv.title, conv.messageCount);
  });
});

// Load conversation
socket.emit('CONVERSATION_LOAD', { sessionId: 'abc-123' });

// Handle loaded conversation
socket.on('CONVERSATION_LOADED', (data) => {
  console.log('Loaded:', data.messages.length, 'messages');
  data.messages.forEach(msg => {
    console.log(msg.role, msg.content);
  });
});

// Delete conversation
socket.emit('CONVERSATION_DELETE', { sessionId: 'abc-123' });
```

## Rate Limits

When using cloud providers, be aware of rate limits:

- **OpenAI**: Varies by tier
- **Groq**: 30 requests/minute (free tier)
- **Hugging Face**: Varies by model

## Error Codes

| Error | Description | Solution |
|-------|-------------|----------|
| `Connection failed` | Cannot connect to server | Check server is running |
| `Session not found` | Invalid session ID | Reconnect to get new session |
| `LLM provider error` | LLM API failed | Check API key and provider status |
| `Audio transcription failed` | STT error | Check audio format and provider |
| `Tool execution failed` | Tool error | Check tool parameters |
| `Database error` | MongoDB/Redis error | Check database connections |

## Best Practices

1. **Always handle errors**: Listen for ERROR events
2. **Check connection**: Verify CONNECTION_ESTABLISHED before sending
3. **Cleanup on disconnect**: Remove listeners when done
4. **Validate input**: Sanitize user input before sending
5. **Handle audio properly**: Send isFinal=true when recording stops
6. **Respect rate limits**: Don't spam requests
7. **Use appropriate personas**: Match persona to use case

## Python SDK Example

For Python clients:

```python
import socketio

sio = socketio.AsyncClient()

@sio.event
async def connect():
    print('Connected')
    await sio.emit('USER_TEXT', {'message': 'Hello!'})

@sio.event
async def BOT_TEXT_RESPONSE(data):
    print(f"Eva: {data['text']}")

@sio.event
async def disconnect():
    print('Disconnected')

# Connect
await sio.connect('http://localhost:3001', 
                  socketio_path='/socket.io',
                  transports=['websocket'])

# Keep alive
await sio.wait()
```

---

For more examples, see the React frontend implementation in `client/src/`.
