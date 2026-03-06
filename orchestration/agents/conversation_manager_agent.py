"""
Conversation Manager Agent
Handles natural dialogue flow with personality-driven responses
"""

from typing import Dict, Any
from agents.base_agent import BaseAgent
from prompts.system_prompts import SystemPrompts, PromptTemplates
from utils.state_manager import Role, EmotionalState, ConversationState
from utils.time_utils import TimeContext
from tools.web_search_tool import get_web_search_tool
from tools.action_tools import get_action_tools


class ConversationManagerAgent(BaseAgent):
    """Agent for managing natural conversation flow"""
    
    def __init__(self):
        super().__init__("conversation_manager")
        self.web_search = get_web_search_tool()
        self.action_tools = get_action_tools()
    
    def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate conversational response
        
        Args:
            input_data: Dict with:
                - message: User message
                - conversation_state: ConversationState object
                - intent_data: Intent classification result
                - emotional_data: Emotional detection result
                - web_search_results: Optional web search results
        
        Returns:
            Dict with response and metadata
        """
        try:
            message = input_data.get("message", "")
            state: ConversationState = input_data.get("conversation_state")
            intent_data = input_data.get("intent_data", {})
            emotional_data = input_data.get("emotional_data", {})
            web_search_results = input_data.get("web_search_results")
            
            if not message or not state:
                return {
                    "success": False,
                    "error": "Missing required input"
                }
            
            # Get current role and emotional state
            current_role = state.get_role()
            emotional_state_data = state.get_emotional_state()
            
            # Convert emotion string to EmotionalState enum
            try:
                emotion = EmotionalState[emotional_state_data["emotion"].upper()]
            except (KeyError, AttributeError):
                emotion = EmotionalState.NEUTRAL
            
            intensity = emotional_state_data.get("intensity", 5)
            
            self.log_decision("Generating response", {
                "role": current_role.value,
                "emotion": emotion.value,
                "intensity": intensity,
                "has_web_results": web_search_results is not None
            })
            
            # Build system prompt based on role and emotion
            system_prompt = SystemPrompts.get_conversation_prompt(
                current_role,
                emotion,
                intensity
            )
            
            # Build context - use fewer messages to avoid topic confusion
            # If there's a web search, it means a new topic/question, so use less history
            context_messages = 5 if web_search_results else 10
            conversation_context = state.get_conversation_context(max_messages=context_messages)
            
            # Add user profile information if available
            user_profile = state.get_user_profile()
            if user_profile:
                profile_info = "\n=== User Profile ===\n"
                for key, value in user_profile.items():
                    if value:  # Only include non-empty values
                        profile_info += f"{key}: {value}\n"
                conversation_context = profile_info + "\n" + conversation_context
            
            # Add time context
            time_context = TimeContext.get_context_string()
            conversation_context += f"\n\n{time_context}"
            
            # Add web search results to context if available
            if web_search_results and web_search_results.get("success"):
                search_context = self.web_search.format_results_for_llm(web_search_results)
                conversation_context += f"\n\nWeb Search Results:\n{search_context}"
            
            # Add health suggestion if available
            health_suggestion = input_data.get("health_suggestion")
            if health_suggestion and health_suggestion.get("success"):
                conversation_context += f"\n\nHealth Suggestion Available: Yes"
            
            # Format full context
            full_context = SystemPrompts.format_conversation_context(
                conversation_context,
                current_role,
                emotional_state_data
            )
            
            # Build prompt
            prompt = PromptTemplates.conversation_template(
                message,
                full_context,
                system_prompt
            )
            
            # Call LLM with higher temperature for natural conversation
            result = self.call_llm(
                prompt=prompt,
                temperature=self.temperature
            )
            
            if not result.get("success"):
                return self.handle_error(
                    Exception(result.get("error", "LLM call failed")),
                    "conversation generation"
                )
            
            response_text = result.get("response", "").strip()
            
            # Check if response is empty
            if not response_text:
                response_text = "I'm here to help. Could you tell me more about what you need?"
            
            self.log_decision("Response generated", {
                "response_length": len(response_text),
                "role": current_role.value
            })
            
            return {
                "success": True,
                "response": response_text,
                "role": current_role.value,
                "emotional_adaptation": {
                    "detected_emotion": emotion.value,
                    "intensity": intensity
                },
                "metadata": {
                    "agent": self.agent_name,
                    "model": result.get("model"),
                    "processing_time": result.get("total_duration", 0)
                }
            }
        
        except Exception as e:
            return self.handle_error(e, "conversation management")
    
    def handle_web_search(self, query: str, user_context: str) -> Dict[str, Any]:
        """
        Perform web search and personalize results
        
        Args:
            query: Search query
            user_context: User context for personalization
        
        Returns:
            Dict with search results
        """
        try:
            self.log_decision("Performing web search", {"query": query})
            
            # Perform search
            search_results = self.web_search.search(query)
            
            if not search_results.get("success"):
                return search_results
            
            # Format results for LLM
            formatted_results = self.web_search.format_results_for_llm(search_results)
            
            # Personalize with LLM
            personalization_prompt = PromptTemplates.web_search_personalization_template(
                query,
                formatted_results,
                user_context
            )
            
            result = self.call_llm(
                prompt=personalization_prompt,
                system_prompt=SystemPrompts.WEB_SEARCH_PERSONALIZATION
            )
            
            if result.get("success"):
                personalized_response = result.get("response", "")
                search_results["personalized_response"] = personalized_response
            
            return search_results
        
        except Exception as e:
            return self.handle_error(e, "web search")
    
    def handle_action_request(
        self,
        action_type: str,
        parameters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Handle action requests (schedule, reminder, etc.)
        
        Args:
            action_type: Type of action (schedule, reminder, call, task)
            parameters: Action parameters
        
        Returns:
            Dict with action result
        """
        try:
            self.log_decision("Handling action request", {
                "action_type": action_type,
                "parameters": parameters
            })
            
            if action_type == "schedule":
                return self.action_tools.schedule_meeting(**parameters)
            elif action_type == "reminder":
                return self.action_tools.set_reminder(**parameters)
            elif action_type == "call":
                return self.action_tools.make_call_request(**parameters)
            elif action_type == "task":
                return self.action_tools.create_task(**parameters)
            else:
                return {
                    "success": False,
                    "error": f"Unknown action type: {action_type}"
                }
        
        except Exception as e:
            return self.handle_error(e, f"action request: {action_type}")

# Made with Bob
