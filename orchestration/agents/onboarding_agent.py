"""
Onboarding Agent
Conducts initial conversation to learn about the user
Builds comprehensive user profile for personalized interactions
"""

from typing import Dict, Any, List
from agents.base_agent import BaseAgent
from utils.logger import get_logger
from utils.time_utils import TimeContext

logger = get_logger()


class OnboardingAgent(BaseAgent):
    """Agent for user onboarding and profile building"""
    
    def __init__(self):
        super().__init__("onboarding")
        self.onboarding_questions = self._get_onboarding_questions()
    
    def _get_onboarding_questions(self) -> List[Dict[str, Any]]:
        """Get list of onboarding questions"""
        return [
            {
                "id": "name",
                "question": "First, what should I call you?",
                "category": "basic",
                "importance": 10
            },
            {
                "id": "location",
                "question": "Where are you from? (City/Country)",
                "category": "basic",
                "importance": 8
            },
            {
                "id": "occupation",
                "question": "What do you do for work or study?",
                "category": "career",
                "importance": 9
            },
            {
                "id": "relationship",
                "question": "Are you in a relationship? (It's okay if you'd rather not say!)",
                "category": "personal",
                "importance": 7
            },
            {
                "id": "family",
                "question": "Tell me a bit about your family - anyone important I should know about?",
                "category": "personal",
                "importance": 8
            },
            {
                "id": "hobbies",
                "question": "What do you like to do for fun? Any hobbies?",
                "category": "interests",
                "importance": 7
            },
            {
                "id": "health",
                "question": "Any dietary preferences or health things I should know? (vegetarian, allergies, etc.)",
                "category": "health",
                "importance": 9
            },
            {
                "id": "fitness",
                "question": "How active are you? Do you exercise regularly?",
                "category": "health",
                "importance": 7
            },
            {
                "id": "goals",
                "question": "What are you working towards right now? Any goals?",
                "category": "aspirations",
                "importance": 8
            },
            {
                "id": "preferences",
                "question": "How can I be most helpful to you? What kind of support do you need?",
                "category": "preferences",
                "importance": 9
            }
        ]
    
    def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process onboarding interaction
        
        Args:
            input_data: Dict with 'action' and relevant data
        
        Returns:
            Dict with onboarding response
        """
        try:
            action = input_data.get("action", "start")
            
            if action == "start":
                return self.start_onboarding()
            elif action == "get_next_question":
                current_index = input_data.get("current_index", 0)
                return self.get_next_question(current_index)
            elif action == "process_answer":
                question_id = input_data.get("question_id", "")
                answer = input_data.get("answer", "")
                if not question_id or not answer:
                    return {
                        "success": False,
                        "error": "Missing question_id or answer"
                    }
                return self.process_answer(question_id, answer)
            elif action == "complete":
                profile = input_data.get("profile", {})
                return self.complete_onboarding(profile)
            else:
                return {
                    "success": False,
                    "error": f"Unknown action: {action}"
                }
        
        except Exception as e:
            return self.handle_error(e, "onboarding")
    
    def start_onboarding(self) -> Dict[str, Any]:
        """Start the onboarding process"""
        time_info = TimeContext.get_current_time_info()
        greeting = time_info['greeting']
        
        welcome_message = f"""{greeting}! I'm EVA, your personal assistant. 

I'm excited to get to know you! To help me be more useful, I'd love to learn a bit about you. This will only take a few minutes, and you can skip anything you're not comfortable sharing.

Ready to start?"""
        
        return {
            "success": True,
            "message": welcome_message,
            "total_questions": len(self.onboarding_questions),
            "is_onboarding": True
        }
    
    def get_next_question(self, current_index: int) -> Dict[str, Any]:
        """Get the next onboarding question"""
        if current_index >= len(self.onboarding_questions):
            return {
                "success": True,
                "completed": True,
                "message": "That's all! Thanks for sharing with me. 😊"
            }
        
        question_data = self.onboarding_questions[current_index]
        
        return {
            "success": True,
            "completed": False,
            "question": question_data["question"],
            "question_id": question_data["id"],
            "category": question_data["category"],
            "progress": f"{current_index + 1}/{len(self.onboarding_questions)}",
            "current_index": current_index
        }
    
    def process_answer(self, question_id: str, answer: str) -> Dict[str, Any]:
        """
        Process user's answer to onboarding question
        
        Args:
            question_id: ID of the question
            answer: User's answer
        
        Returns:
            Dict with processed answer data
        """
        try:
            # Find the question
            question_data = next(
                (q for q in self.onboarding_questions if q["id"] == question_id),
                None
            )
            
            if not question_data:
                return {
                    "success": False,
                    "error": "Question not found"
                }
            
            # Check if user skipped
            skip_phrases = ["skip", "pass", "rather not", "don't want", "next"]
            if any(phrase in answer.lower() for phrase in skip_phrases):
                return {
                    "success": True,
                    "skipped": True,
                    "question_id": question_id,
                    "acknowledgment": "No problem! Let's move on."
                }
            
            # Extract and structure the information
            profile_data = {
                "question_id": question_id,
                "category": question_data["category"],
                "answer": answer,
                "importance": question_data["importance"],
                "skipped": False
            }
            
            # Generate acknowledgment
            acknowledgment = self._generate_acknowledgment(question_id, answer)
            
            return {
                "success": True,
                "skipped": False,
                "profile_data": profile_data,
                "acknowledgment": acknowledgment
            }
        
        except Exception as e:
            logger.error(f"Error processing answer: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def _generate_acknowledgment(self, question_id: str, answer: str) -> str:
        """Generate natural acknowledgment for user's answer"""
        acknowledgments = {
            "name": f"Nice to meet you! I'll remember that.",
            "location": "Got it! That's helpful to know.",
            "occupation": "Interesting! I'll keep that in mind.",
            "relationship": "Thanks for sharing!",
            "family": "That's sweet! Family is important.",
            "hobbies": "Cool! I love learning about people's interests.",
            "health": "Good to know! I'll remember that for meal suggestions.",
            "fitness": "Awesome! I'll keep that in mind for workout suggestions.",
            "goals": "That's great! I'll help you work towards that.",
            "preferences": "Perfect! I'll do my best to help in that way."
        }
        
        return acknowledgments.get(question_id, "Thanks for sharing!")
    
    def complete_onboarding(self, profile: Dict[str, Any]) -> Dict[str, Any]:
        """
        Complete onboarding and generate summary
        
        Args:
            profile: Collected user profile data
        
        Returns:
            Dict with completion message and profile summary
        """
        try:
            # Generate personalized completion message
            name = profile.get("name", "friend")
            
            completion_message = f"""Thanks for taking the time to share with me, {name}! 

I've got a good sense of who you are now. I'll use this to:
- Give you personalized suggestions
- Remember what's important to you
- Adapt my responses to your preferences
- Help you with your goals

You can always update this information by just telling me - I'm always learning!

So, what can I help you with today? 😊"""
            
            return {
                "success": True,
                "completed": True,
                "message": completion_message,
                "profile": profile
            }
        
        except Exception as e:
            return self.handle_error(e, "onboarding completion")
    
    def should_onboard(self, user_profile: Dict[str, Any]) -> bool:
        """
        Check if user needs onboarding
        
        Args:
            user_profile: Current user profile
        
        Returns:
            True if onboarding is needed
        """
        # Check if essential information is missing
        essential_fields = ["name", "preferences"]
        
        if not user_profile:
            return True
        
        for field in essential_fields:
            if field not in user_profile or not user_profile[field]:
                return True
        
        return False


# Made with Bob