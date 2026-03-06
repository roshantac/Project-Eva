"""
Memory Classification Agent
Determines if information should be stored and classifies memory type
"""

from typing import Dict, Any
from agents.base_agent import BaseAgent
from prompts.system_prompts import SystemPrompts, PromptTemplates
from tools.memory_tools import get_memory_tools


class MemoryClassifierAgent(BaseAgent):
    """Agent for classifying and storing memories"""
    
    def __init__(self):
        super().__init__("memory_classifier")
        self.system_prompt = SystemPrompts.MEMORY_CLASSIFICATION
        self.memory_tools = get_memory_tools()
    
    def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Classify memory and store if appropriate
        
        Args:
            input_data: Dict with 'message' and optional 'context'
        
        Returns:
            Dict with memory classification and storage result
        """
        try:
            message = input_data.get("message", "")
            context = input_data.get("context", "")
            
            if not message or not message.strip():
                return {
                    "success": True,
                    "should_store": False,
                    "reason": "Empty message"
                }
            
            self.log_decision("Classifying memory", {
                "message_length": len(message),
                "has_context": bool(context)
            })
            
            # Build prompt
            prompt = PromptTemplates.memory_classification_template(message, context)
            
            # Call LLM
            result = self.call_llm(
                prompt=prompt,
                system_prompt=self.system_prompt
            )
            
            if not result.get("success"):
                return self.handle_error(
                    Exception(result.get("error", "LLM call failed")),
                    "memory classification"
                )
            
            # Parse JSON response
            response_text = result.get("response", "")
            parsed = self.parse_json_response(response_text)
            
            if not parsed:
                self.log_decision("Failed to parse memory classification", {})
                return {
                    "success": True,
                    "should_store": False,
                    "reason": "Parse failed"
                }
            
            # Extract fields
            should_store = parsed.get("should_store", False)
            
            if not should_store:
                self.log_decision("Memory not stored", {
                    "reason": "Not significant enough"
                })
                return {
                    "success": True,
                    "should_store": False,
                    "reason": "Not significant enough to store"
                }
            
            # Extract memory details
            memory_type = parsed.get("memory_type", "short_term")
            category = parsed.get("category", "NOTES")
            importance = parsed.get("importance", 5)
            structured_data = parsed.get("structured_data", {})
            summary = parsed.get("summary", message)
            
            # Store memory using appropriate tool
            storage_result = None
            if memory_type == "short_term":
                storage_result = self.memory_tools.store_short_term_memory(
                    content=summary,
                    category=category,
                    metadata={
                        "original_message": message,
                        "structured_data": structured_data,
                        "importance": importance
                    }
                )
            else:  # long_term
                storage_result = self.memory_tools.store_long_term_memory(
                    content=summary,
                    category=category,
                    importance=importance,
                    metadata={
                        "original_message": message,
                        "structured_data": structured_data
                    }
                )
            
            self.log_decision("Memory stored", {
                "memory_type": memory_type,
                "category": category,
                "importance": importance,
                "memory_id": storage_result.get("memory_id") if storage_result else None
            })
            
            return {
                "success": True,
                "should_store": True,
                "memory_type": memory_type,
                "category": category,
                "importance": importance,
                "summary": summary,
                "structured_data": structured_data,
                "storage_result": storage_result,
                "metadata": {
                    "agent": self.agent_name,
                    "model": result.get("model")
                }
            }
        
        except Exception as e:
            return self.handle_error(e, "memory classification")

# Made with Bob
