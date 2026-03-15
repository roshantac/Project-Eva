import React from 'react';
import { User, Bot, Mic } from 'lucide-react';
import './ChatMessage.css';

const ChatMessage = ({ message, emotion, persona, isUser, isTranscribed }) => {
  const getEmotionColor = (emotion) => {
    const colors = {
      happy: 'var(--emotion-happy)',
      sad: 'var(--emotion-sad)',
      anxious: 'var(--emotion-anxious)',
      excited: 'var(--emotion-excited)',
      angry: 'var(--emotion-angry)',
      neutral: 'var(--emotion-neutral)',
      grateful: 'var(--emotion-grateful)',
      confused: 'var(--emotion-confused)'
    };
    return colors[emotion] || colors.neutral;
  };

  return (
    <div className={`chat-message ${isUser ? 'user-message' : 'bot-message'} fade-in`}>
      <div className="message-avatar" style={{ 
        background: isUser ? 'var(--primary-color)' : getEmotionColor(emotion) 
      }}>
        {isUser ? <User size={20} /> : <Bot size={20} />}
      </div>
      <div className="message-content">
        <div className="message-header">
          <span className="message-sender">
            {isUser ? 'You' : `Eva ${persona ? `(${persona})` : ''}`}
          </span>
          {isUser && isTranscribed && (
            <span className="message-badge transcribed-badge">
              <Mic size={12} />
              <span>Voice</span>
            </span>
          )}
          {!isUser && emotion && emotion !== 'neutral' && (
            <span className="message-emotion" style={{ color: getEmotionColor(emotion) }}>
              {emotion}
            </span>
          )}
        </div>
        <div className="message-text">{message}</div>
      </div>
    </div>
  );
};

export default ChatMessage;
