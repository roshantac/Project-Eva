"""
Intent Classification Agent
Analyzes user messages to identify intent and extract entities
"""

from typing import Dict, Any
from agents.base_agent import BaseAgent
from prompts.system_prompts import SystemPrompts, PromptTemplates


class IntentClassifierAgent(BaseAgent):
    """Agent for classifying user intent and extracting entities"""
    
    def __init__(self):
        super().__init__("intent_classification")
        self.system_prompt = SystemPrompts.INTENT_CLASSIFICATION
    
    def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Classify user intent and extract entities
        
        Args:
            input_data: Dict with 'message' and optional 'context'
        
        Returns:
            Dict with intent classification and entities
        """
        try:
            message = input_data.get("message", "")
            context = input_data.get("context", "")
            
            if not message or not message.strip():
                return {
                    "success": False,
                    "error": "Empty message provided"
                }
            
            self.log_decision("Classifying intent", {
                "message_length": len(message),
                "has_context": bool(context)
            })
            
            # Build prompt
            prompt = PromptTemplates.intent_classification_template(message, context)
            
            # Call LLM
            result = self.call_llm(
                prompt=prompt,
                system_prompt=self.system_prompt
            )
            
            if not result.get("success"):
                return self.handle_error(
                    Exception(result.get("error", "LLM call failed")),
                    "intent classification"
                )
            
            # Parse JSON response
            response_text = result.get("response", "")
            parsed = self.parse_json_response(response_text)
            
            if not parsed:
                # Fallback to default intent
                self.log_decision("Failed to parse intent, using default", {})
                return {
                    "success": True,
                    "primary_intent": "CASUAL_CHAT",
                    "secondary_intents": [],
                    "confidence": 0.5,
                    "entities": {},
                    "memory_type": "none",
                    "requires_web_search": False,
                    "action_type": "none",
                    "fallback": True
                }
            
            # Extract and validate fields
            intent_result = {
                "success": True,
                "primary_intent": parsed.get("primary_intent", "CASUAL_CHAT"),
                "secondary_intents": parsed.get("secondary_intents", []),
                "confidence": parsed.get("confidence", 0.8),
                "entities": parsed.get("entities", {}),
                "memory_type": parsed.get("memory_type", "none"),
                "requires_web_search": parsed.get("requires_web_search", False),
                "action_type": parsed.get("action_type", "none"),
                "metadata": {
                    "agent": self.agent_name,
                    "model": result.get("model")
                }
            }
            
            self.log_decision("Intent classified", {
                "primary_intent": intent_result["primary_intent"],
                "confidence": intent_result["confidence"],
                "requires_web_search": intent_result["requires_web_search"],
                "action_type": intent_result["action_type"]
            })
            
            return intent_result
        
        except Exception as e:
            return self.handle_error(e, "intent classification")

# Made with Bob
