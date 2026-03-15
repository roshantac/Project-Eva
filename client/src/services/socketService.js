import { io } from 'socket.io-client';

class SocketService {
  constructor() {
    this.socket = null;
    this.listeners = new Map();
  }

  connect(serverUrl = 'http://localhost:3001', userId = 'anonymous') {
    if (this.socket?.connected) {
      return this.socket;
    }

    this.socket = io(serverUrl, {
      query: { userId },
      transports: ['websocket', 'polling'],
      reconnection: true,
      reconnectionDelay: 1000,
      reconnectionDelayMax: 5000,
      reconnectionAttempts: 5
    });

    this.socket.on('connect', () => {
      console.log('✅ Connected to Eva AI server');
    });

    this.socket.on('disconnect', (reason) => {
      console.log('❌ Disconnected from server:', reason);
    });

    this.socket.on('connect_error', (error) => {
      console.error('Connection error:', error);
    });

    // Debug: Log all incoming events
    this.socket.onAny((eventName, ...args) => {
      console.log(`📥 Received event: ${eventName}`, args);
    });

    return this.socket;
  }

  disconnect() {
    if (this.socket) {
      this.socket.disconnect();
      this.socket = null;
    }
  }

  on(event, callback) {
    if (!this.socket) {
      console.warn(`Socket not initialized for event: ${event}`);
      return;
    }

    // Wrap callback to add logging
    const wrappedCallback = (...args) => {
      callback(...args);
    };
    
    this.socket.on(event, wrappedCallback);
    
    if (!this.listeners.has(event)) {
      this.listeners.set(event, []);
    }
    this.listeners.get(event).push({ original: callback, wrapped: wrappedCallback });
  }

  off(event, callback) {
    if (!this.socket) return;
    
    if (this.listeners.has(event)) {
      const callbacks = this.listeners.get(event);
      const entry = callbacks.find(e => e.original === callback);
      if (entry) {
        this.socket.off(event, entry.wrapped);
        const index = callbacks.indexOf(entry);
        callbacks.splice(index, 1);
      }
    }
  }

  emit(event, data) {
    if (!this.socket) {
      console.warn('Socket not connected');
      return;
    }

    console.log(`📤 Emitting event: ${event}`, data);
    this.socket.emit(event, data);
  }

  sendTextMessage(message) {
    this.emit('USER_TEXT', { message });
  }

  sendAudioChunk(audioData, isFinal = false) {
    this.emit('USER_AUDIO_CHUNK', { 
      audio: audioData,
      isFinal 
    });
  }

  changePersona(persona) {
    this.emit('PERSONA_CHANGED', { persona });
  }

  changeMode(inputMode, outputMode, audioDisabled) {
    this.emit('MODE_CHANGED', { 
      inputMode, 
      outputMode, 
      audioDisabled 
    });
  }

  requestMemories(limit = 50) {
    this.emit('MEMORY_REQUEST', { limit });
  }

  addMemory(memoryData) {
    this.emit('MEMORY_ADD', memoryData);
  }

  updateMemory(memoryId, updates) {
    this.emit('MEMORY_UPDATE', { memoryId, updates });
  }

  deleteMemory(memoryId) {
    this.emit('MEMORY_DELETE', { memoryId });
  }

  stopAudio() {
    this.emit('STOP_AUDIO');
  }

  isConnected() {
    return this.socket?.connected || false;
  }

  getSocket() {
    return this.socket;
  }
}

export default new SocketService();
