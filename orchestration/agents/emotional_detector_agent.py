"""
Emotional Detection Agent
Detects user's emotional state from conversation
"""

from typing import Dict, Any
from agents.base_agent import BaseAgent
from prompts.system_prompts import SystemPrompts, PromptTemplates
from utils.state_manager import EmotionalState


class EmotionalDetectorAgent(BaseAgent):
    """Agent for detecting user's emotional state"""
    
    def __init__(self):
        super().__init__("emotional_detector")
        self.system_prompt = SystemPrompts.EMOTIONAL_DETECTION
    
    def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Detect emotional state from user message
        
        Args:
            input_data: Dict with 'message' and optional 'context'
        
        Returns:
            Dict with emotional state, intensity, and confidence
        """
        try:
            message = input_data.get("message", "")
            context = input_data.get("context", "")
            
            if not message or not message.strip():
                # Default to neutral if no message
                return {
                    "success": True,
                    "emotion": "NEUTRAL",
                    "intensity": 5,
                    "confidence": 1.0,
                    "indicators": [],
                    "reasoning": "No message provided"
                }
            
            self.log_decision("Detecting emotional state", {
                "message_length": len(message),
                "has_context": bool(context)
            })
            
            # Build prompt
            prompt = PromptTemplates.emotional_detection_template(message, context)
            
            # Call LLM
            result = self.call_llm(
                prompt=prompt,
                system_prompt=self.system_prompt
            )
            
            if not result.get("success"):
                # Fallback to neutral
                self.log_decision("Detection failed, defaulting to neutral", {
                    "error": result.get("error")
                })
                return {
                    "success": True,
                    "emotion": "NEUTRAL",
                    "intensity": 5,
                    "confidence": 0.5,
                    "indicators": [],
                    "reasoning": "Detection failed",
                    "fallback": True
                }
            
            # Parse JSON response
            response_text = result.get("response", "")
            parsed = self.parse_json_response(response_text)
            
            if not parsed:
                # Fallback to neutral
                self.log_decision("Failed to parse emotion, defaulting to neutral", {})
                return {
                    "success": True,
                    "emotion": "NEUTRAL",
                    "intensity": 5,
                    "confidence": 0.5,
                    "indicators": [],
                    "reasoning": "Parse failed",
                    "fallback": True
                }
            
            # Extract and validate fields
            emotion_str = parsed.get("emotion", "NEUTRAL").upper()
            
            # Validate emotion is valid
            try:
                emotion_enum = EmotionalState[emotion_str]
                emotion = emotion_enum.value
            except KeyError:
                emotion = "neutral"
                self.log_decision("Invalid emotion detected, using neutral", {
                    "invalid_emotion": emotion_str
                })
            
            # Clamp intensity to 1-10 range
            intensity = max(1, min(10, parsed.get("intensity", 5)))
            
            emotion_result = {
                "success": True,
                "emotion": emotion,
                "intensity": intensity,
                "confidence": parsed.get("confidence", 0.8),
                "indicators": parsed.get("indicators", []),
                "reasoning": parsed.get("reasoning", ""),
                "metadata": {
                    "agent": self.agent_name,
                    "model": result.get("model")
                }
            }
            
            self.log_decision("Emotional state detected", {
                "emotion": emotion,
                "intensity": intensity,
                "confidence": emotion_result["confidence"]
            })
            
            return emotion_result
        
        except Exception as e:
            return self.handle_error(e, "emotional detection")

# Made with Bob
