"""
Reminder service for scheduling and managing reminders
"""

import os
import json
import asyncio
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.date import DateTrigger
from app.utils.logger import logger


class ReminderService:
    """Service for managing reminders with voice notifications"""
    
    def __init__(self):
        self.scheduler = AsyncIOScheduler()
        self.reminders_file = Path(__file__).parent.parent.parent / 'data' / 'reminders.json'
        self.reminders: Dict[str, Dict[str, Any]] = {}
        self.socket_handler = None  # Will be set by main app
        self.tts_service = None  # Will be set by main app
        
        # Ensure reminders file exists
        self.reminders_file.parent.mkdir(parents=True, exist_ok=True)
        if not self.reminders_file.exists():
            self._save_reminders()
        
        self._load_reminders()
        self.scheduler.start()
        logger.info("✅ Reminder service initialized")
    
    def set_services(self, socket_handler, tts_service):
        """Set socket handler and TTS service for sending reminders"""
        self.socket_handler = socket_handler
        self.tts_service = tts_service
    
    def _load_reminders(self):
        """Load reminders from file"""
        try:
            if self.reminders_file.exists():
                with open(self.reminders_file, 'r') as f:
                    self.reminders = json.load(f)
                logger.info(f"Loaded {len(self.reminders)} reminders")
                
                # Reschedule active reminders
                for reminder_id, reminder in self.reminders.items():
                    if reminder['status'] == 'active':
                        self._schedule_reminder(reminder_id, reminder)
        except Exception as e:
            logger.error(f"Error loading reminders: {e}")
            self.reminders = {}
    
    def _save_reminders(self):
        """Save reminders to file"""
        try:
            with open(self.reminders_file, 'w') as f:
                json.dump(self.reminders, f, indent=2, default=str)
        except Exception as e:
            logger.error(f"Error saving reminders: {e}")
    
    def _schedule_reminder(self, reminder_id: str, reminder: Dict[str, Any]):
        """Schedule a reminder"""
        try:
            trigger_time = datetime.fromisoformat(reminder['trigger_time'])
            
            # Only schedule if in the future
            if trigger_time > datetime.now():
                self.scheduler.add_job(
                    self._trigger_reminder,
                    trigger=DateTrigger(run_date=trigger_time),
                    args=[reminder_id],
                    id=reminder_id,
                    replace_existing=True
                )
                logger.info(f"⏰ Scheduled reminder '{reminder['message']}' for {trigger_time}")
            else:
                # Mark as expired if past
                reminder['status'] = 'expired'
                self._save_reminders()
        except Exception as e:
            logger.error(f"Error scheduling reminder: {e}")
    
    async def _trigger_reminder(self, reminder_id: str):
        """Trigger a reminder - send notification"""
        try:
            reminder = self.reminders.get(reminder_id)
            if not reminder:
                return
            
            logger.info(f"🔔 Triggering reminder: {reminder['message']}")
            
            # Update status
            reminder['status'] = 'completed'
            reminder['completed_at'] = datetime.now().isoformat()
            self._save_reminders()
            
            # Send notification via socket if available
            if self.socket_handler and reminder.get('user_sid'):
                await self._send_reminder_notification(reminder)
            
        except Exception as e:
            logger.error(f"Error triggering reminder: {e}")
    
    async def _send_reminder_notification(self, reminder: Dict[str, Any]):
        """Send reminder notification to user"""
        try:
            user_sid = reminder.get('user_sid')
            if not user_sid:
                return
            
            message = f"🔔 Reminder: {reminder['message']}"
            
            # Send text notification
            await self.socket_handler.sio.emit(
                'BOT_TEXT_RESPONSE',
                {
                    'text': message,
                    'emotion': 'neutral',
                    'persona': 'assistant',
                    'isReminder': True
                },
                to=user_sid
            )
            
            # Send voice notification if TTS available
            if self.tts_service and reminder.get('voice_enabled', True):
                audio_buffer = await self.tts_service.generate_speech(
                    f"Reminder: {reminder['message']}",
                    {'voice': 'nova', 'speed': 1.0}
                )
                
                import base64
                audio_base64 = base64.b64encode(audio_buffer).decode('utf-8')
                
                await self.socket_handler.sio.emit(
                    'BOT_AUDIO_STREAM',
                    {
                        'audio': audio_base64,
                        'isLast': True,
                        'format': 'base64',
                        'isReminder': True
                    },
                    to=user_sid
                )
            
            logger.info(f"✅ Reminder notification sent to {user_sid}")
            
        except Exception as e:
            logger.error(f"Error sending reminder notification: {e}")
    
    async def create_reminder(
        self,
        message: str,
        trigger_time: datetime,
        user_id: str,
        user_sid: str,
        voice_enabled: bool = True
    ) -> Dict[str, Any]:
        """
        Create a new reminder
        
        Args:
            message: Reminder message
            trigger_time: When to trigger the reminder
            user_id: User ID
            user_sid: Socket ID for notification
            voice_enabled: Whether to send voice notification
            
        Returns:
            Created reminder data
        """
        try:
            # Generate unique ID
            reminder_id = f"reminder_{int(datetime.now().timestamp() * 1000)}"
            
            reminder = {
                'id': reminder_id,
                'message': message,
                'trigger_time': trigger_time.isoformat(),
                'created_at': datetime.now().isoformat(),
                'user_id': user_id,
                'user_sid': user_sid,
                'voice_enabled': voice_enabled,
                'status': 'active'
            }
            
            # Save reminder
            self.reminders[reminder_id] = reminder
            self._save_reminders()
            
            # Schedule it
            self._schedule_reminder(reminder_id, reminder)
            
            logger.info(f"✅ Created reminder: {message} at {trigger_time}")
            
            return {
                'success': True,
                'reminder': reminder,
                'message': f"Reminder set for {trigger_time.strftime('%Y-%m-%d %H:%M:%S')}"
            }
            
        except Exception as e:
            logger.error(f"Error creating reminder: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    async def get_reminders(self, user_id: str, status: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get reminders for a user"""
        try:
            user_reminders = [
                r for r in self.reminders.values()
                if r['user_id'] == user_id and (status is None or r['status'] == status)
            ]
            return sorted(user_reminders, key=lambda x: x['trigger_time'])
        except Exception as e:
            logger.error(f"Error getting reminders: {e}")
            return []
    
    async def cancel_reminder(self, reminder_id: str) -> bool:
        """Cancel a reminder"""
        try:
            if reminder_id in self.reminders:
                # Remove from scheduler
                try:
                    self.scheduler.remove_job(reminder_id)
                except:
                    pass
                
                # Update status
                self.reminders[reminder_id]['status'] = 'cancelled'
                self._save_reminders()
                
                logger.info(f"❌ Cancelled reminder: {reminder_id}")
                return True
            return False
        except Exception as e:
            logger.error(f"Error cancelling reminder: {e}")
            return False
    
    def parse_time_expression(self, expression: str) -> Optional[datetime]:
        """
        Parse natural language time expressions
        
        Examples:
            - "in 5 minutes"
            - "in 2 hours"
            - "tomorrow at 3pm"
            - "at 5:30pm"
            - "in 1 day"
        """
        import re
        from dateutil import parser as date_parser
        
        expression = expression.lower().strip()
        now = datetime.now()
        
        # Pattern: "in X minutes/hours/days"
        match = re.search(r'in (\d+)\s*(minute|hour|day|week)s?', expression)
        if match:
            amount = int(match.group(1))
            unit = match.group(2)
            
            if unit == 'minute':
                return now + timedelta(minutes=amount)
            elif unit == 'hour':
                return now + timedelta(hours=amount)
            elif unit == 'day':
                return now + timedelta(days=amount)
            elif unit == 'week':
                return now + timedelta(weeks=amount)
        
        # Pattern: "tomorrow at X"
        if 'tomorrow' in expression:
            tomorrow = now + timedelta(days=1)
            time_part = expression.replace('tomorrow', '').replace('at', '').strip()
            if time_part:
                try:
                    time_obj = date_parser.parse(time_part)
                    return tomorrow.replace(hour=time_obj.hour, minute=time_obj.minute, second=0, microsecond=0)
                except:
                    return tomorrow.replace(hour=9, minute=0, second=0, microsecond=0)
            return tomorrow.replace(hour=9, minute=0, second=0, microsecond=0)
        
        # Pattern: "at X" (today)
        if expression.startswith('at '):
            time_str = expression.replace('at ', '').strip()
            try:
                time_obj = date_parser.parse(time_str)
                result = now.replace(hour=time_obj.hour, minute=time_obj.minute, second=0, microsecond=0)
                # If time has passed today, schedule for tomorrow
                if result <= now:
                    result += timedelta(days=1)
                return result
            except:
                pass
        
        # Try general date parsing
        try:
            result = date_parser.parse(expression, fuzzy=True)
            if result > now:
                return result
        except:
            pass
        
        return None

# Made with Bob
