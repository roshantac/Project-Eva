"""
Conversation logging utility for structured logging of user interactions
"""

import os
import json
from datetime import datetime
from pathlib import Path
from typing import Optional
from app.utils.logger import logger


class ConversationLogger:
    """Logger for conversation events"""
    
    def __init__(self):
        self.enabled = os.getenv('LOG_CONVERSATIONS', 'true').lower() == 'true'
        self.log_dir = Path('logs/conversations')
        
        if self.enabled:
            self.log_dir.mkdir(parents=True, exist_ok=True)
    
    def _get_log_file(self) -> Path:
        """Get today's log file path"""
        today = datetime.now().strftime('%Y-%m-%d')
        return self.log_dir / f'conversation-{today}.log'
    
    def _write_log(self, event_type: str, data: dict):
        """Write log entry"""
        if not self.enabled:
            return
        
        try:
            log_entry = {
                'timestamp': datetime.utcnow().isoformat() + 'Z',
                'event': event_type,
                **data
            }
            
            log_file = self._get_log_file()
            with open(log_file, 'a', encoding='utf-8') as f:
                f.write(json.dumps(log_entry, ensure_ascii=False) + '\n')
        
        except Exception as e:
            logger.error(f"Error writing conversation log: {e}")
    
    async def log_session_start(self, session_id: str, user_id: str, persona: str):
        """Log session start"""
        self._write_log('SESSION_START', {
            'sessionId': session_id,
            'userId': user_id,
            'persona': persona
        })
    
    async def log_session_end(self, session_id: str, user_id: str, duration: Optional[float] = None):
        """Log session end"""
        self._write_log('SESSION_END', {
            'sessionId': session_id,
            'userId': user_id,
            'duration': duration
        })
    
    async def log_user_input(self, session_id: str, user_id: str, message: str, input_type: str = 'text'):
        """Log user input"""
        self._write_log('USER_INPUT', {
            'sessionId': session_id,
            'userId': user_id,
            'message': message,
            'inputType': input_type
        })
    
    async def log_bot_response(self, session_id: str, user_id: str, response: str, emotion: str, persona: str, output_mode: str = 'text'):
        """Log bot response"""
        self._write_log('BOT_RESPONSE', {
            'sessionId': session_id,
            'userId': user_id,
            'response': response,
            'emotion': emotion,
            'persona': persona,
            'outputMode': output_mode
        })
    
    async def log_tool_usage(self, session_id: str, tool_name: str, result: Optional[dict] = None):
        """Log tool usage"""
        self._write_log('TOOL_USAGE', {
            'sessionId': session_id,
            'toolName': tool_name,
            'result': result
        })
    
    async def log_transcription(self, session_id: str, user_id: str, transcribed_text: str, duration: Optional[float] = None):
        """Log audio transcription"""
        self._write_log('TRANSCRIPTION', {
            'sessionId': session_id,
            'userId': user_id,
            'text': transcribed_text,
            'duration': duration
        })


# Global instance
conversation_logger = ConversationLogger()
