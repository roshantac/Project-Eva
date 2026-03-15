"""
Tool execution engine for handling external tool calls
"""

import os
import re
import json
from typing import Dict, Any, Optional, List, Callable
from datetime import datetime
from app.services.weather_service import WeatherService
from app.services.search_service import SearchService
from app.services.reminder_service import ReminderService
from app.services.notes_service import NotesService
from app.services.calendar_service import CalendarService
from app.utils.logger import logger


class ToolEngine:
    """Engine for detecting and executing tools"""
    
    def __init__(self):
        self.weather_service = WeatherService()
        self.search_service = SearchService()
        self.reminder_service = ReminderService()
        self.notes_service = NotesService()
        self.calendar_service = CalendarService()
        self.tools = self._initialize_tools()
    
    def _initialize_tools(self) -> Dict[str, Dict[str, Any]]:
        """Initialize available tools with their definitions and handlers"""
        return {
            'get_current_weather': {
                'name': 'get_current_weather',
                'description': 'Get the current weather for a specific location',
                'parameters': {
                    'type': 'object',
                    'properties': {
                        'location': {
                            'type': 'string',
                            'description': 'The city and country, e.g. London, UK'
                        }
                    },
                    'required': ['location']
                },
                'handler': self._handle_current_weather
            },
            
            'get_weather_forecast': {
                'name': 'get_weather_forecast',
                'description': 'Get weather forecast for a specific location for the next few days',
                'parameters': {
                    'type': 'object',
                    'properties': {
                        'location': {
                            'type': 'string',
                            'description': 'The city and country, e.g. London, UK'
                        },
                        'days': {
                            'type': 'number',
                            'description': 'Number of days for forecast (1-5)',
                            'default': 5
                        }
                    },
                    'required': ['location']
                },
                'handler': self._handle_weather_forecast
            },
            
            'get_weather_advice': {
                'name': 'get_weather_advice',
                'description': 'Get weather-based advice (e.g., should I carry an umbrella?)',
                'parameters': {
                    'type': 'object',
                    'properties': {
                        'location': {
                            'type': 'string',
                            'description': 'The city and country, e.g. London, UK'
                        }
                    },
                    'required': ['location']
                },
                'handler': self._handle_weather_advice
            },
            
            'search_web': {
                'name': 'search_web',
                'description': 'Search the internet for information on any topic. Returns summarized results from web search.',
                'parameters': {
                    'type': 'object',
                    'properties': {
                        'query': {
                            'type': 'string',
                            'description': 'The search query or question to search for'
                        },
                        'max_results': {
                            'type': 'number',
                            'description': 'Maximum number of results to return (default: 3)',
                            'default': 3
                        }
                    },
                    'required': ['query']
                },
                'handler': self._handle_web_search
            },
            
            'set_reminder': {
                'name': 'set_reminder',
                'description': 'Set a reminder that will notify the user at a specific time with voice notification.',
                'parameters': {
                    'type': 'object',
                    'properties': {
                        'message': {
                            'type': 'string',
                            'description': 'The reminder message to deliver'
                        },
                        'time_expression': {
                            'type': 'string',
                            'description': 'When to remind (e.g., "in 5 minutes", "tomorrow at 3pm", "at 5:30pm")'
                        },
                        'user_id': {
                            'type': 'string',
                            'description': 'User ID'
                        },
                        'user_sid': {
                            'type': 'string',
                            'description': 'Socket ID for notification'
                        }
                    },
                    'required': ['message', 'time_expression', 'user_id', 'user_sid']
                },
                'handler': self._handle_set_reminder
            },
            
            'save_note': {
                'name': 'save_note',
                'description': 'Save a note or list (e.g., grocery list, todo list, shopping list) that persists until deleted.',
                'parameters': {
                    'type': 'object',
                    'properties': {
                        'title': {
                            'type': 'string',
                            'description': 'Title/name of the note (e.g., "grocery list", "todo", "shopping list")'
                        },
                        'content': {
                            'type': 'string',
                            'description': 'The content to save'
                        },
                        'user_id': {
                            'type': 'string',
                            'description': 'User ID'
                        }
                    },
                    'required': ['title', 'content', 'user_id']
                },
                'handler': self._handle_save_note
            },
            
            'get_note': {
                'name': 'get_note',
                'description': 'Retrieve a saved note or list by its title.',
                'parameters': {
                    'type': 'object',
                    'properties': {
                        'title': {
                            'type': 'string',
                            'description': 'Title/name of the note to retrieve'
                        },
                        'user_id': {
                            'type': 'string',
                            'description': 'User ID'
                        }
                    },
                    'required': ['title', 'user_id']
                },
                'handler': self._handle_get_note
            },
            
            'delete_note': {
                'name': 'delete_note',
                'description': 'Delete a saved note or list.',
                'parameters': {
                    'type': 'object',
                    'properties': {
                        'title': {
                            'type': 'string',
                            'description': 'Title/name of the note to delete'
                        },
                        'user_id': {
                            'type': 'string',
                            'description': 'User ID'
                        }
                    },
                    'required': ['title', 'user_id']
                },
                'handler': self._handle_delete_note
            },
            
            'list_notes': {
                'name': 'list_notes',
                'description': 'List all saved notes and lists.',
                'parameters': {
                    'type': 'object',
                    'properties': {
                        'user_id': {
                            'type': 'string',
                            'description': 'User ID'
                        }
                    },
                    'required': ['user_id']
                },
                'handler': self._handle_list_notes
            },
            
            'schedule_meeting': {
                'name': 'schedule_meeting',
                'description': 'Schedule a meeting or event in the calendar with a specific time and duration.',
                'parameters': {
                    'type': 'object',
                    'properties': {
                        'title': {
                            'type': 'string',
                            'description': 'Meeting title or event name'
                        },
                        'time_expression': {
                            'type': 'string',
                            'description': 'When the meeting starts (e.g., "tomorrow at 3pm", "at 5:30pm", "next Monday at 10am")'
                        },
                        'duration_minutes': {
                            'type': 'number',
                            'description': 'Duration in minutes (default: 60)',
                            'default': 60
                        },
                        'description': {
                            'type': 'string',
                            'description': 'Optional meeting description'
                        },
                        'location': {
                            'type': 'string',
                            'description': 'Optional meeting location'
                        },
                        'user_id': {
                            'type': 'string',
                            'description': 'User ID'
                        }
                    },
                    'required': ['title', 'time_expression', 'user_id']
                },
                'handler': self._handle_schedule_meeting
            },
            
            'get_todays_calendar': {
                'name': 'get_todays_calendar',
                'description': 'Get all events scheduled for today with times and details.',
                'parameters': {
                    'type': 'object',
                    'properties': {
                        'user_id': {
                            'type': 'string',
                            'description': 'User ID'
                        }
                    },
                    'required': ['user_id']
                },
                'handler': self._handle_get_todays_calendar
            },
            
            'cancel_meeting': {
                'name': 'cancel_meeting',
                'description': 'Cancel a scheduled meeting or event.',
                'parameters': {
                    'type': 'object',
                    'properties': {
                        'event_id': {
                            'type': 'string',
                            'description': 'Event ID to cancel'
                        },
                        'user_id': {
                            'type': 'string',
                            'description': 'User ID'
                        }
                    },
                    'required': ['event_id', 'user_id']
                },
                'handler': self._handle_cancel_meeting
            },
            
            'list_all_meetings': {
                'name': 'list_all_meetings',
                'description': 'List all scheduled meetings (today and upcoming). Use this when user asks to see all meetings, list meetings, or show scheduled meetings.',
                'parameters': {
                    'type': 'object',
                    'properties': {
                        'user_id': {
                            'type': 'string',
                            'description': 'User ID'
                        }
                    },
                    'required': ['user_id']
                },
                'handler': self._handle_list_all_meetings
            }
        }
    
    async def _handle_current_weather(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle current weather tool call"""
        weather = await self.weather_service.get_current_weather(params['location'])
        return {
            'success': True,
            'data': weather,
            'formatted': self.weather_service.format_weather_response(weather)
        }
    
    async def _handle_weather_forecast(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle weather forecast tool call"""
        forecast = await self.weather_service.get_forecast(
            params['location'],
            params.get('days', 5)
        )
        return {
            'success': True,
            'data': forecast,
            'formatted': self.weather_service.format_forecast_response(forecast)
        }
    
    async def _handle_weather_advice(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle weather advice tool call"""
        weather = await self.weather_service.get_current_weather(params['location'])
        advice = self.weather_service.get_weather_advice(weather)
        should_carry_umbrella = self.weather_service.should_carry_umbrella(weather)
        
        return {
            'success': True,
            'data': {
                'weather': weather,
                'advice': advice,
                'shouldCarryUmbrella': should_carry_umbrella
            },
            'formatted': f"{self.weather_service.format_weather_response(weather)}\n\n{advice}"
        }
    
    async def _handle_web_search(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle web search tool call"""
        query = params['query']
        max_results = params.get('max_results', 3)
        
        result = await self.search_service.search_and_summarize(query, max_results)
        
        if not result.get('success'):
            return {
                'success': False,
                'error': result.get('error', 'Search failed'),
                'formatted': result.get('message', 'Failed to search the web')
            }
        
        return {
            'success': True,
            'data': result,
            'formatted': result['formatted']
        }
    
    async def _handle_set_reminder(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle set reminder tool call"""
        message = params['message']
        time_expression = params['time_expression']
        user_id = params['user_id']
        user_sid = params['user_sid']
        
        # Parse time expression
        trigger_time = self.reminder_service.parse_time_expression(time_expression)
        
        if not trigger_time:
            return {
                'success': False,
                'error': 'Could not parse time expression',
                'formatted': f"Sorry, I couldn't understand when you want to be reminded. Please try expressions like 'in 5 minutes', 'tomorrow at 3pm', or 'at 5:30pm'."
            }
        
        # Create reminder
        result = await self.reminder_service.create_reminder(
            message=message,
            trigger_time=trigger_time,
            user_id=user_id,
            user_sid=user_sid,
            voice_enabled=True
        )
        
        if result.get('success'):
            formatted_time = trigger_time.strftime('%B %d at %I:%M %p')
            return {
                'success': True,
                'data': result['reminder'],
                'formatted': f"✅ Reminder set! I'll remind you about '{message}' on {formatted_time}."
            }
        else:
            return {
                'success': False,
                'error': result.get('error', 'Failed to set reminder'),
                'formatted': 'Sorry, I couldn\'t set the reminder. Please try again.'
            }
    
    async def _handle_save_note(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle save note tool call"""
        title = params['title']
        content = params['content']
        user_id = params['user_id']
        
        result = await self.notes_service.save_note(user_id, title, content, 'list')
        
        if result.get('success'):
            return {
                'success': True,
                'data': result,
                'formatted': result['message']
            }
        else:
            return {
                'success': False,
                'error': result.get('error', 'Failed to save note'),
                'formatted': result.get('message', f'Failed to save {title}')
            }
    
    async def _handle_get_note(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle get note tool call"""
        title = params['title']
        user_id = params['user_id']
        
        result = await self.notes_service.get_note(user_id, title)
        
        if result.get('success'):
            note = result['note']
            formatted_content = self.notes_service.format_note_content(note)
            return {
                'success': True,
                'data': note,
                'formatted': formatted_content
            }
        else:
            return {
                'success': False,
                'error': result.get('error', 'Note not found'),
                'formatted': result.get('message', f'Could not find {title}')
            }
    
    async def _handle_delete_note(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle delete note tool call"""
        title = params['title']
        user_id = params['user_id']
        
        result = await self.notes_service.delete_note(user_id, title)
        
        if result.get('success'):
            return {
                'success': True,
                'data': result,
                'formatted': result['message']
            }
        else:
            return {
                'success': False,
                'error': result.get('error', 'Failed to delete note'),
                'formatted': result.get('message', f'Could not delete {title}')
            }
    
    async def _handle_list_notes(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle list notes tool call"""
        user_id = params['user_id']
        
        result = await self.notes_service.list_all_notes(user_id)
        
        if result.get('success'):
            if result.get('count', 0) == 0:
                return {
                    'success': True,
                    'data': result,
                    'formatted': result['message']
                }
            
            # Format the list
            notes_list = result['notes']
            formatted = f"{result['message']}\n\n"
            for i, note in enumerate(notes_list, 1):
                formatted += f"{i}. **{note['title']}** ({note['type']})\n"
            
            return {
                'success': True,
                'data': result,
                'formatted': formatted
            }
        else:
            return {
                'success': False,
                'error': result.get('error', 'Failed to list notes'),
                'formatted': result.get('message', 'Could not list notes')
            }
    async def _handle_schedule_meeting(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle schedule meeting tool call"""
        title = params['title']
        time_expression = params['time_expression']
        user_id = params['user_id']
        duration_minutes = params.get('duration_minutes', 60)
        description = params.get('description', '')
        location = params.get('location', '')
        
        # Parse time expression
        start_time = self.calendar_service.parse_time_expression(time_expression)
        
        if not start_time:
            return {
                'success': False,
                'error': 'Could not parse time expression',
                'formatted': f"Sorry, I couldn't understand the time '{time_expression}'. Please try something like 'tomorrow at 3pm' or 'at 5:30pm'."
            }
        
        result = await self.calendar_service.schedule_meeting(
            title=title,
            start_time=start_time,
            duration_minutes=duration_minutes,
            user_id=user_id,
            description=description,
            location=location
        )
        
        if result.get('success'):
            return {
                'success': True,
                'data': result['event'],
                'formatted': result['message']
            }
        else:
            return {
                'success': False,
                'error': result.get('error', 'Failed to schedule meeting'),
                'formatted': 'Sorry, I couldn\'t schedule the meeting. Please try again.'
            }
    
    async def _handle_get_todays_calendar(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle get today's calendar tool call"""
        user_id = params['user_id']
        
        result = await self.calendar_service.get_todays_calendar(user_id)
        
        if result.get('success'):
            return {
                'success': True,
                'data': result,
                'formatted': result['message']
            }
        else:
            return {
                'success': False,
                'error': result.get('error', 'Failed to get calendar'),
                'formatted': result.get('message', 'Sorry, I couldn\'t retrieve your calendar.')
            }
    
    async def _handle_cancel_meeting(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle cancel meeting tool call"""
        event_id = params['event_id']
        user_id = params['user_id']
        
        result = await self.calendar_service.cancel_event(event_id, user_id)
        
        if result.get('success'):
            return {
                'success': True,
                'data': result,
                'formatted': result['message']
            }
        else:
            return {
                'success': False,
                'error': result.get('error', 'Failed to cancel meeting'),
                'formatted': result.get('message', 'Sorry, I couldn\'t cancel the meeting.')
            }
    
    async def _handle_list_all_meetings(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle list all meetings tool call"""
        user_id = params['user_id']
        
        result = await self.calendar_service.list_all_meetings(user_id)
        
        if result.get('success'):
            return {
                'success': True,
                'data': result,
                'formatted': result['message']
            }
        else:
            return {
                'success': False,
                'error': result.get('error', 'Failed to list meetings'),
                'formatted': result.get('message', 'Sorry, I couldn\'t retrieve your meetings.')
            }
    
    
    def get_tool_definitions(self) -> List[Dict[str, Any]]:
        """
        Get tool definitions for LLM function calling
        
        Returns:
            List of tool definitions
        """
        return [
            {
                'name': tool['name'],
                'description': tool['description'],
                'parameters': tool['parameters']
            }
            for tool in self.tools.values()
        ]
    
    async def execute_tool(self, tool_name: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a tool by name
        
        Args:
            tool_name: Name of the tool to execute
            parameters: Tool parameters
            
        Returns:
            Tool execution result
        """
        try:
            tool = self.tools.get(tool_name)
            
            if not tool:
                raise ValueError(f"Tool not found: {tool_name}")
            
            logger.info(f"Executing tool: {tool_name} with params: {parameters}")
            
            result = await tool['handler'](parameters)
            
            logger.info(f"Tool {tool_name} executed successfully")
            return result
        except Exception as error:
            logger.error(f"Error executing tool {tool_name}: {error}")
            return {
                'success': False,
                'error': str(error)
            }
    
    async def detect_and_execute_tools(
        self,
        user_message: str,
        llm_service: Optional[Any] = None,
        user_id: str = 'anonymous',
        user_sid: str = ''
    ) -> Dict[str, Any]:
        """
        Detect if tools are needed and execute them
        
        Args:
            user_message: User's message
            llm_service: Optional LLM service (unused but kept for compatibility)
            user_id: User ID for reminders
            user_sid: Socket ID for reminders
            
        Returns:
            Dictionary with tool execution results
        """
        try:
            # Check for note operations first
            note_action = self.detect_note_query(user_message)
            if note_action:
                note_data = self.extract_note_data(user_message, note_action)
                if note_data:
                    logger.info(f"📝 Note action triggered: {note_action} - {note_data.get('title', 'N/A')}")
                    
                    if note_action == 'save':
                        result = await self.execute_tool('save_note', {
                            'title': note_data['title'],
                            'content': note_data['content'],
                            'user_id': user_id
                        })
                    elif note_action == 'get':
                        result = await self.execute_tool('get_note', {
                            'title': note_data['title'],
                            'user_id': user_id
                        })
                    elif note_action == 'delete':
                        result = await self.execute_tool('delete_note', {
                            'title': note_data['title'],
                            'user_id': user_id
                        })
                    elif note_action == 'list':
                        result = await self.execute_tool('list_notes', {
                            'user_id': user_id
                        })
                    
                    if result.get('success'):
                        return {
                            'toolUsed': True,
                            'toolName': f'{note_action}_note' if note_action != 'list' else 'list_notes',
                            'result': result
                        }
            
            # Check for calendar operations
            calendar_action = self.detect_calendar_query(user_message)
            if calendar_action:
                calendar_data = self.extract_calendar_data(user_message, calendar_action)
                if calendar_data:
                    logger.info(f"📅 Calendar action triggered: {calendar_action}")
                    
                    if calendar_action == 'schedule':
                        result = await self.execute_tool('schedule_meeting', {
                            'title': calendar_data['title'],
                            'time_expression': calendar_data['time'],
                            'duration_minutes': calendar_data.get('duration', 60),
                            'description': calendar_data.get('description', ''),
                            'location': calendar_data.get('location', ''),
                            'user_id': user_id
                        })
                    elif calendar_action == 'get_today':
                        result = await self.execute_tool('get_todays_calendar', {
                            'user_id': user_id
                        })
                    elif calendar_action == 'list_all':
                        result = await self.execute_tool('list_all_meetings', {
                            'user_id': user_id
                        })
                    
                    if result.get('success'):
                        tool_name_map = {
                            'schedule': 'schedule_meeting',
                            'get_today': 'get_todays_calendar',
                            'list_all': 'list_all_meetings'
                        }
                        return {
                            'toolUsed': True,
                            'toolName': tool_name_map.get(calendar_action, 'get_todays_calendar'),
                            'result': result
                        }
            
            # Check for reminder
            needs_reminder = self.detect_reminder_query(user_message)
            if needs_reminder:
                reminder_data = self.extract_reminder_data(user_message)
                if reminder_data:
                    logger.info(f"⏰ Reminder triggered: {reminder_data['message']} at {reminder_data['time']}")
                    result = await self.execute_tool('set_reminder', {
                        'message': reminder_data['message'],
                        'time_expression': reminder_data['time'],
                        'user_id': user_id,
                        'user_sid': user_sid
                    })
                    
                    if result.get('success'):
                        return {
                            'toolUsed': True,
                            'toolName': 'set_reminder',
                            'result': result
                        }
            
            # Check for web search
            needs_search = self.detect_search_query(user_message)
            if needs_search:
                query = self.extract_search_query(user_message)
                if query:
                    logger.info(f"🔍 Web search triggered for: {query}")
                    result = await self.execute_tool('search_web', {'query': query, 'max_results': 3})
                    
                    if result.get('success'):
                        return {
                            'toolUsed': True,
                            'toolName': 'search_web',
                            'result': result
                        }
            
            # Check for weather queries
            needs_weather = self.detect_weather_query(user_message)
            
            if needs_weather:
                if not os.getenv('OPENWEATHER_API_KEY') or \
                   os.getenv('OPENWEATHER_API_KEY') == 'your_openweather_api_key_here':
                    logger.warning('Weather tool triggered but API key not configured')
                    return {
                        'toolUsed': False,
                        'error': 'Weather API not configured',
                        'message': 'Weather features require an OpenWeather API key. Get one free at: https://openweathermap.org/api'
                    }
                
                location = self.extract_location(user_message)
                
                if location:
                    tool_name = 'get_current_weather'
                    parameters = {'location': location}
                    
                    lower_message = user_message.lower()
                    if any(keyword in lower_message for keyword in ['forecast', 'tomorrow', 'next', 'week']):
                        tool_name = 'get_weather_forecast'
                        parameters['days'] = 5
                    elif any(keyword in lower_message for keyword in ['umbrella', 'jacket', 'should i']):
                        tool_name = 'get_weather_advice'
                    
                    result = await self.execute_tool(tool_name, parameters)
                    
                    if not result.get('success'):
                        logger.warning(f"Weather tool failed: {result.get('error')}")
                        return {
                            'toolUsed': False,
                            'error': result.get('error'),
                            'message': 'Unable to fetch weather data. Please check your API key configuration.'
                        }
                    
                    return {
                        'toolUsed': True,
                        'toolName': tool_name,
                        'result': result
                    }
            
            return {
                'toolUsed': False
            }
        except Exception as error:
            logger.error(f"Error in tool detection: {error}")
            return {
                'toolUsed': False,
                'error': str(error)
            }
    
    def detect_note_query(self, message: str) -> Optional[str]:
        """
        Detect if message is a note operation (save, get, delete, list)
        
        Args:
            message: User message
            
        Returns:
            Action type ('save', 'get', 'delete', 'list') or None
        """
        lower_message = message.lower()
        
        # Save/Remember patterns
        save_keywords = [
            'remember', 'save', 'note', 'write down', 'keep track',
            'add to', 'put in', 'store', 'record'
        ]
        
        # Get/Retrieve patterns
        get_keywords = [
            'what\'s', 'what is', 'show me', 'tell me', 'get', 'retrieve',
            'read', 'what\'s in', 'what\'s on'
        ]
        
        # Delete patterns
        delete_keywords = [
            'delete', 'remove', 'clear', 'erase', 'forget'
        ]
        
        # List patterns
        list_keywords = [
            'list all', 'show all', 'what notes', 'what lists',
            'all my notes', 'all my lists'
        ]
        
        # Check for list action
        if any(keyword in lower_message for keyword in list_keywords):
            return 'list'
        
        # Check for delete action
        if any(keyword in lower_message for keyword in delete_keywords):
            if any(word in lower_message for word in ['list', 'note', 'grocery', 'todo', 'shopping']):
                return 'delete'
        
        # Check for get action
        if any(keyword in lower_message for keyword in get_keywords):
            if any(word in lower_message for word in ['list', 'note', 'grocery', 'todo', 'shopping']):
                return 'get'
        
        # Check for save action
        if any(keyword in lower_message for keyword in save_keywords):
            if any(word in lower_message for word in ['list', 'note', 'grocery', 'todo', 'shopping']):
                return 'save'
        
        return None
    
    def extract_note_data(self, message: str, action: str) -> Optional[Dict[str, str]]:
        """
        Extract note data from message
        
        Args:
            message: User message
            action: Action type ('save', 'get', 'delete', 'list')
            
        Returns:
            Dictionary with 'title' and optionally 'content'
        """
        lower_message = message.lower()
        
        if action == 'list':
            return {}  # No data needed for list
        
        # Common list/note names
        common_titles = ['grocery list', 'shopping list', 'todo list', 'to-do list', 'notes']
        
        # Try to find a common title
        for title in common_titles:
            if title in lower_message:
                if action == 'save':
                    # Extract content after the title
                    patterns = [
                        rf'{title}[:\s]+(.+?)(?:\?|$)',
                        rf'(?:remember|save|note|write down)\s+(?:that\s+)?(.+?)\s+(?:in|to|on)\s+(?:my\s+)?{title}',
                        rf'(?:add|put)\s+(.+?)\s+(?:to|in|on)\s+(?:my\s+)?{title}',
                    ]
                    
                    for pattern in patterns:
                        match = re.search(pattern, lower_message, re.IGNORECASE)
                        if match:
                            content = match.group(1).strip()
                            return {'title': title, 'content': content}
                    
                    # If no content pattern matched, try to extract everything after "remember"
                    remember_match = re.search(r'(?:remember|save|note)\s+(.+)', lower_message, re.IGNORECASE)
                    if remember_match:
                        full_text = remember_match.group(1).strip()
                        # Remove the title from content
                        content = full_text.replace(title, '').strip()
                        content = re.sub(r'^[:\s]+', '', content)  # Remove leading colons/spaces
                        if content:
                            return {'title': title, 'content': content}
                else:
                    # For get/delete, just return the title
                    return {'title': title}
        
        # If no common title found, try generic patterns
        if action == 'save':
            patterns = [
                r'(?:remember|save|note)\s+(?:that\s+)?(.+?)\s+(?:as|in|to)\s+(?:my\s+)?(.+?)(?:\?|$)',
                r'(?:add|put)\s+(.+?)\s+(?:to|in)\s+(?:my\s+)?(.+?)(?:\?|$)',
            ]
            
            for pattern in patterns:
                match = re.search(pattern, lower_message, re.IGNORECASE)
                if match:
                    content = match.group(1).strip()
                    title = match.group(2).strip()
                    return {'title': title, 'content': content}
        
        elif action in ['get', 'delete']:
            patterns = [
                r'(?:what\'s|show me|tell me|get|delete|remove)\s+(?:the\s+)?(?:my\s+)?(.+?)(?:\?|$)',
            ]
            
            for pattern in patterns:
                match = re.search(pattern, lower_message, re.IGNORECASE)
                if match:
                    title = match.group(1).strip()
                    # Clean up common words
                    title = re.sub(r'\s+list$', ' list', title)
                    return {'title': title}
        
        return None
    
    def detect_reminder_query(self, message: str) -> bool:
        """
        Detect if message is a reminder request
        
        Args:
            message: User message
            
        Returns:
            True if reminder query detected
        """
        reminder_keywords = [
            'remind me', 'reminder', 'set a reminder', 'create a reminder',
            'schedule a reminder', 'alert me', 'notify me', 'wake me',
            'don\'t forget', 'remember to', 'set alarm'
        ]
        
        lower_message = message.lower()
        return any(keyword in lower_message for keyword in reminder_keywords)
    
    def extract_reminder_data(self, message: str) -> Optional[Dict[str, str]]:
        """
        Extract reminder message and time from user message
        
        Args:
            message: User message
            
        Returns:
            Dictionary with 'message' and 'time' or None
        """
        lower_message = message.lower()
        
        # Patterns to extract reminder data
        patterns = [
            r'remind me (?:to )?(.+?) (?:in|at|tomorrow|after) (.+?)(?:\?|$)',
            r'remind me (?:in|at|tomorrow|after) (.+?) (?:to )?(.+?)(?:\?|$)',
            r'set (?:a )?reminder (?:to )?(.+?) (?:in|at|for|tomorrow) (.+?)(?:\?|$)',
            r'set (?:a )?reminder (?:for|in|at|tomorrow) (.+?) (?:to )?(.+?)(?:\?|$)',
            r'alert me (?:to )?(.+?) (?:in|at|tomorrow) (.+?)(?:\?|$)',
            r'notify me (?:to )?(.+?) (?:in|at|tomorrow) (.+?)(?:\?|$)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, lower_message, re.IGNORECASE)
            if match:
                # Determine which group is message and which is time
                group1 = match.group(1).strip()
                group2 = match.group(2).strip()
                
                # Check if group1 looks like a time expression
                time_indicators = ['minute', 'hour', 'day', 'week', 'pm', 'am', 'tomorrow', 'o\'clock']
                if any(indicator in group1.lower() for indicator in time_indicators):
                    return {'time': group1, 'message': group2}
                else:
                    return {'message': group1, 'time': group2}
        
        # Simpler pattern: "remind me to X"
        simple_match = re.search(r'remind me (?:to )?(.+?)(?:\?|$)', lower_message, re.IGNORECASE)
        if simple_match:
            full_text = simple_match.group(1).strip()
            # Try to split by time indicators
            for indicator in [' in ', ' at ', ' tomorrow', ' after ']:
                if indicator in full_text:
                    parts = full_text.split(indicator, 1)
                    return {'message': parts[0].strip(), 'time': indicator.strip() + ' ' + parts[1].strip()}
            
            # Default: assume message is everything, time is "in 1 hour"
            return {'message': full_text, 'time': 'in 1 hour'}
        
        return None
    
    def detect_search_query(self, message: str) -> bool:
        """
        Detect if message is a web search query
        
        Args:
            message: User message
            
        Returns:
            True if search query detected
        """
        search_keywords = [
            'search', 'look up', 'find', 'google', 'what is', 'who is',
            'tell me about', 'information about', 'learn about', 'research',
            'find out', 'look for', 'search for', 'latest news', 'recent news',
            'current news', 'news about', 'get news', 'fetch', 'retrieve',
            'get information', 'get latest', 'get recent', 'get current',
            'from internet', 'from the web', 'online', 'browse', 'check online'
        ]
        
        lower_message = message.lower()
        
        # Check for direct keyword matches
        if any(keyword in lower_message for keyword in search_keywords):
            return True
        
        # Check for question patterns that likely need internet search
        question_patterns = [
            r'what\'?s? (?:the )?latest',
            r'what\'?s? (?:the )?current',
            r'what\'?s? (?:the )?recent',
            r'what\'?s? happening',
            r'what\'?s? new',
            r'can you (?:get|find|search|look up)',
            r'could you (?:get|find|search|look up)',
            r'please (?:get|find|search|look up)',
        ]
        
        for pattern in question_patterns:
            if re.search(pattern, lower_message):
                return True
        
        return False
    
    def extract_search_query(self, message: str) -> Optional[str]:
        """
        Extract search query from message
        
        Args:
            message: User message
            
        Returns:
            Extracted search query or None
        """
        lower_message = message.lower()
        
        # Patterns to extract query - more comprehensive
        patterns = [
            r'search (?:for |about )?(.+?)(?:\?|$)',
            r'look up (.+?)(?:\?|$)',
            r'find (?:out )?(?:about )?(.+?)(?:\?|$)',
            r'google (.+?)(?:\?|$)',
            r'what is (.+?)(?:\?|$)',
            r'who is (.+?)(?:\?|$)',
            r'tell me about (.+?)(?:\?|$)',
            r'information about (.+?)(?:\?|$)',
            r'learn about (.+?)(?:\?|$)',
            r'research (.+?)(?:\?|$)',
            r'(?:get|fetch|retrieve) (?:the )?(?:latest|recent|current) (.+?)(?:\?|$)',
            r'(?:latest|recent|current) (?:news|information|updates?) (?:about|on|for) (.+?)(?:\?|$)',
            r'(?:latest|recent|current) (.+?) news(?:\?|$)',
            r'news (?:about|on|for) (.+?)(?:\?|$)',
            r'can you (?:get|find|search|look up) (.+?)(?:\?|$)',
            r'could you (?:get|find|search|look up) (.+?)(?:\?|$)',
            r'please (?:get|find|search|look up) (.+?)(?:\?|$)',
            r'what\'?s? (?:the )?(?:latest|recent|current) (?:on |about )?(.+?)(?:\?|$)',
            r'what\'?s? happening (?:with |in )?(.+?)(?:\?|$)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, lower_message, re.IGNORECASE)
            if match and match.group(1):
                query = match.group(1).strip()
                # Clean up common trailing words
                query = re.sub(r'\s+from\s+(?:the\s+)?(?:internet|web|online)$', '', query, flags=re.IGNORECASE)
                return query
        
        # If no pattern matches but search keywords found, try to extract meaningful part
        if self.detect_search_query(message):
            # Remove common prefixes and get the main query
            prefixes_to_remove = [
                'can you get', 'could you get', 'please get',
                'can you find', 'could you find', 'please find',
                'can you search', 'could you search', 'please search',
                'search for', 'search about', 'search',
                'look up', 'find out about', 'find about', 'find',
                'google', 'tell me about', 'get', 'fetch', 'retrieve'
            ]
            
            query = message
            for prefix in prefixes_to_remove:
                if lower_message.startswith(prefix):
                    query = message[len(prefix):].strip()
                    break
            
            # Clean up
            query = re.sub(r'\s+from\s+(?:the\s+)?(?:internet|web|online)$', '', query, flags=re.IGNORECASE)
            query = query.strip('?.,! ')
            
            if query and len(query) > 3:  # Ensure we have a meaningful query
                return query
        
        return None
    
    def detect_weather_query(self, message: str) -> bool:
        """
        Detect if message is a weather query
        
        Args:
            message: User message
            
        Returns:
            True if weather query detected
        """
        weather_keywords = [
            'weather', 'temperature', 'forecast', 'rain', 'snow', 'sunny',
            'cloudy', 'hot', 'cold', 'warm', 'umbrella', 'jacket', 'climate'
        ]
        
        lower_message = message.lower()
        return any(keyword in lower_message for keyword in weather_keywords)
    
    def extract_location(self, message: str) -> Optional[str]:
        """
        Extract location from message
        
        Args:
            message: User message
            
        Returns:
            Extracted location or None
        """
        patterns = [
            r'(?:in|at|for)\s+([A-Z][a-zA-Z\s]+?)(?:\s+weather|\s+forecast|[?.!]|$)',
            r'weather\s+(?:in|at|for)\s+([A-Z][a-zA-Z\s]+?)(?:[?.!]|$)',
            r'([A-Z][a-zA-Z\s]+?)\s+weather',
            r'(?:in|at)\s+([A-Z][a-zA-Z\s]+?)$'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, message, re.IGNORECASE)
            if match and match.group(1):
                return match.group(1).strip()
        
        default_locations = ['London', 'New York', 'Tokyo', 'Paris', 'Sydney']
        for location in default_locations:
            if location.lower() in message.lower():
                return location
        
        return None
    def detect_calendar_query(self, message: str) -> Optional[str]:
        """
        Detect if message is a calendar query
        
        Args:
            message: User message
            
        Returns:
            'schedule' for scheduling, 'get_today' for viewing today's calendar,
            'list_all' for listing all meetings, None otherwise
        """
        lower_message = message.lower()
        
        # Check for "list all meetings" queries first (more specific)
        list_all_keywords = [
            'list all meetings', 'list meetings', 'show all meetings',
            'all my meetings', 'all scheduled meetings', 'list my meetings',
            'show my meetings', 'what meetings do i have scheduled',
            'show scheduled meetings', 'list scheduled meetings',
            'all meetings', 'my meetings'
        ]
        
        if any(keyword in lower_message for keyword in list_all_keywords):
            return 'list_all'
        
        # Check for "get today's calendar" queries
        get_calendar_keywords = [
            'today\'s calendar', 'todays calendar', 'calendar for today',
            'what\'s on my calendar', 'whats on my calendar',
            'show my calendar', 'show calendar', 'my calendar today',
            'what do i have today', 'what\'s scheduled today',
            'my schedule today', 'today\'s schedule', 'todays schedule',
            'what meetings do i have today', 'do i have any meetings today'
        ]
        
        if any(keyword in lower_message for keyword in get_calendar_keywords):
            return 'get_today'
        
        # Check for scheduling keywords
        schedule_keywords = [
            'schedule a meeting', 'schedule meeting', 'book a meeting',
            'set up a meeting', 'arrange a meeting', 'plan a meeting',
            'schedule an event', 'create a meeting', 'add to calendar',
            'put on calendar', 'calendar event', 'meeting at', 'meeting on'
        ]
        
        if any(keyword in lower_message for keyword in schedule_keywords):
            return 'schedule'
        
        # Check for time-based scheduling patterns
        time_patterns = [
            r'meeting\s+(?:at|on|for|tomorrow|next)',
            r'schedule\s+(?:at|on|for|tomorrow|next)',
            r'(?:tomorrow|next\s+\w+)\s+at\s+\d',
        ]
        
        for pattern in time_patterns:
            if re.search(pattern, lower_message):
                return 'schedule'
        
        return None
    
    def extract_calendar_data(self, message: str, action: str) -> Optional[Dict[str, Any]]:
        """
        Extract calendar data from message
        
        Args:
            message: User message
            action: 'schedule', 'get_today', or 'list_all'
            
        Returns:
            Dictionary with calendar data or None
        """
        if action == 'get_today' or action == 'list_all':
            # No extraction needed for getting today's calendar or listing all meetings
            return {}
        
        if action == 'schedule':
            lower_message = message.lower()
            
            # Extract meeting title
            title = None
            title_patterns = [
                r'schedule\s+(?:a\s+)?(?:meeting\s+)?(?:called\s+|named\s+|about\s+)?["\']([^"\']+)["\']',
                r'schedule\s+(?:a\s+)?(?:meeting\s+)?(?:called\s+|named\s+|about\s+)?(\w+(?:\s+\w+){0,4})\s+(?:at|on|for|tomorrow)',
                r'meeting\s+(?:called\s+|named\s+|about\s+)?["\']([^"\']+)["\']',
                r'(?:schedule|book|create)\s+["\']([^"\']+)["\']',
            ]
            
            for pattern in title_patterns:
                match = re.search(pattern, message, re.IGNORECASE)
                if match:
                    title = match.group(1).strip()
                    break
            
            # If no title found, try to extract from context
            if not title:
                # Look for words between schedule/meeting and time expression
                match = re.search(r'(?:schedule|meeting|book)\s+(?:a\s+)?(\w+(?:\s+\w+){0,3})\s+(?:at|on|for|tomorrow)', lower_message)
                if match:
                    potential_title = match.group(1).strip()
                    # Filter out common words
                    if potential_title not in ['a', 'an', 'the', 'with', 'for', 'about']:
                        title = potential_title
            
            if not title:
                title = "Meeting"  # Default title
            
            # Extract time expression
            time_expression = None
            time_patterns = [
                r'(?:at|on|for)\s+(tomorrow\s+at\s+\d+(?::\d+)?\s*(?:am|pm)?)',
                r'(?:at|on|for)\s+(next\s+\w+\s+at\s+\d+(?::\d+)?\s*(?:am|pm)?)',
                r'(?:at|on)\s+(\d+(?::\d+)?\s*(?:am|pm))',
                r'(tomorrow\s+at\s+\d+(?::\d+)?\s*(?:am|pm)?)',
                r'(at\s+\d+(?::\d+)?\s*(?:am|pm))',
                r'(in\s+\d+\s+hours?)',
            ]
            
            for pattern in time_patterns:
                match = re.search(pattern, lower_message)
                if match:
                    time_expression = match.group(1).strip()
                    break
            
            if not time_expression:
                # Try to find any time-like pattern
                match = re.search(r'(\d+(?::\d+)?\s*(?:am|pm))', lower_message)
                if match:
                    time_expression = f"at {match.group(1)}"
            
            if not time_expression:
                return None  # Can't schedule without time
            
            # Extract duration (optional)
            duration = 60  # Default 1 hour
            duration_match = re.search(r'(?:for|lasting)\s+(\d+)\s*(?:minutes?|mins?|hours?|hrs?)', lower_message)
            if duration_match:
                amount = int(duration_match.group(1))
                if 'hour' in lower_message or 'hr' in lower_message:
                    duration = amount * 60
                else:
                    duration = amount
            
            # Extract location (optional)
            location = None
            location_patterns = [
                r'(?:at|in)\s+(?:the\s+)?([A-Z][a-zA-Z\s]+?)\s+(?:room|office|building)',
                r'location:\s*([^\n,]+)',
                r'(?:at|in)\s+([A-Z][a-zA-Z\s]+?)(?:\s+at|\s+on|$)',
            ]
            
            for pattern in location_patterns:
                match = re.search(pattern, message)
                if match:
                    location = match.group(1).strip()
                    break
            
            # Extract description (optional)
            description = None
            desc_patterns = [
                r'about\s+([^,\.]+)',
                r'regarding\s+([^,\.]+)',
                r'to\s+discuss\s+([^,\.]+)',
            ]
            
            for pattern in desc_patterns:
                match = re.search(pattern, lower_message)
                if match:
                    description = match.group(1).strip()
                    break
            
            return {
                'title': title,
                'time': time_expression,
                'duration': duration,
                'location': location or '',
                'description': description or ''
            }
        
        return None
    
    
    def register_tool(self, tool_name: str, tool_definition: Dict[str, Any]) -> None:
        """
        Register a new tool
        
        Args:
            tool_name: Name of the tool
            tool_definition: Tool definition with handler
        """
        self.tools[tool_name] = tool_definition
        logger.info(f"Tool registered: {tool_name}")
    
    def unregister_tool(self, tool_name: str) -> None:
        """
        Unregister a tool
        
        Args:
            tool_name: Name of the tool to remove
        """
        if tool_name in self.tools:
            del self.tools[tool_name]
            logger.info(f"Tool unregistered: {tool_name}")
    
    def get_tools_list(self) -> List[str]:
        """
        Get list of registered tool names
        
        Returns:
            List of tool names
        """
        return list(self.tools.keys())
    
    async def execute_multiple_tools(
        self,
        tool_calls: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Execute multiple tools sequentially
        
        Args:
            tool_calls: List of tool call dictionaries with toolName and parameters
            
        Returns:
            List of tool execution results
        """
        results = []
        
        for call in tool_calls:
            result = await self.execute_tool(
                call.get('toolName'),
                call.get('parameters', {})
            )
            results.append({
                'toolName': call.get('toolName'),
                'result': result
            })
        
        return results
    
    def format_tool_result_for_context(self, tool_result: Dict[str, Any]) -> str:
        """
        Format tool result for inclusion in LLM context
        
        Args:
            tool_result: Tool execution result
            
        Returns:
            Formatted string for context
        """
        if tool_result.get('success') and tool_result.get('formatted'):
            return f"[Tool Result]\n{tool_result['formatted']}"
        elif tool_result.get('success'):
            return f"[Tool Result]\n{json.dumps(tool_result.get('data', {}), indent=2)}"
        else:
            return f"[Tool Error]\n{tool_result.get('error', 'Unknown error')}"
