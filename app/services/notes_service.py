"""
Notes/Lists service for saving and managing user notes and lists
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional
from app.utils.logger import logger


class NotesService:
    """Service for managing user notes and lists"""
    
    def __init__(self):
        self.notes_dir = Path(__file__).parent.parent.parent / 'data' / 'notes'
        self.notes_dir.mkdir(parents=True, exist_ok=True)
        logger.info("✅ Notes service initialized")
    
    def _get_user_notes_file(self, user_id: str) -> Path:
        """Get the notes file path for a user"""
        return self.notes_dir / f'{user_id}_notes.json'
    
    def _load_user_notes(self, user_id: str) -> Dict[str, Any]:
        """Load all notes for a user"""
        notes_file = self._get_user_notes_file(user_id)
        if notes_file.exists():
            try:
                with open(notes_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Error loading notes: {e}")
                return {}
        return {}
    
    def _save_user_notes(self, user_id: str, notes: Dict[str, Any]):
        """Save all notes for a user"""
        notes_file = self._get_user_notes_file(user_id)
        try:
            with open(notes_file, 'w') as f:
                json.dump(notes, f, indent=2, default=str)
        except Exception as e:
            logger.error(f"Error saving notes: {e}")
    
    def _normalize_title(self, title: str) -> str:
        """Normalize title for consistent storage"""
        return title.lower().strip()
    
    async def save_note(
        self,
        user_id: str,
        title: str,
        content: str,
        note_type: str = 'note'
    ) -> Dict[str, Any]:
        """
        Save a note or list
        
        Args:
            user_id: User ID
            title: Note title (e.g., "grocery list", "todo", "shopping")
            content: Note content
            note_type: Type of note ('note', 'list', 'todo')
            
        Returns:
            Result dictionary
        """
        try:
            notes = self._load_user_notes(user_id)
            normalized_title = self._normalize_title(title)
            
            # Check if updating existing note
            is_update = normalized_title in notes
            
            notes[normalized_title] = {
                'title': title,  # Keep original casing
                'content': content,
                'type': note_type,
                'created_at': notes.get(normalized_title, {}).get('created_at', datetime.now().isoformat()),
                'updated_at': datetime.now().isoformat()
            }
            
            self._save_user_notes(user_id, notes)
            
            action = 'updated' if is_update else 'saved'
            logger.info(f"📝 Note '{title}' {action} for user {user_id}")
            
            return {
                'success': True,
                'action': action,
                'title': title,
                'message': f"✅ {title.title()} {action} successfully!"
            }
            
        except Exception as e:
            logger.error(f"Error saving note: {e}")
            return {
                'success': False,
                'error': str(e),
                'message': f"Failed to save {title}"
            }
    
    async def get_note(self, user_id: str, title: str) -> Dict[str, Any]:
        """
        Retrieve a specific note
        
        Args:
            user_id: User ID
            title: Note title
            
        Returns:
            Note data or error
        """
        try:
            notes = self._load_user_notes(user_id)
            normalized_title = self._normalize_title(title)
            
            if normalized_title in notes:
                note = notes[normalized_title]
                logger.info(f"📖 Retrieved note '{title}' for user {user_id}")
                
                return {
                    'success': True,
                    'note': note,
                    'message': f"Here's your {title}:"
                }
            else:
                return {
                    'success': False,
                    'error': 'Note not found',
                    'message': f"I couldn't find a note called '{title}'. Would you like to create one?"
                }
                
        except Exception as e:
            logger.error(f"Error retrieving note: {e}")
            return {
                'success': False,
                'error': str(e),
                'message': f"Failed to retrieve {title}"
            }
    
    async def delete_note(self, user_id: str, title: str) -> Dict[str, Any]:
        """
        Delete a note
        
        Args:
            user_id: User ID
            title: Note title
            
        Returns:
            Result dictionary
        """
        try:
            notes = self._load_user_notes(user_id)
            normalized_title = self._normalize_title(title)
            
            if normalized_title in notes:
                del notes[normalized_title]
                self._save_user_notes(user_id, notes)
                
                logger.info(f"🗑️ Deleted note '{title}' for user {user_id}")
                
                return {
                    'success': True,
                    'message': f"✅ {title.title()} deleted successfully!"
                }
            else:
                return {
                    'success': False,
                    'error': 'Note not found',
                    'message': f"I couldn't find a note called '{title}' to delete."
                }
                
        except Exception as e:
            logger.error(f"Error deleting note: {e}")
            return {
                'success': False,
                'error': str(e),
                'message': f"Failed to delete {title}"
            }
    
    async def list_all_notes(self, user_id: str) -> Dict[str, Any]:
        """
        List all notes for a user
        
        Args:
            user_id: User ID
            
        Returns:
            List of all notes
        """
        try:
            notes = self._load_user_notes(user_id)
            
            if not notes:
                return {
                    'success': True,
                    'notes': [],
                    'message': "You don't have any saved notes yet."
                }
            
            note_list = [
                {
                    'title': note['title'],
                    'type': note['type'],
                    'updated_at': note['updated_at']
                }
                for note in notes.values()
            ]
            
            # Sort by update time
            note_list.sort(key=lambda x: x['updated_at'], reverse=True)
            
            return {
                'success': True,
                'notes': note_list,
                'count': len(note_list),
                'message': f"You have {len(note_list)} saved note(s):"
            }
            
        except Exception as e:
            logger.error(f"Error listing notes: {e}")
            return {
                'success': False,
                'error': str(e),
                'message': "Failed to list notes"
            }
    
    async def update_note(
        self,
        user_id: str,
        title: str,
        content: str
    ) -> Dict[str, Any]:
        """
        Update an existing note (alias for save_note)
        
        Args:
            user_id: User ID
            title: Note title
            content: New content
            
        Returns:
            Result dictionary
        """
        return await self.save_note(user_id, title, content)
    
    def format_note_content(self, note: Dict[str, Any]) -> str:
        """
        Format note content for display
        
        Args:
            note: Note dictionary
            
        Returns:
            Formatted string
        """
        content = note['content']
        title = note['title']
        
        # If it's a list, format as bullet points
        if note.get('type') == 'list' or '\n' in content:
            lines = content.split('\n')
            formatted_lines = [f"• {line.strip()}" for line in lines if line.strip()]
            return f"**{title}:**\n" + '\n'.join(formatted_lines)
        else:
            return f"**{title}:** {content}"

# Made with Bob
