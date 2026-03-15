import React, { useState, useEffect, useCallback } from 'react';
import { MessageSquare, Plus, Trash2, ChevronLeft, ChevronRight, Search, Clock } from 'lucide-react';
import { useSocketEvent } from '../hooks/useSocket';
import './ConversationSidebar.css';

const ConversationSidebar = ({ 
  socket,
  isConnected,
  currentSessionId, 
  onNewConversation, 
  onLoadConversation,
  isCollapsed,
  onToggleCollapse
}) => {
  const [conversations, setConversations] = useState([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  // Use useSocketEvent hook for proper event handling
  useSocketEvent('CONVERSATIONS_LIST', useCallback((data) => {
    const convArray = data.conversations || [];
    setConversations(convArray);
    setIsLoading(false);
  }, []));

  useSocketEvent('CONVERSATION_DELETED', useCallback((data) => {
    setConversations(prev => prev.filter(conv => conv.sessionId !== data.sessionId));
  }, []));

  const loadConversations = useCallback(() => {
    if (socket && socket.isConnected()) {
      setIsLoading(true);
      socket.emit('CONVERSATIONS_REQUEST', { limit: 50 });
    } else {
      setIsLoading(false);
    }
  }, [socket]);

  useEffect(() => {
    // Load conversations when connection is established
    if (isConnected && socket) {
      loadConversations();
    }
  }, [isConnected, socket, loadConversations]);

  const handleLoadConversation = (sessionId) => {
    if (socket && sessionId !== currentSessionId) {
      socket.emit('CONVERSATION_LOAD', { sessionId });
      onLoadConversation(sessionId);
    }
  };

  const handleDeleteConversation = (sessionId, e) => {
    e.stopPropagation();
    if (window.confirm('Are you sure you want to delete this conversation?')) {
      if (socket) {
        socket.emit('CONVERSATION_DELETE', { sessionId });
      }
    }
  };

  const formatDate = (dateString) => {
    const date = new Date(dateString);
    const now = new Date();
    const diffMs = now - date;
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMs / 3600000);
    const diffDays = Math.floor(diffMs / 86400000);

    if (diffMins < 1) return 'Just now';
    if (diffMins < 60) return `${diffMins}m ago`;
    if (diffHours < 24) return `${diffHours}h ago`;
    if (diffDays < 7) return `${diffDays}d ago`;
    
    return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
  };

  const filteredConversations = conversations.filter(conv =>
    conv.title.toLowerCase().includes(searchQuery.toLowerCase())
  );

  if (isCollapsed) {
    return (
      <div className="conversation-sidebar collapsed">
        <button 
          className="sidebar-toggle"
          onClick={onToggleCollapse}
          title="Show conversations"
        >
          <ChevronRight size={20} />
        </button>
        <button 
          className="new-conversation-btn collapsed"
          onClick={onNewConversation}
          title="New conversation"
        >
          <Plus size={20} />
        </button>
      </div>
    );
  }

  return (
    <div className="conversation-sidebar">
      <div className="sidebar-header">
        <div className="sidebar-title">
          <MessageSquare size={20} />
          <span>Conversations</span>
        </div>
        <div className="sidebar-actions">
          <button 
            className="icon-button"
            onClick={onNewConversation}
            title="New conversation"
          >
            <Plus size={18} />
          </button>
          <button 
            className="icon-button"
            onClick={onToggleCollapse}
            title="Hide sidebar"
          >
            <ChevronLeft size={18} />
          </button>
        </div>
      </div>

      <div className="sidebar-search">
        <Search size={16} />
        <input
          type="text"
          placeholder="Search conversations..."
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
        />
      </div>

      <div className="conversations-list">
        {isLoading ? (
          <div className="loading-state">
            <div className="spinner"></div>
            <span>Loading conversations...</span>
          </div>
        ) : filteredConversations.length === 0 ? (
          <div className="empty-state">
            <MessageSquare size={48} className="empty-icon" />
            <p>No conversations yet</p>
            <button className="start-button" onClick={onNewConversation}>
              Start chatting
            </button>
          </div>
        ) : (
          filteredConversations.map((conv) => (
            <div
              key={conv.sessionId}
              className={`conversation-item ${conv.sessionId === currentSessionId ? 'active' : ''}`}
              onClick={() => handleLoadConversation(conv.sessionId)}
            >
              <div className="conversation-content">
                <div className="conversation-title">{conv.title}</div>
                <div className="conversation-meta">
                  <span className="message-count">{conv.messageCount} messages</span>
                  <span className="conversation-time">
                    <Clock size={12} />
                    {formatDate(conv.lastMessageAt)}
                  </span>
                </div>
              </div>
              <button
                className="delete-button"
                onClick={(e) => handleDeleteConversation(conv.sessionId, e)}
                title="Delete conversation"
              >
                <Trash2 size={16} />
              </button>
            </div>
          ))
        )}
      </div>
    </div>
  );
};

export default ConversationSidebar;
