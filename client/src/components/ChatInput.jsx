import React, { useState, useRef, useEffect } from 'react';
import { Send, Mic, MicOff, Loader } from 'lucide-react';
import './ChatInput.css';

const ChatInput = ({ 
  onSendMessage, 
  onStartRecording, 
  onStopRecording, 
  isRecording, 
  audioLevel,
  isProcessing,
  disabled,
  recordingDuration = 0
}) => {
  const [message, setMessage] = useState('');
  const textareaRef = useRef(null);

  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = textareaRef.current.scrollHeight + 'px';
    }
  }, [message]);

  const handleSubmit = (e) => {
    e.preventDefault();
    if (message.trim() && !isProcessing) {
      onSendMessage(message);
      setMessage('');
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  const handleMicClick = () => {
    if (isRecording) {
      onStopRecording();
    } else {
      onStartRecording();
    }
  };

  return (
    <div className="chat-input-container">
      {isRecording && (
        <div className="recording-indicator">
          <div className="recording-wave">
            <div 
              className="wave-bar" 
              style={{ height: `${Math.max(20, audioLevel * 100)}%` }}
            />
            <div 
              className="wave-bar" 
              style={{ height: `${Math.max(20, audioLevel * 80)}%` }}
            />
            <div 
              className="wave-bar" 
              style={{ height: `${Math.max(20, audioLevel * 100)}%` }}
            />
          </div>
          <span>
            Recording... {recordingDuration.toFixed(1)}s
            {recordingDuration < 2.0 && (
              <span style={{ color: '#ff6b6b', marginLeft: '8px' }}>
                (speak for at least 2s)
              </span>
            )}
          </span>
        </div>
      )}

      <form onSubmit={handleSubmit} className="chat-input-form">
        <button
          type="button"
          className={`mic-button ${isRecording ? 'recording' : ''}`}
          onClick={handleMicClick}
          disabled={disabled || isProcessing}
          title={isRecording ? 'Stop recording' : 'Start recording'}
        >
          {isRecording ? <MicOff size={20} /> : <Mic size={20} />}
        </button>

        <textarea
          ref={textareaRef}
          value={message}
          onChange={(e) => setMessage(e.target.value)}
          onKeyPress={handleKeyPress}
          placeholder="Type your message or use voice..."
          className="message-input"
          disabled={disabled || isRecording || isProcessing}
          rows={1}
        />

        <button
          type="submit"
          className="send-button"
          disabled={!message.trim() || disabled || isProcessing}
          title="Send message"
        >
          {isProcessing ? <Loader size={20} className="pulse" /> : <Send size={20} />}
        </button>
      </form>
    </div>
  );
};

export default ChatInput;
