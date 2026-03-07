"""
Tool execution engine for handling external tool calls
"""

import os
import re
import json
from typing import Dict, Any, Optional, List, Callable
from app.services.weather_service import WeatherService
from app.utils.logger import logger


class ToolEngine:
    """Engine for detecting and executing tools"""
    
    def __init__(self):
        self.weather_service = WeatherService()
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
        llm_service: Optional[Any] = None
    ) -> Dict[str, Any]:
        """
        Detect if tools are needed and execute them
        
        Args:
            user_message: User's message
            llm_service: Optional LLM service (unused but kept for compatibility)
            
        Returns:
            Dictionary with tool execution results
        """
        try:
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
