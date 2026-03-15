import React, { useState, useEffect, useRef, useCallback } from 'react';
import { Brain, MessageCircle, Clock, Wifi, WifiOff } from 'lucide-react';
import { useSocket, useSocketEvent } from './hooks/useSocket';
import { useAudioRecorder } from './hooks/useAudioRecorder';
import { useAudioPlayer } from './hooks/useAudioPlayer';
import ChatMessage from './components/ChatMessage';
import ChatInput from './components/ChatInput';
import ControlPanel from './components/ControlPanel';
import MemoryLane from './components/MemoryLane';
import ConversationSidebar from './components/ConversationSidebar';
import './App.css';

function App() {
  const [messages, setMessages] = useState([]);
  const [currentEmotion, setCurrentEmotion] = useState('neutral');
  const [persona, setPersona] = useState('friend');
  const [inputMode, setInputMode] = useState('text');
  // When Audio Output is enabled, use voice output so server sends both text + audio
  const [outputMode, setOutputMode] = useState('voice');
  const [audioDisabled, setAudioDisabled] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  const [isTranscribing, setIsTranscribing] = useState(false);
  const [processingStatus, setProcessingStatus] = useState('');
  const [activeView, setActiveView] = useState('chat');
  const [notification, setNotification] = useState(null);
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const [recordingDuration, setRecordingDuration] = useState(0);

  const messagesEndRef = useRef(null);
  const recordingTimerRef = useRef(null);
  const { isConnected, sessionId, socket } = useSocket('http://localhost:3001', 'user_001');
  const { isRecording, audioLevel, startRecording, stopRecording } = useAudioRecorder();
  const { isPlaying, queueAudioChunk, stopAudio } = useAudioPlayer();

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const showNotification = useCallback((message, type = 'info') => {
    setNotification({ message, type });
    setTimeout(() => setNotification(null), 3000);
  }, []);

  useSocketEvent('PROCESSING_START', useCallback(() => {
    setIsProcessing(true);
    setProcessingStatus('Processing your message...');
  }, []));

  useSocketEvent('PROCESSING_END', useCallback(() => {
    setIsProcessing(false);
    setProcessingStatus('');
  }, []));

  useSocketEvent('EMOTION_DETECTED', useCallback((data) => {
    setCurrentEmotion(data.emotion);
    if (isProcessing) {
      setProcessingStatus('Generating response...');
    }
  }, [isProcessing]));

  useSocketEvent('BOT_TEXT_RESPONSE', useCallback((data) => {
    setMessages(prev => [...prev, {
      text: data.text,
      isUser: false,
      emotion: data.emotion,
      persona: data.persona,
      timestamp: new Date()
    }]);
    setIsProcessing(false);
    setProcessingStatus('');
  }, []));

  useSocketEvent('BOT_AUDIO_STREAM', useCallback((data) => {
    console.log('🔊 BOT_AUDIO_STREAM received:', {
      hasAudio: !!data.audio,
      format: data.format,
      isLast: data.isLast,
      audioDisabled,
      outputMode,
      audioType: typeof data.audio,
      audioLength: data.audio?.length || 0
    });

    if (!audioDisabled && outputMode === 'voice') {
      try {
        // Handle base64-encoded audio
        if (data.format === 'base64') {
          console.log('📦 Decoding base64 audio...');
          // Decode base64 to binary
          const binaryString = atob(data.audio);
          const bytes = new Uint8Array(binaryString.length);
          for (let i = 0; i < binaryString.length; i++) {
            bytes[i] = binaryString.charCodeAt(i);
          }
          
          // Detect audio format from magic bytes
          let mimeType = 'audio/mpeg'; // default
          if (bytes[0] === 0x52 && bytes[1] === 0x49 && bytes[2] === 0x46 && bytes[3] === 0x46) {
            mimeType = 'audio/wav'; // WAV file
            console.log('🎵 Detected WAV format');
          } else if (bytes[0] === 0xFF && (bytes[1] & 0xE0) === 0xE0) {
            mimeType = 'audio/mpeg'; // MP3 file
            console.log('🎵 Detected MP3 format');
          }
          
          // Create a Blob from the binary data
          const audioBlob = new Blob([bytes], { type: mimeType });
          console.log('✅ Audio blob created:', audioBlob.size, 'bytes, type:', mimeType);
          queueAudioChunk(audioBlob);
        } else {
          // Fallback for raw binary data
          console.log('📦 Using raw binary audio data');
          queueAudioChunk(data.audio);
        }
      } catch (error) {
        console.error('❌ Error processing audio stream:', error);
        console.error('Error stack:', error.stack);
      }
    } else {
      console.log('⏭️ Skipping audio playback (audioDisabled:', audioDisabled, ', outputMode:', outputMode, ')');
    }
  }, [audioDisabled, outputMode, queueAudioChunk]));

  useSocketEvent('TRANSCRIPTION_RESULT', useCallback((data) => {
    setIsTranscribing(false);
    // Empty audio: no speech detected, don't add message or continue processing
    if (data.empty || !(data.text || '').trim()) {
      setIsProcessing(false);
      setProcessingStatus('');
      showNotification('No speech detected', 'info');
      return;
    }
    setIsProcessing(true); // Start processing after transcription
    setProcessingStatus('Analyzing emotion...');
    
    // Add transcribed text as a user message in the chat
    setMessages(prev => {
      // Check if this message already exists (prevent duplicates)
      const isDuplicate = prev.some(msg => 
        msg.text === data.text && 
        msg.isUser && 
        msg.isTranscribed &&
        (Date.now() - new Date(msg.timestamp).getTime()) < 2000 // Within 2 seconds
      );
      
      if (isDuplicate) {
        console.log('⚠️ Duplicate transcription detected, skipping');
        return prev;
      }
      
      return [...prev, {
        text: data.text,
        isUser: true,
        isTranscribed: true,
        timestamp: new Date()
      }];
    });
    
    showNotification(`✓ Transcribed`, 'success');
  }, [showNotification]));

  useSocketEvent('TOOL_USED', useCallback((data) => {
    setProcessingStatus(`Using ${data.toolName}...`);
    showNotification(`Using ${data.toolName}...`, 'info');
  }, [showNotification]));

  useSocketEvent('ERROR', useCallback((data) => {
    showNotification(data.message, 'error');
    setIsProcessing(false);
    setIsTranscribing(false);
    setProcessingStatus('');
  }, [showNotification]));

  useSocketEvent('CONNECTION_ESTABLISHED', useCallback((data) => {
    // Set audio availability based on server capabilities
    const serverAudioEnabled = data.audioEnabled !== false;
    if (data.audioEnabled !== undefined) {
      setAudioDisabled(!data.audioEnabled);
      if (data.audioEnabled) {
        showNotification(`Audio enabled (${data.audioProvider || 'local'})`, 'success');
      }
    }
    // When audio is enabled, use voice output so server sends both text + audio
    const outMode = serverAudioEnabled ? 'voice' : 'text';
    setOutputMode(outMode);
    if (socket) {
      socket.changeMode(inputMode, outMode, !serverAudioEnabled);
    }
    // If resuming an existing conversation, load its messages
    if (data.isResumed && socket) {
      socket.emit('CONVERSATION_LOAD', { sessionId: data.sessionId });
    }
  }, [socket, showNotification, inputMode]));

  useSocketEvent('CONVERSATION_LOADED', useCallback((data) => {
    // Clear current messages and load conversation history
    const formattedMessages = data.messages.map(msg => ({
      text: msg.content,
      isUser: msg.role === 'user',
      isTranscribed: msg.isTranscribed,
      emotion: msg.emotion,
      persona: msg.persona,
      timestamp: new Date(msg.timestamp)
    }));
    setMessages(formattedMessages);
    if (formattedMessages.length > 0) {
      showNotification('Conversation resumed', 'success');
    }
  }, [showNotification]));

  const handleSendMessage = useCallback((message) => {
    if (!socket || !message.trim()) return;

    setMessages(prev => [...prev, {
      text: message,
      isUser: true,
      timestamp: new Date()
    }]);

    setIsProcessing(true); // Start processing
    socket.sendTextMessage(message);
  }, [socket]);

  const handleStartRecording = useCallback(async () => {
    const success = await startRecording((audioData, isFinal) => {
      // Send every chunk as it comes in (like Node.js version)
      if (socket && audioData) {
        const reader = new FileReader();
        reader.onload = () => {
          // Convert ArrayBuffer to base64 for reliable transmission
          const arrayBuffer = reader.result;
          const bytes = new Uint8Array(arrayBuffer);
          let binary = '';
          for (let i = 0; i < bytes.byteLength; i++) {
            binary += String.fromCharCode(bytes[i]);
          }
          const base64 = btoa(binary);
          console.log(`Sending audio chunk: ${bytes.byteLength} bytes (base64: ${base64.length} chars), isFinal: ${isFinal}`);
          socket.sendAudioChunk(base64, isFinal);
        };
        reader.readAsArrayBuffer(audioData);
      }
    });

    if (success) {
      // Start recording duration timer
      setRecordingDuration(0);
      recordingTimerRef.current = setInterval(() => {
        setRecordingDuration(prev => prev + 0.1);
      }, 100);
      
      showNotification('Recording started - speak for at least 2 seconds', 'success');
    } else {
      showNotification('Failed to start recording', 'error');
    }
  }, [startRecording, socket, showNotification]);

  const handleStopRecording = useCallback(() => {
    // Clear recording timer
    if (recordingTimerRef.current) {
      clearInterval(recordingTimerRef.current);
      recordingTimerRef.current = null;
    }
    
    const duration = recordingDuration;
    console.log('Final recording duration:', duration.toFixed(1), 'seconds');
    
    if (duration < 1.0) {
      showNotification('Recording too short! Please record for at least 2 seconds.', 'warning');
      stopRecording();
      setRecordingDuration(0);
      return;
    }
    
    stopRecording();
    setIsTranscribing(true);
    setProcessingStatus('Transcribing audio...');
    setRecordingDuration(0);
  }, [stopRecording, showNotification, recordingDuration]);

  const handlePersonaChange = useCallback((newPersona) => {
    setPersona(newPersona);
    if (socket) {
      socket.changePersona(newPersona);
      showNotification(`Persona changed to ${newPersona}`, 'success');
    }
  }, [socket, showNotification]);

  const handleModeChange = useCallback((newInputMode, newOutputMode) => {
    setInputMode(newInputMode);
    setOutputMode(newOutputMode || newInputMode);
    
    if (socket) {
      socket.changeMode(newInputMode, newOutputMode || newInputMode, audioDisabled);
    }
  }, [socket, audioDisabled]);

  const handleAudioToggle = useCallback(() => {
    const newAudioDisabled = !audioDisabled;
    setAudioDisabled(newAudioDisabled);
    // When Audio is enabled, use voice output so server sends both text + audio reply
    const newOutputMode = newAudioDisabled ? 'text' : 'voice';
    setOutputMode(newOutputMode);

    if (newAudioDisabled && isPlaying) {
      stopAudio();
      if (socket) {
        socket.stopAudio();
      }
    }

    if (socket) {
      socket.changeMode(inputMode, newOutputMode, newAudioDisabled);
    }

    showNotification(
      newAudioDisabled ? 'Replies: text only' : 'Replies: text + audio',
      'info'
    );
  }, [audioDisabled, isPlaying, stopAudio, socket, inputMode, showNotification]);

  const handleNewConversation = useCallback(() => {
    // Reload the page to start a new session
    window.location.reload();
  }, []);

  const handleLoadConversation = useCallback((sessionId) => {
    setMessages([]);
    setIsProcessing(false);
  }, []);

  const handleToggleSidebar = useCallback(() => {
    setSidebarCollapsed(prev => !prev);
  }, []);

  return (
    <div className="app">
      <header className="app-header">
        <div className="header-left">
          <Brain size={32} className="logo" />
          <div className="header-info">
            <h1>Eva AI</h1>
            <span className="subtitle">Emotional Voice Assistant</span>
          </div>
        </div>

        <div className="header-center">
          <button
            className={`view-button ${activeView === 'chat' ? 'active' : ''}`}
            onClick={() => setActiveView('chat')}
          >
            <MessageCircle size={20} />
            <span>Chat</span>
          </button>
          <button
            className={`view-button ${activeView === 'memory' ? 'active' : ''}`}
            onClick={() => setActiveView('memory')}
          >
            <Clock size={20} />
            <span>Memory Lane</span>
          </button>
        </div>

        <div className="header-right">
          <div className={`connection-status ${isConnected ? 'connected' : 'disconnected'}`}>
            {isConnected ? <Wifi size={18} /> : <WifiOff size={18} />}
            <span>{isConnected ? 'Connected' : 'Disconnected'}</span>
          </div>
        </div>
      </header>

      {notification && (
        <div className={`notification ${notification.type} slide-up`}>
          {notification.message}
        </div>
      )}

      <main className="app-main">
        {activeView === 'chat' ? (
          <>
            <ConversationSidebar
              socket={socket}
              isConnected={isConnected}
              currentSessionId={sessionId}
              onNewConversation={handleNewConversation}
              onLoadConversation={handleLoadConversation}
              isCollapsed={sidebarCollapsed}
              onToggleCollapse={handleToggleSidebar}
            />

            <div className="chat-content">
              <ControlPanel
                persona={persona}
                onPersonaChange={handlePersonaChange}
                inputMode={inputMode}
                outputMode={outputMode}
                audioDisabled={audioDisabled}
                onModeChange={handleModeChange}
                onAudioToggle={handleAudioToggle}
              />

              <div className="chat-container">
              <div className="messages-container">
                {messages.length === 0 && !isTranscribing ? (
                  <div className="welcome-message">
                    <Brain size={64} className="welcome-icon" />
                    <h2>Welcome to Eva AI</h2>
                    <p>Your emotional voice assistant is ready to help.</p>
                    <p className="welcome-hint">
                      Try asking about the weather, share your thoughts, or just have a conversation!
                    </p>
                  </div>
                ) : (
                  <>
                    {messages.map((msg, idx) => (
                      <ChatMessage
                        key={idx}
                        message={msg.text}
                        emotion={msg.emotion}
                        persona={msg.persona}
                        isUser={msg.isUser}
                        isTranscribed={msg.isTranscribed}
                      />
                    ))}
                  </>
                )}
                
                {isTranscribing && (
                  <div className="transcribing-indicator fade-in">
                    <div className="transcribing-icon">
                      <div className="audio-wave">
                        <span></span>
                        <span></span>
                        <span></span>
                      </div>
                    </div>
                    <span className="transcribing-text">Transcribing audio...</span>
                  </div>
                )}
                
                {isProcessing && !isTranscribing && (
                  <div className="thinking-indicator fade-in">
                    <div className="thinking-icon">
                      <div className="thinking-dots">
                        <span></span>
                        <span></span>
                        <span></span>
                      </div>
                    </div>
                    <span className="thinking-text">{processingStatus || 'Eva is thinking...'}</span>
                  </div>
                )}
                
                <div ref={messagesEndRef} />
              </div>

                <ChatInput
                  onSendMessage={handleSendMessage}
                  onStartRecording={handleStartRecording}
                  onStopRecording={handleStopRecording}
                  isRecording={isRecording}
                  audioLevel={audioLevel}
                  isProcessing={isProcessing}
                  disabled={!isConnected}
                  recordingDuration={recordingDuration}
                />
              </div>
            </div>
          </>
        ) : (
          <MemoryLane socket={socket} isVisible={activeView === 'memory'} />
        )}
      </main>
    </div>
  );
}

export default App;
