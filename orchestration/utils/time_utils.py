"""
Time utilities for EVA
Provides time-aware context for conversations
"""

from datetime import datetime
from typing import Dict, Any, Optional


class TimeContext:
    """Provides time-aware context for EVA"""
    
    @staticmethod
    def get_current_time_info() -> Dict[str, Any]:
        """
        Get comprehensive time information
        
        Returns:
            Dict with time context
        """
        now = datetime.now()
        hour = now.hour
        
        return {
            "datetime": now,
            "hour": hour,
            "minute": now.minute,
            "day_of_week": now.strftime("%A"),
            "date": now.strftime("%Y-%m-%d"),
            "time_str": now.strftime("%I:%M %p"),
            "period": TimeContext.get_time_period(hour),
            "greeting": TimeContext.get_time_greeting(hour),
            "meal_type": TimeContext.get_meal_type(hour),
            "is_work_hours": TimeContext.is_work_hours(hour),
            "is_sleep_time": TimeContext.is_sleep_time(hour)
        }
    
    @staticmethod
    def get_time_period(hour: Optional[int] = None) -> str:
        """
        Get time period of day
        
        Args:
            hour: Hour (0-23), uses current if None
        
        Returns:
            Time period: early_morning, morning, afternoon, evening, night, late_night
        """
        if hour is None:
            hour = datetime.now().hour
        
        if 0 <= hour < 5:
            return "late_night"
        elif 5 <= hour < 8:
            return "early_morning"
        elif 8 <= hour < 12:
            return "morning"
        elif 12 <= hour < 17:
            return "afternoon"
        elif 17 <= hour < 21:
            return "evening"
        else:  # 21-24
            return "night"
    
    @staticmethod
    def get_time_greeting(hour: Optional[int] = None) -> str:
        """
        Get appropriate greeting based on time
        
        Args:
            hour: Hour (0-23), uses current if None
        
        Returns:
            Greeting string
        """
        if hour is None:
            hour = datetime.now().hour
        
        if 5 <= hour < 12:
            return "Good morning"
        elif 12 <= hour < 17:
            return "Good afternoon"
        elif 17 <= hour < 21:
            return "Good evening"
        else:
            return "Hey"  # Casual for late night
    
    @staticmethod
    def get_meal_type(hour: Optional[int] = None) -> str:
        """
        Get appropriate meal type based on time
        
        Args:
            hour: Hour (0-23), uses current if None
        
        Returns:
            Meal type: breakfast, lunch, snack, dinner
        """
        if hour is None:
            hour = datetime.now().hour
        
        if 5 <= hour < 11:
            return "breakfast"
        elif 11 <= hour < 16:
            return "lunch"
        elif 16 <= hour < 19:
            return "snack"
        else:  # 19-5
            return "dinner"
    
    @staticmethod
    def is_work_hours(hour: Optional[int] = None) -> bool:
        """
        Check if it's typical work hours (9 AM - 6 PM)
        
        Args:
            hour: Hour (0-23), uses current if None
        
        Returns:
            True if work hours
        """
        if hour is None:
            hour = datetime.now().hour
        
        return 9 <= hour < 18
    
    @staticmethod
    def is_sleep_time(hour: Optional[int] = None) -> bool:
        """
        Check if it's typical sleep time (10 PM - 6 AM)
        
        Args:
            hour: Hour (0-23), uses current if None
        
        Returns:
            True if sleep time
        """
        if hour is None:
            hour = datetime.now().hour
        
        return hour >= 22 or hour < 6
    
    @staticmethod
    def get_context_string() -> str:
        """
        Get formatted time context string for LLM
        
        Returns:
            Formatted string with time context
        """
        info = TimeContext.get_current_time_info()
        
        context = f"""Current Time Context:
- Time: {info['time_str']}
- Day: {info['day_of_week']}
- Period: {info['period'].replace('_', ' ').title()}
- Appropriate greeting: {info['greeting']}
- Meal time: {info['meal_type'].title()}"""
        
        if info['is_sleep_time']:
            context += "\n- Note: It's late - user might be tired or should consider sleeping"
        elif info['is_work_hours']:
            context += "\n- Note: Work hours - user might be busy"
        
        return context
    
    @staticmethod
    def should_suggest_sleep(hour: Optional[int] = None) -> bool:
        """Check if should suggest sleep (very late)"""
        if hour is None:
            hour = datetime.now().hour
        return hour >= 23 or hour < 5
    
    @staticmethod
    def should_suggest_workout(hour: Optional[int] = None) -> bool:
        """Check if good time for workout suggestion"""
        if hour is None:
            hour = datetime.now().hour
        # Good workout times: morning (6-10) or evening (17-20)
        return (6 <= hour < 10) or (17 <= hour < 20)


# Made with Bob