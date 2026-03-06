"""
Configuration manager for EVA system
Loads and manages configuration from YAML file
"""

import yaml
from pathlib import Path
from typing import Dict, Any, Optional
from utils.logger import get_logger

logger = get_logger()


class ConfigManager:
    """Manages configuration loading and access"""
    
    def __init__(self, config_path: str = "config/config.yaml"):
        self.config_path = Path(config_path)
        self.config: Dict[str, Any] = {}
        self.load_config()
    
    def load_config(self) -> None:
        """Load configuration from YAML file"""
        try:
            if not self.config_path.exists():
                logger.warning(f"Config file not found: {self.config_path}. Using defaults.")
                self._load_defaults()
                return
            
            with open(self.config_path, 'r') as f:
                self.config = yaml.safe_load(f)
            
            logger.info(f"Configuration loaded from {self.config_path}")
        
        except Exception as e:
            logger.error(f"Failed to load config: {str(e)}. Using defaults.")
            self._load_defaults()
    
    def _load_defaults(self) -> None:
        """Load default configuration"""
        self.config = {
            "model": {
                "name": "gemma:7b",
                "base_url": "http://localhost:11434",
                "timeout": 120
            },
            "agents": {
                "audio_correction": {"temperature": 0.3, "max_tokens": 1024, "top_p": 0.9},
                "intent_classification": {"temperature": 0.2, "max_tokens": 512, "top_p": 0.85},
                "conversation_manager": {"temperature": 0.7, "max_tokens": 2048, "top_p": 0.95},
                "emotional_detector": {"temperature": 0.4, "max_tokens": 512, "top_p": 0.9},
                "memory_classifier": {"temperature": 0.3, "max_tokens": 1024, "top_p": 0.9}
            },
            "context": {
                "max_history_messages": 10,
                "summary_threshold": 20,
                "max_tokens_per_message": 500
            },
            "conversation": {
                "default_role": "friend",
                "enable_proactive_suggestions": True,
                "enable_emotional_tracking": True
            },
            "memory": {
                "short_term_ttl_hours": 24,
                "long_term_importance_threshold": 7
            },
            "web_search": {
                "max_results": 5,
                "timeout": 10
            },
            "logging": {
                "level": "INFO",
                "log_file": "logs/eva.log",
                "log_agent_decisions": True
            }
        }
    
    def get(self, key_path: str, default: Any = None) -> Any:
        """
        Get configuration value using dot notation
        Example: config.get('model.name') returns 'gemma:7b'
        """
        keys = key_path.split('.')
        value = self.config
        
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return default
        
        return value
    
    def set(self, key_path: str, value: Any) -> None:
        """
        Set configuration value using dot notation
        Example: config.set('model.name', 'gemma:2b')
        """
        keys = key_path.split('.')
        config = self.config
        
        # Navigate to the parent of the target key
        for key in keys[:-1]:
            if key not in config:
                config[key] = {}
            config = config[key]
        
        # Set the final value
        config[keys[-1]] = value
        logger.info(f"Configuration updated: {key_path} = {value}")
    
    def get_agent_config(self, agent_name: str) -> Dict[str, Any]:
        """Get configuration for specific agent"""
        return self.get(f'agents.{agent_name}', {})
    
    def get_model_config(self) -> Dict[str, Any]:
        """Get model configuration"""
        return self.get('model', {})
    
    def get_context_config(self) -> Dict[str, Any]:
        """Get context management configuration"""
        return self.get('context', {})
    
    def get_conversation_config(self) -> Dict[str, Any]:
        """Get conversation configuration"""
        return self.get('conversation', {})
    
    def reload(self) -> None:
        """Reload configuration from file"""
        self.load_config()


# Global config instance
_config_instance: Optional[ConfigManager] = None


def get_config(config_path: str = "config/config.yaml") -> ConfigManager:
    """Get or create config manager instance"""
    global _config_instance
    if _config_instance is None:
        _config_instance = ConfigManager(config_path)
    return _config_instance

# Made with Bob
