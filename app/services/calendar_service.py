"""
Calendar service for managing meetings and events
"""

import os
import json
import asyncio
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional
from app.utils.logger import logger


class CalendarService:
    """Service for managing calendar events and meetings"""
    
    def __init__(self):
        self.calendar_file = Path(__file__).parent.parent.parent / 'data' / 'calendar.json'
        self.events: Dict[str, Dict[str, Any]] = {}
        
        # Ensure calendar file exists
        self.calendar_file.parent.mkdir(parents=True, exist_ok=True)
        if not self.calendar_file.exists():
            self._save_events()
        
        self._load_events()
        logger.info("✅ Calendar service initialized")
    
    def _load_events(self):
        """Load calendar events from file"""
        try:
            if self.calendar_file.exists():
                with open(self.calendar_file, 'r') as f:
                    self.events = json.load(f)
                logger.info(f"Loaded {len(self.events)} calendar events")
        except Exception as e:
            logger.error(f"Error loading calendar events: {e}")
            self.events = {}
    
    def _save_events(self):
        """Save calendar events to file"""
        try:
            with open(self.calendar_file, 'w') as f:
                json.dump(self.events, f, indent=2, default=str)
        except Exception as e:
            logger.error(f"Error saving calendar events: {e}")
    
    async def schedule_meeting(
        self,
        title: str,
        start_time: datetime,
        duration_minutes: int,
        user_id: str,
        description: Optional[str] = None,
        location: Optional[str] = None,
        attendees: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Schedule a new meeting/event
        
        Args:
            title: Meeting title
            start_time: When the meeting starts
            duration_minutes: Duration in minutes
            user_id: User ID
            description: Optional meeting description
            location: Optional meeting location
            attendees: Optional list of attendees
            
        Returns:
            Created event data
        """
        try:
            # Generate unique ID
            event_id = f"event_{int(datetime.now().timestamp() * 1000)}"
            
            # Calculate end time
            end_time = start_time + timedelta(minutes=duration_minutes)
            
            # Check for conflicts
            conflicts = self._check_conflicts(user_id, start_time, end_time)
            
            event = {
                'id': event_id,
                'title': title,
                'description': description or '',
                'start_time': start_time.isoformat(),
                'end_time': end_time.isoformat(),
                'duration_minutes': duration_minutes,
                'location': location or '',
                'attendees': attendees or [],
                'created_at': datetime.now().isoformat(),
                'user_id': user_id,
                'status': 'scheduled',
                'has_conflicts': len(conflicts) > 0,
                'conflicts': conflicts
            }
            
            # Save event
            self.events[event_id] = event
            self._save_events()
            
            logger.info(f"✅ Scheduled meeting: {title} at {start_time}")
            
            conflict_warning = ""
            if conflicts:
                conflict_warning = f"\n⚠️ Warning: This meeting conflicts with {len(conflicts)} existing event(s)."
            
            return {
                'success': True,
                'event': event,
                'message': f"Meeting '{title}' scheduled for {start_time.strftime('%Y-%m-%d at %I:%M %p')}{conflict_warning}"
            }
            
        except Exception as e:
            logger.error(f"Error scheduling meeting: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _check_conflicts(self, user_id: str, start_time: datetime, end_time: datetime) -> List[str]:
        """Check for scheduling conflicts"""
        conflicts = []
        for event_id, event in self.events.items():
            if event['user_id'] != user_id or event['status'] == 'cancelled':
                continue
            
            event_start = datetime.fromisoformat(event['start_time'])
            event_end = datetime.fromisoformat(event['end_time'])
            
            # Check if times overlap
            if (start_time < event_end and end_time > event_start):
                conflicts.append(event['title'])
        
        return conflicts
    
    async def get_todays_calendar(self, user_id: str) -> Dict[str, Any]:
        """
        Get today's calendar events
        
        Args:
            user_id: User ID
            
        Returns:
            Today's events formatted nicely
        """
        try:
            now = datetime.now()
            today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
            today_end = today_start + timedelta(days=1)
            
            # Get today's events
            todays_events = []
            for event in self.events.values():
                if event['user_id'] != user_id or event['status'] == 'cancelled':
                    continue
                
                event_start = datetime.fromisoformat(event['start_time'])
                if today_start <= event_start < today_end:
                    todays_events.append(event)
            
            # Sort by start time
            todays_events.sort(key=lambda x: x['start_time'])
            
            if not todays_events:
                return {
                    'success': True,
                    'events': [],
                    'count': 0,
                    'message': f"📅 You have no events scheduled for today ({now.strftime('%A, %B %d, %Y')})."
                }
            
            # Format events nicely
            formatted_events = []
            for event in todays_events:
                start = datetime.fromisoformat(event['start_time'])
                end = datetime.fromisoformat(event['end_time'])
                
                formatted = {
                    'id': event['id'],
                    'title': event['title'],
                    'time': f"{start.strftime('%I:%M %p')} - {end.strftime('%I:%M %p')}",
                    'duration': f"{event['duration_minutes']} minutes",
                    'description': event['description'],
                    'location': event['location'],
                    'status': event['status']
                }
                formatted_events.append(formatted)
            
            # Create a nice summary
            summary_lines = [f"📅 Your calendar for today ({now.strftime('%A, %B %d, %Y')}):"]
            summary_lines.append(f"\nYou have {len(todays_events)} event(s) scheduled:\n")
            
            for i, event in enumerate(formatted_events, 1):
                start = datetime.fromisoformat(todays_events[i-1]['start_time'])
                summary_lines.append(f"{i}. {event['title']}")
                summary_lines.append(f"   ⏰ {event['time']}")
                if event['location']:
                    summary_lines.append(f"   📍 {event['location']}")
                if event['description']:
                    summary_lines.append(f"   📝 {event['description']}")
                summary_lines.append("")
            
            return {
                'success': True,
                'events': formatted_events,
                'count': len(todays_events),
                'message': '\n'.join(summary_lines)
            }
            
        except Exception as e:
            logger.error(f"Error getting today's calendar: {e}")
            return {
                'success': False,
                'error': str(e),
                'message': "Sorry, I couldn't retrieve your calendar."
            }
    async def list_all_meetings(self, user_id: str) -> Dict[str, Any]:
        """
        List all scheduled meetings (upcoming and today)
        
        Args:
            user_id: User ID
            
        Returns:
            All scheduled meetings formatted nicely
        """
        try:
            now = datetime.now()
            
            # Get all future and today's events
            all_events = []
            for event in self.events.values():
                if event['user_id'] != user_id or event['status'] == 'cancelled':
                    continue
                
                event_start = datetime.fromisoformat(event['start_time'])
                # Include events from today onwards
                if event_start.date() >= now.date():
                    all_events.append(event)
            
            # Sort by start time
            all_events.sort(key=lambda x: x['start_time'])
            
            if not all_events:
                return {
                    'success': True,
                    'events': [],
                    'count': 0,
                    'message': "📅 You have no scheduled meetings."
                }
            
            # Group events by date
            events_by_date = {}
            for event in all_events:
                start = datetime.fromisoformat(event['start_time'])
                date_key = start.strftime('%Y-%m-%d')
                if date_key not in events_by_date:
                    events_by_date[date_key] = []
                events_by_date[date_key].append(event)
            
            # Create a nice summary
            summary_lines = [f"📅 Your Scheduled Meetings ({len(all_events)} total):\n"]
            
            for date_key in sorted(events_by_date.keys()):
                date_events = events_by_date[date_key]
                date_obj = datetime.fromisoformat(date_events[0]['start_time'])
                
                # Determine if it's today, tomorrow, or a specific date
                if date_obj.date() == now.date():
                    date_label = "Today"
                elif date_obj.date() == (now + timedelta(days=1)).date():
                    date_label = "Tomorrow"
                else:
                    date_label = date_obj.strftime('%A, %B %d, %Y')
                
                summary_lines.append(f"\n📆 {date_label}:")
                
                for event in date_events:
                    start = datetime.fromisoformat(event['start_time'])
                    end = datetime.fromisoformat(event['end_time'])
                    
                    summary_lines.append(f"  • {event['title']}")
                    summary_lines.append(f"    ⏰ {start.strftime('%I:%M %p')} - {end.strftime('%I:%M %p')}")
                    if event['location']:
                        summary_lines.append(f"    📍 {event['location']}")
                    if event['description']:
                        summary_lines.append(f"    📝 {event['description']}")
            
            return {
                'success': True,
                'events': all_events,
                'count': len(all_events),
                'message': '\n'.join(summary_lines)
            }
            
        except Exception as e:
            logger.error(f"Error listing all meetings: {e}")
            return {
                'success': False,
                'error': str(e),
                'message': "Sorry, I couldn't retrieve your meetings."
            }
    
    
    async def get_events_by_date(self, user_id: str, date: datetime) -> List[Dict[str, Any]]:
        """Get events for a specific date"""
        try:
            day_start = date.replace(hour=0, minute=0, second=0, microsecond=0)
            day_end = day_start + timedelta(days=1)
            
            events = []
            for event in self.events.values():
                if event['user_id'] != user_id or event['status'] == 'cancelled':
                    continue
                
                event_start = datetime.fromisoformat(event['start_time'])
                if day_start <= event_start < day_end:
                    events.append(event)
            
            return sorted(events, key=lambda x: x['start_time'])
        except Exception as e:
            logger.error(f"Error getting events by date: {e}")
            return []
    
    async def get_upcoming_events(self, user_id: str, days: int = 7) -> List[Dict[str, Any]]:
        """Get upcoming events for the next N days"""
        try:
            now = datetime.now()
            end_date = now + timedelta(days=days)
            
            events = []
            for event in self.events.values():
                if event['user_id'] != user_id or event['status'] == 'cancelled':
                    continue
                
                event_start = datetime.fromisoformat(event['start_time'])
                if now <= event_start <= end_date:
                    events.append(event)
            
            return sorted(events, key=lambda x: x['start_time'])
        except Exception as e:
            logger.error(f"Error getting upcoming events: {e}")
            return []
    
    async def cancel_event(self, event_id: str, user_id: str) -> Dict[str, Any]:
        """Cancel an event"""
        try:
            if event_id not in self.events:
                return {
                    'success': False,
                    'message': "Event not found."
                }
            
            event = self.events[event_id]
            
            # Check ownership
            if event['user_id'] != user_id:
                return {
                    'success': False,
                    'message': "You don't have permission to cancel this event."
                }
            
            # Update status
            event['status'] = 'cancelled'
            event['cancelled_at'] = datetime.now().isoformat()
            self._save_events()
            
            logger.info(f"❌ Cancelled event: {event['title']}")
            
            return {
                'success': True,
                'message': f"Event '{event['title']}' has been cancelled."
            }
            
        except Exception as e:
            logger.error(f"Error cancelling event: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    async def update_event(
        self,
        event_id: str,
        user_id: str,
        **updates
    ) -> Dict[str, Any]:
        """Update an event"""
        try:
            if event_id not in self.events:
                return {
                    'success': False,
                    'message': "Event not found."
                }
            
            event = self.events[event_id]
            
            # Check ownership
            if event['user_id'] != user_id:
                return {
                    'success': False,
                    'message': "You don't have permission to update this event."
                }
            
            # Update allowed fields
            allowed_fields = ['title', 'description', 'location', 'attendees']
            for field, value in updates.items():
                if field in allowed_fields:
                    event[field] = value
            
            event['updated_at'] = datetime.now().isoformat()
            self._save_events()
            
            logger.info(f"✏️ Updated event: {event['title']}")
            
            return {
                'success': True,
                'event': event,
                'message': f"Event '{event['title']}' has been updated."
            }
            
        except Exception as e:
            logger.error(f"Error updating event: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def parse_time_expression(self, expression: str) -> Optional[datetime]:
        """
        Parse natural language time expressions for meetings
        
        Examples:
            - "tomorrow at 3pm"
            - "next Monday at 10am"
            - "at 5:30pm today"
            - "in 2 hours"
        """
        import re
        from dateutil import parser as date_parser
        
        expression = expression.lower().strip()
        now = datetime.now()
        
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
        
        # Pattern: "in X hours"
        match = re.search(r'in (\d+)\s*hour', expression)
        if match:
            hours = int(match.group(1))
            return now + timedelta(hours=hours)
        
        # Try general date parsing
        try:
            result = date_parser.parse(expression, fuzzy=True)
            if result > now:
                return result
        except:
            pass
        
        return None