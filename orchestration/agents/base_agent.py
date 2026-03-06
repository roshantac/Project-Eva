"""
Base agent class for EVA system
Provides common functionality for all agents
"""

from typing import Dict, Any, Optional
from abc import ABC, abstractmethod
from utils.ollama_client import OllamaClient
from utils.config_manager import get_config
from utils.logger import get_logger

logger = get_logger()


class BaseAgent(ABC):
    """Abstract base class for all EVA agents"""
    
    def __init__(self, agent_name: str):
        self.agent_name = agent_name
        self.config = get_config()
        self.agent_config = self.config.get_agent_config(agent_name)
        
        # Initialize Ollama client
        model_config = self.config.get_model_config()
        self.llm_client = OllamaClient(
            base_url=model_config.get("base_url", "http://localhost:11434"),
            model=model_config.get("name", "gemma:7b"),
            timeout=model_config.get("timeout", 120)
        )
        
        # Agent-specific parameters
        self.temperature = self.agent_config.get("temperature", 0.7)
        self.max_tokens = self.agent_config.get("max_tokens", 2048)
        self.top_p = self.agent_config.get("top_p", 0.9)
        
        logger.info(f"Initialized {agent_name} agent")
    
    @abstractmethod
    def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process input and return output
        Must be implemented by subclasses
        
        Args:
            input_data: Input data for the agent
        
        Returns:
            Dict containing agent output
        """
        pass
    
    def call_llm(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Call LLM with prompt
        
        Args:
            prompt: User prompt
            system_prompt: System prompt (optional)
            temperature: Override default temperature
            max_tokens: Override default max tokens
        
        Returns:
            Dict with LLM response
        """
        logger.agent_input(self.agent_name, prompt)
        
        result = self.llm_client.generate(
            prompt=prompt,
            system=system_prompt,
            temperature=temperature or self.temperature,
            max_tokens=max_tokens or self.max_tokens,
            top_p=self.top_p
        )
        
        if result.get("success"):
            logger.agent_output(self.agent_name, result.get("response", ""))
        else:
            logger.error(f"{self.agent_name} LLM call failed: {result.get('error')}")
        
        return result
    
    def parse_json_response(self, response: str) -> Optional[Dict[str, Any]]:
        """
        Parse JSON from LLM response
        Handles cases where LLM includes extra text
        
        Args:
            response: LLM response string
        
        Returns:
            Parsed JSON dict or None if parsing fails
        """
        import json
        import re
        
        try:
            # Try direct parsing first
            return json.loads(response)
        except json.JSONDecodeError:
            # Try to extract JSON from response
            # Look for content between { and }
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                try:
                    return json.loads(json_match.group())
                except json.JSONDecodeError:
                    pass
            
            logger.warning(f"{self.agent_name}: Failed to parse JSON from response")
            return None
    
    def handle_error(self, error: Exception, context: str = "") -> Dict[str, Any]:
        """
        Handle errors gracefully
        
        Args:
            error: The exception that occurred
            context: Additional context about the error
        
        Returns:
            Dict with error information
        """
        error_msg = f"{self.agent_name} error"
        if context:
            error_msg += f" ({context})"
        error_msg += f": {str(error)}"
        
        logger.error(error_msg)
        
        return {
            "success": False,
            "error": str(error),
            "agent": self.agent_name,
            "context": context
        }
    
    def log_decision(self, decision: str, details: Optional[Dict[str, Any]] = None) -> None:
        """
        Log agent decision
        
        Args:
            decision: Description of the decision
            details: Additional details
        """
        logger.agent_decision(self.agent_name, decision, details or {})

# Made with Bob
