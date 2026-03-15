import React from 'react';
import { Volume2, VolumeX, MessageSquare, Mic } from 'lucide-react';
import './ControlPanel.css';

const ControlPanel = ({ 
  persona, 
  onPersonaChange, 
  inputMode, 
  outputMode, 
  audioDisabled,
  onModeChange,
  onAudioToggle 
}) => {
  const personas = [
    { value: 'friend', label: 'Friend', description: 'Casual & Supportive' },
    { value: 'mentor', label: 'Mentor', description: 'Growth-Oriented' },
    { value: 'advisor', label: 'Advisor', description: 'Professional & Practical' }
  ];

  return (
    <div className="control-panel">
      <div className="control-section">
        <label className="control-label">Persona</label>
        <select 
          value={persona} 
          onChange={(e) => onPersonaChange(e.target.value)}
          className="persona-select"
        >
          {personas.map(p => (
            <option key={p.value} value={p.value}>
              {p.label} - {p.description}
            </option>
          ))}
        </select>
      </div>

      <div className="control-section">
        <label className="control-label">Communication Mode</label>
        <div className="mode-buttons">
          <button
            className={`mode-button ${inputMode === 'text' ? 'active' : ''}`}
            onClick={() => onModeChange('text', outputMode)}
            title="Text input"
          >
            <MessageSquare size={18} />
            <span>Text</span>
          </button>
          <button
            className={`mode-button ${inputMode === 'voice' ? 'active' : ''}`}
            onClick={() => onModeChange('voice', outputMode)}
            title="Voice input"
          >
            <Mic size={18} />
            <span>Voice</span>
          </button>
        </div>
      </div>

      <div className="control-section">
        <label className="control-label">Reply with</label>
        <button
          className={`audio-toggle ${audioDisabled ? 'disabled' : 'enabled'}`}
          onClick={onAudioToggle}
          title={audioDisabled ? 'Enable text + audio replies' : 'Text only (disable audio)'}
        >
          {audioDisabled ? (
            <>
              <MessageSquare size={18} />
              <span>Text only</span>
            </>
          ) : (
            <>
              <Volume2 size={18} />
              <span>Text + Audio</span>
            </>
          )}
        </button>
      </div>
    </div>
  );
};

export default ControlPanel;
