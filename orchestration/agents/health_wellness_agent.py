"""
Health & Wellness Agent
Tracks user's health information and provides personalized diet and fitness suggestions
"""

from typing import Dict, Any, List, Optional
from agents.base_agent import BaseAgent
from utils.logger import get_logger

logger = get_logger()


class HealthWellnessAgent(BaseAgent):
    """Agent for health tracking and wellness suggestions"""
    
    def __init__(self):
        super().__init__("health_wellness")
        self.system_prompt = self._get_system_prompt()
    
    def _get_system_prompt(self) -> str:
        return """You are EVA's Health & Wellness specialist.

Your role is to:
1. Extract health-related information from conversations
2. Provide personalized diet suggestions based on user's health profile
3. Recommend appropriate exercises and activities
4. Track health goals and progress

Health Information to Track:
- Medical conditions (diabetes, allergies, heart issues, etc.)
- Dietary restrictions (vegetarian, vegan, gluten-free, etc.)
- Fitness level (sedentary, moderate, active)
- Health goals (weight loss, muscle gain, general fitness)
- Current habits (exercise routine, sleep patterns, diet)
- Allergies and food sensitivities
- Age, height, weight (if mentioned)
- Medications or supplements

Guidelines:
1. Be supportive and non-judgmental
2. Provide practical, actionable suggestions
3. Consider user's health conditions and restrictions
4. Suggest balanced, nutritious meals
5. Recommend appropriate exercise intensity
6. Be encouraging about healthy habits
7. Never provide medical advice - suggest consulting doctors for medical issues

Output Format (JSON):
{
  "has_health_info": true/false,
  "health_data": {
    "conditions": ["diabetes", "high blood pressure"],
    "restrictions": ["vegetarian", "lactose intolerant"],
    "fitness_level": "moderate",
    "goals": ["weight loss", "better sleep"],
    "allergies": ["peanuts"],
    "current_habits": "walks 30 min daily"
  },
  "importance": 8,
  "category": "health_profile"
}
"""
    
    def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process health-related requests
        
        Args:
            input_data: Dict with 'message', 'context', and optional 'request_type'
        
        Returns:
            Dict with health suggestion or extracted info
        """
        try:
            message = input_data.get("message", "")
            context = input_data.get("context", "")
            request_type = input_data.get("request_type", "auto")
            
            # Auto-detect what's needed
            if request_type == "extract_info":
                return self.extract_health_info(message, context)
            elif request_type == "meal_suggestion":
                health_profile = input_data.get("health_profile", {})
                meal_type = input_data.get("meal_type", "dinner")
                return self.suggest_meal(meal_type, health_profile)
            elif request_type == "exercise_suggestion":
                health_profile = input_data.get("health_profile", {})
                time_available = input_data.get("time_available", 30)
                return self.suggest_exercise(health_profile, time_available, context)
            else:
                # Auto-detect based on message
                if self.check_if_health_related(message):
                    return self.extract_health_info(message, context)
                else:
                    return {
                        "success": True,
                        "has_health_info": False,
                        "message": "No health-related information detected"
                    }
        
        except Exception as e:
            return self.handle_error(e, "health wellness processing")
    
    def extract_health_info(self, message: str, context: str = "") -> Dict[str, Any]:
        """
        Extract health-related information from user message
        
        Args:
            message: User message
            context: Conversation context
        
        Returns:
            Dict with extracted health information
        """
        try:
            self.log_decision("Extracting health information", {
                "message_length": len(message)
            })
            
            prompt = f"""Analyze this message for health-related information.

Context:
{context}

User Message: "{message}"

Extract any health information and provide in JSON format:"""
            
            result = self.call_llm(
                prompt=prompt,
                system_prompt=self.system_prompt,
                temperature=0.2
            )
            
            if not result.get("success"):
                return {
                    "success": False,
                    "has_health_info": False
                }
            
            # Parse JSON response
            import json
            try:
                health_data = json.loads(result.get("response", "{}"))
                
                self.log_decision("Health information extracted", {
                    "has_info": health_data.get("has_health_info", False),
                    "categories": list(health_data.get("health_data", {}).keys())
                })
                
                return {
                    "success": True,
                    **health_data
                }
            except json.JSONDecodeError:
                return {
                    "success": False,
                    "has_health_info": False
                }
        
        except Exception as e:
            return self.handle_error(e, "health info extraction")
    
    def suggest_meal(
        self,
        meal_type: str,
        health_profile: Dict[str, Any],
        preferences: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Suggest a meal based on health profile
        
        Args:
            meal_type: breakfast, lunch, dinner, snack
            health_profile: User's health information
            preferences: Additional preferences
        
        Returns:
            Dict with meal suggestions
        """
        try:
            self.log_decision("Generating meal suggestion", {
                "meal_type": meal_type,
                "has_profile": bool(health_profile)
            })
            
            profile_text = self._format_health_profile(health_profile)
            prefs_text = ", ".join(preferences) if preferences else "none specified"
            
            prompt = f"""Suggest a healthy {meal_type} considering this health profile:

{profile_text}

Additional preferences: {prefs_text}

Provide:
1. 2-3 meal options
2. Brief nutritional benefits
3. Why it's good for their health profile
4. Keep it practical and easy to prepare

Be conversational and encouraging. Format as a friendly suggestion, not a list."""
            
            result = self.call_llm(
                prompt=prompt,
                system_prompt="You are a friendly nutritionist helping someone eat healthier.",
                temperature=0.7
            )
            
            if result.get("success"):
                suggestion = result.get("response", "").strip()
                
                self.log_decision("Meal suggestion generated", {
                    "meal_type": meal_type,
                    "length": len(suggestion)
                })
                
                return {
                    "success": True,
                    "meal_type": meal_type,
                    "suggestion": suggestion
                }
            else:
                return {
                    "success": False,
                    "error": "Failed to generate suggestion"
                }
        
        except Exception as e:
            return self.handle_error(e, "meal suggestion")
    
    def suggest_exercise(
        self,
        health_profile: Dict[str, Any],
        time_available: int = 30,
        context: str = ""
    ) -> Dict[str, Any]:
        """
        Suggest exercise based on health profile
        
        Args:
            health_profile: User's health information
            time_available: Minutes available for exercise
            context: Additional context
        
        Returns:
            Dict with exercise suggestions
        """
        try:
            self.log_decision("Generating exercise suggestion", {
                "time_available": time_available,
                "has_profile": bool(health_profile)
            })
            
            profile_text = self._format_health_profile(health_profile)
            
            prompt = f"""Suggest an appropriate workout considering this health profile:

{profile_text}

Time available: {time_available} minutes
Context: {context if context else "General workout"}

Provide:
1. Specific exercises or activities
2. Duration and intensity
3. Why it's suitable for their fitness level
4. Motivational encouragement

Be friendly and encouraging. Keep it practical and achievable."""
            
            result = self.call_llm(
                prompt=prompt,
                system_prompt="You are a supportive fitness coach helping someone stay active.",
                temperature=0.7
            )
            
            if result.get("success"):
                suggestion = result.get("response", "").strip()
                
                self.log_decision("Exercise suggestion generated", {
                    "time": time_available,
                    "length": len(suggestion)
                })
                
                return {
                    "success": True,
                    "time_available": time_available,
                    "suggestion": suggestion
                }
            else:
                return {
                    "success": False,
                    "error": "Failed to generate suggestion"
                }
        
        except Exception as e:
            return self.handle_error(e, "exercise suggestion")
    
    def _format_health_profile(self, profile: Dict[str, Any]) -> str:
        """Format health profile for LLM consumption"""
        if not profile:
            return "No health profile available. Provide general healthy suggestions."
        
        formatted = []
        
        if profile.get("conditions"):
            formatted.append(f"Medical conditions: {', '.join(profile['conditions'])}")
        
        if profile.get("restrictions"):
            formatted.append(f"Dietary restrictions: {', '.join(profile['restrictions'])}")
        
        if profile.get("allergies"):
            formatted.append(f"Allergies: {', '.join(profile['allergies'])}")
        
        if profile.get("fitness_level"):
            formatted.append(f"Fitness level: {profile['fitness_level']}")
        
        if profile.get("goals"):
            formatted.append(f"Health goals: {', '.join(profile['goals'])}")
        
        if profile.get("current_habits"):
            formatted.append(f"Current habits: {profile['current_habits']}")
        
        return "\n".join(formatted) if formatted else "No specific health information available."
    
    def check_if_health_related(self, message: str) -> bool:
        """
        Quick check if message is health/wellness related
        
        Args:
            message: User message
        
        Returns:
            True if health-related
        """
        health_keywords = [
            "health", "diet", "food", "meal", "eat", "dinner", "lunch", "breakfast",
            "exercise", "workout", "fitness", "gym", "run", "walk", "weight",
            "sleep", "tired", "energy", "nutrition", "calories", "protein",
            "diabetes", "allergy", "allergic", "vegetarian", "vegan",
            "doctor", "medicine", "sick", "pain", "headache"
        ]
        
        message_lower = message.lower()
        return any(keyword in message_lower for keyword in health_keywords)


# Made with Bob