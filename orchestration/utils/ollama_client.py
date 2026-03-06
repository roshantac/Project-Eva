"""
Ollama client for interacting with local LLM models
Handles API calls, error handling, and response parsing
"""

import json
import requests
from typing import Dict, Any, Optional, List
from utils.logger import get_logger

logger = get_logger()


class OllamaClient:
    """Client for interacting with Ollama API"""
    
    def __init__(self, base_url: str = "http://localhost:11434", model: str = "gemma:7b", timeout: int = 120):
        self.base_url = base_url.rstrip('/')
        self.model = model
        self.timeout = timeout
        self.generate_url = f"{self.base_url}/api/generate"
        self.chat_url = f"{self.base_url}/api/chat"
        
        logger.info(f"Initialized Ollama client with model: {model}")
    
    def generate(
        self,
        prompt: str,
        system: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2048,
        top_p: float = 0.9,
        stop: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Generate completion using Ollama API
        
        Args:
            prompt: The user prompt
            system: System prompt for context
            temperature: Sampling temperature (0.0 to 1.0)
            max_tokens: Maximum tokens to generate
            top_p: Nucleus sampling parameter
            stop: Stop sequences
        
        Returns:
            Dict containing response and metadata
        """
        try:
            # Build the full prompt with system message if provided
            full_prompt = prompt
            if system:
                full_prompt = f"{system}\n\n{prompt}"
            
            payload = {
                "model": self.model,
                "prompt": full_prompt,
                "stream": False,
                "options": {
                    "temperature": temperature,
                    "num_predict": max_tokens,
                    "top_p": top_p,
                }
            }
            
            if stop:
                payload["options"]["stop"] = stop
            
            logger.debug(f"Sending request to Ollama: {self.generate_url}")
            
            response = requests.post(
                self.generate_url,
                json=payload,
                timeout=self.timeout
            )
            
            response.raise_for_status()
            result = response.json()
            
            return {
                "success": True,
                "response": result.get("response", ""),
                "model": result.get("model", self.model),
                "total_duration": result.get("total_duration", 0),
                "prompt_eval_count": result.get("prompt_eval_count", 0),
                "eval_count": result.get("eval_count", 0)
            }
            
        except requests.exceptions.Timeout:
            logger.error(f"Ollama request timed out after {self.timeout}s")
            return {
                "success": False,
                "error": "Request timed out",
                "response": ""
            }
        
        except requests.exceptions.ConnectionError:
            logger.error("Failed to connect to Ollama. Is it running?")
            return {
                "success": False,
                "error": "Connection failed. Ensure Ollama is running.",
                "response": ""
            }
        
        except Exception as e:
            logger.error(f"Ollama request failed: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "response": ""
            }
    
    def chat(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 2048,
        top_p: float = 0.9
    ) -> Dict[str, Any]:
        """
        Chat completion using Ollama API with message history
        
        Args:
            messages: List of message dicts with 'role' and 'content'
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            top_p: Nucleus sampling parameter
        
        Returns:
            Dict containing response and metadata
        """
        try:
            payload = {
                "model": self.model,
                "messages": messages,
                "stream": False,
                "options": {
                    "temperature": temperature,
                    "num_predict": max_tokens,
                    "top_p": top_p,
                }
            }
            
            logger.debug(f"Sending chat request to Ollama with {len(messages)} messages")
            
            response = requests.post(
                self.chat_url,
                json=payload,
                timeout=self.timeout
            )
            
            response.raise_for_status()
            result = response.json()
            
            message = result.get("message", {})
            
            return {
                "success": True,
                "response": message.get("content", ""),
                "role": message.get("role", "assistant"),
                "model": result.get("model", self.model),
                "total_duration": result.get("total_duration", 0),
                "prompt_eval_count": result.get("prompt_eval_count", 0),
                "eval_count": result.get("eval_count", 0)
            }
            
        except requests.exceptions.Timeout:
            logger.error(f"Ollama chat request timed out after {self.timeout}s")
            return {
                "success": False,
                "error": "Request timed out",
                "response": ""
            }
        
        except requests.exceptions.ConnectionError:
            logger.error("Failed to connect to Ollama. Is it running?")
            return {
                "success": False,
                "error": "Connection failed. Ensure Ollama is running.",
                "response": ""
            }
        
        except Exception as e:
            logger.error(f"Ollama chat request failed: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "response": ""
            }
    
    def check_connection(self) -> bool:
        """Check if Ollama is running and accessible"""
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            response.raise_for_status()
            logger.info("Successfully connected to Ollama")
            return True
        except Exception as e:
            logger.error(f"Cannot connect to Ollama: {str(e)}")
            return False
    
    def list_models(self) -> List[Dict[str, Any]]:
        """
        List available models in Ollama with details
        
        Returns:
            List of dicts containing model information (name, size, modified date)
        """
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            response.raise_for_status()
            data = response.json()
            models = data.get("models", [])
            logger.info(f"Found {len(models)} available models")
            return models
        except Exception as e:
            logger.error(f"Failed to list models: {str(e)}")
            return []
    
    def set_model(self, model_name: str) -> bool:
        """
        Change the current model
        
        Args:
            model_name: Name of the model to use
        
        Returns:
            True if model was changed successfully
        """
        try:
            # Verify model exists
            models = self.list_models()
            model_names = [m.get("name", "") for m in models]
            
            if model_name not in model_names:
                logger.error(f"Model '{model_name}' not found in available models")
                return False
            
            self.model = model_name
            logger.info(f"Switched to model: {model_name}")
            return True
        except Exception as e:
            logger.error(f"Failed to set model: {str(e)}")
            return False

# Made with Bob
