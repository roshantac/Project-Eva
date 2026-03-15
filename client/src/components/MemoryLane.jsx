import React, { useState, useEffect } from 'react';
import { Clock, Tag, Search, Trash2, Edit2, Plus } from 'lucide-react';
import { format } from 'date-fns';
import './MemoryLane.css';

const MemoryLane = ({ socket, isVisible }) => {
  const [memories, setMemories] = useState([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedMemory, setSelectedMemory] = useState(null);
  const [isEditing, setIsEditing] = useState(false);

  useEffect(() => {
    if (isVisible && socket) {
      socket.requestMemories();

      const handleMemoryData = (data) => {
        setMemories(data.memories);
      };

      const handleMemoryUpdated = (data) => {
        if (data.action === 'added' || data.action === 'updated') {
          socket.requestMemories();
        } else if (data.action === 'deleted') {
          setMemories(prev => prev.filter(m => m._id !== data.memoryId));
        }
      };

      socket.on('MEMORY_DATA', handleMemoryData);
      socket.on('MEMORY_UPDATED', handleMemoryUpdated);

      return () => {
        socket.off('MEMORY_DATA', handleMemoryData);
        socket.off('MEMORY_UPDATED', handleMemoryUpdated);
      };
    }
  }, [isVisible, socket]);

  const filteredMemories = memories.filter(memory => 
    memory.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
    memory.content.toLowerCase().includes(searchQuery.toLowerCase()) ||
    (memory.summary && memory.summary.toLowerCase().includes(searchQuery.toLowerCase()))
  );

  const handleDeleteMemory = (memoryId) => {
    if (window.confirm('Are you sure you want to delete this memory?')) {
      socket.deleteMemory(memoryId);
      setSelectedMemory(null);
    }
  };

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

  if (!isVisible) return null;

  return (
    <div className="memory-lane">
      <div className="memory-header">
        <h2>Memory Lane</h2>
        <div className="memory-search">
          <Search size={18} />
          <input
            type="text"
            placeholder="Search memories..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
          />
        </div>
      </div>

      <div className="memory-content">
        <div className="memory-list">
          {filteredMemories.length === 0 ? (
            <div className="empty-state">
              <Clock size={48} />
              <p>No memories yet</p>
              <span>Important moments will be saved here automatically</span>
            </div>
          ) : (
            filteredMemories.map(memory => (
              <div
                key={memory._id}
                className={`memory-item ${selectedMemory?._id === memory._id ? 'selected' : ''}`}
                onClick={() => setSelectedMemory(memory)}
              >
                <div className="memory-item-header">
                  <h3>{memory.title}</h3>
                  <span 
                    className="memory-emotion"
                    style={{ color: getEmotionColor(memory.emotion) }}
                  >
                    {memory.emotion}
                  </span>
                </div>
                <p className="memory-summary">
                  {memory.summary || memory.content.substring(0, 100) + '...'}
                </p>
                <div className="memory-meta">
                  <span className="memory-date">
                    <Clock size={14} />
                    {format(new Date(memory.metadata.createdAt), 'MMM dd, yyyy')}
                  </span>
                  {memory.tags && memory.tags.length > 0 && (
                    <div className="memory-tags">
                      {memory.tags.map((tag, idx) => (
                        <span key={idx} className="memory-tag">
                          <Tag size={12} />
                          {tag}
                        </span>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            ))
          )}
        </div>

        {selectedMemory && (
          <div className="memory-detail">
            <div className="memory-detail-header">
              <h2>{selectedMemory.title}</h2>
              <div className="memory-actions">
                <button
                  className="icon-button"
                  onClick={() => handleDeleteMemory(selectedMemory._id)}
                  title="Delete memory"
                >
                  <Trash2 size={18} />
                </button>
              </div>
            </div>

            <div className="memory-detail-content">
              <div className="memory-info">
                <span 
                  className="memory-emotion-badge"
                  style={{ background: getEmotionColor(selectedMemory.emotion) }}
                >
                  {selectedMemory.emotion}
                </span>
                <span className="memory-importance">
                  Importance: {selectedMemory.importance}/10
                </span>
              </div>

              {selectedMemory.summary && (
                <div className="memory-section">
                  <h4>Summary</h4>
                  <p>{selectedMemory.summary}</p>
                </div>
              )}

              <div className="memory-section">
                <h4>Details</h4>
                <p className="memory-full-content">{selectedMemory.content}</p>
              </div>

              {selectedMemory.tags && selectedMemory.tags.length > 0 && (
                <div className="memory-section">
                  <h4>Tags</h4>
                  <div className="memory-tags-list">
                    {selectedMemory.tags.map((tag, idx) => (
                      <span key={idx} className="tag-badge">
                        {tag}
                      </span>
                    ))}
                  </div>
                </div>
              )}

              <div className="memory-footer">
                <span>
                  Created: {format(new Date(selectedMemory.metadata.createdAt), 'PPpp')}
                </span>
                {selectedMemory.metadata.accessCount > 0 && (
                  <span>
                    Accessed {selectedMemory.metadata.accessCount} times
                  </span>
                )}
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default MemoryLane;
