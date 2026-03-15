"""
Weather service using OpenWeather API
"""

import os
from datetime import datetime
from typing import Dict, List, Optional, Any
from collections import Counter
import aiohttp
from app.utils.logger import logger


class WeatherService:
    """Weather service for fetching weather data"""
    
    def __init__(self):
        self.api_key = os.getenv('OPENWEATHER_API_KEY')
        self.base_url = 'https://api.openweathermap.org/data/2.5'
        self.geo_url = 'https://api.openweathermap.org/geo/1.0'
    
    async def get_current_weather(self, location: str) -> Dict[str, Any]:
        """
        Get current weather for a location
        
        Args:
            location: City name or location string
            
        Returns:
            Weather data dictionary
        """
        try:
            coords = await self.get_coordinates(location)
            
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.base_url}/weather",
                    params={
                        'lat': coords['lat'],
                        'lon': coords['lon'],
                        'appid': self.api_key,
                        'units': 'metric'
                    }
                ) as response:
                    response.raise_for_status()
                    data = await response.json()
            
            weather = {
                'location': data['name'],
                'country': data['sys']['country'],
                'temperature': round(data['main']['temp']),
                'feelsLike': round(data['main']['feels_like']),
                'condition': data['weather'][0]['main'],
                'description': data['weather'][0]['description'],
                'humidity': data['main']['humidity'],
                'windSpeed': data['wind']['speed'],
                'icon': data['weather'][0]['icon'],
                'timestamp': datetime.fromtimestamp(data['dt'])
            }
            
            logger.info(f"Weather fetched for {location}: {weather['temperature']}°C, {weather['condition']}")
            return weather
        
        except Exception as e:
            logger.error(f"Error fetching current weather: {e}")
            raise Exception(f"Failed to fetch weather for {location}: {str(e)}")
    
    async def get_forecast(self, location: str, days: int = 5) -> Dict[str, Any]:
        """
        Get weather forecast for a location
        
        Args:
            location: City name or location string
            days: Number of days (default 5)
            
        Returns:
            Forecast data dictionary
        """
        try:
            coords = await self.get_coordinates(location)
            
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.base_url}/forecast",
                    params={
                        'lat': coords['lat'],
                        'lon': coords['lon'],
                        'appid': self.api_key,
                        'units': 'metric',
                        'cnt': days * 8
                    }
                ) as response:
                    response.raise_for_status()
                    data = await response.json()
            
            forecast = [
                {
                    'datetime': datetime.fromtimestamp(item['dt']),
                    'temperature': round(item['main']['temp']),
                    'feelsLike': round(item['main']['feels_like']),
                    'condition': item['weather'][0]['main'],
                    'description': item['weather'][0]['description'],
                    'humidity': item['main']['humidity'],
                    'windSpeed': item['wind']['speed'],
                    'precipitation': item['pop'] * 100
                }
                for item in data['list']
            ]
            
            logger.info(f"Forecast fetched for {location}: {len(forecast)} entries")
            return {
                'location': data['city']['name'],
                'country': data['city']['country'],
                'forecast': forecast
            }
        
        except Exception as e:
            logger.error(f"Error fetching forecast: {e}")
            raise Exception(f"Failed to fetch forecast for {location}: {str(e)}")
    
    async def get_coordinates(self, location: str) -> Dict[str, Any]:
        """
        Get coordinates for a location
        
        Args:
            location: City name or location string
            
        Returns:
            Coordinates dictionary with lat, lon, name, country
        """
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.geo_url}/direct",
                    params={
                        'q': location,
                        'limit': 1,
                        'appid': self.api_key
                    }
                ) as response:
                    response.raise_for_status()
                    data = await response.json()
            
            if not data:
                raise Exception('Location not found')
            
            return {
                'lat': data[0]['lat'],
                'lon': data[0]['lon'],
                'name': data[0]['name'],
                'country': data[0]['country']
            }
        
        except Exception as e:
            logger.error(f"Error getting coordinates: {e}")
            raise Exception(f"Location not found: {location}")
    
    def format_weather_response(self, weather: Dict[str, Any]) -> str:
        """
        Format weather data as human-readable text
        
        Args:
            weather: Weather data dictionary
            
        Returns:
            Formatted weather string
        """
        return (
            f"The current weather in {weather['location']}, {weather['country']} "
            f"is {weather['temperature']}°C with {weather['description']}. "
            f"It feels like {weather['feelsLike']}°C. "
            f"Humidity is {weather['humidity']}% and wind speed is {weather['windSpeed']} m/s."
        )
    
    def format_forecast_response(self, forecast_data: Dict[str, Any]) -> str:
        """
        Format forecast data as human-readable text
        
        Args:
            forecast_data: Forecast data dictionary
            
        Returns:
            Formatted forecast string
        """
        location = forecast_data['location']
        country = forecast_data['country']
        forecast = forecast_data['forecast']
        
        # Group by day
        forecast_by_day = {}
        for item in forecast:
            date = item['datetime'].strftime('%Y-%m-%d')
            if date not in forecast_by_day:
                forecast_by_day[date] = []
            forecast_by_day[date].append(item)
        
        # Calculate daily summaries
        daily_forecasts = []
        for date, items in forecast_by_day.items():
            temps = [item['temperature'] for item in items]
            conditions = [item['condition'] for item in items]
            max_temp = max(temps)
            min_temp = min(temps)
            dominant_condition = self._get_most_frequent(conditions)
            
            daily_forecasts.append({
                'date': date,
                'maxTemp': max_temp,
                'minTemp': min_temp,
                'condition': dominant_condition
            })
        
        # Format response
        response = f"Weather forecast for {location}, {country}:\n\n"
        for day in daily_forecasts:
            response += f"{day['date']}: {day['condition']}, High: {day['maxTemp']}°C, Low: {day['minTemp']}°C\n"
        
        return response
    
    def _get_most_frequent(self, arr: List[Any]) -> Any:
        """Get most frequent item in array"""
        if not arr:
            return None
        counter = Counter(arr)
        return counter.most_common(1)[0][0]
    
    def should_carry_umbrella(self, weather: Dict[str, Any]) -> bool:
        """
        Check if user should carry an umbrella
        
        Args:
            weather: Weather data dictionary
            
        Returns:
            True if umbrella recommended
        """
        rainy_conditions = ['Rain', 'Drizzle', 'Thunderstorm']
        return (
            weather['condition'] in rainy_conditions or
            'rain' in weather['description'].lower()
        )
    
    def get_weather_advice(self, weather: Dict[str, Any]) -> str:
        """
        Get weather advice based on conditions
        
        Args:
            weather: Weather data dictionary
            
        Returns:
            Weather advice string
        """
        advice = []
        
        if weather['temperature'] < 10:
            advice.append("It's quite cold, dress warmly!")
        elif weather['temperature'] > 30:
            advice.append("It's hot outside, stay hydrated!")
        
        if self.should_carry_umbrella(weather):
            advice.append("You should carry an umbrella.")
        
        if weather['windSpeed'] > 10:
            advice.append("It's quite windy today.")
        
        if weather['humidity'] > 80:
            advice.append("High humidity today, might feel muggy.")
        
        return ' '.join(advice) if advice else "Have a great day!"
    
    def validate_api_key(self) -> bool:
        """
        Validate that API key is configured
        
        Returns:
            True if API key exists
        """
        return bool(self.api_key)
