"""
Utility modules for EVA system
"""

from utils.logger import get_logger, EVALogger
from utils.ollama_client import OllamaClient
from utils.config_manager import get_config, ConfigManager
from utils.state_manager import ConversationState, Role, EmotionalState

__all__ = [
    'get_logger',
    'EVALogger',
    'OllamaClient',
    'get_config',
    'ConfigManager',
    'ConversationState',
    'Role',
    'EmotionalState'
]

# Made with Bob
