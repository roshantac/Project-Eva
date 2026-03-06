"""
Agent modules for EVA system
"""

from agents.base_agent import BaseAgent
from agents.audio_correction_agent import AudioCorrectionAgent
from agents.intent_classifier_agent import IntentClassifierAgent
from agents.emotional_detector_agent import EmotionalDetectorAgent
from agents.memory_classifier_agent import MemoryClassifierAgent
from agents.conversation_manager_agent import ConversationManagerAgent
from agents.orchestrator import AgentOrchestrator

__all__ = [
    'BaseAgent',
    'AudioCorrectionAgent',
    'IntentClassifierAgent',
    'EmotionalDetectorAgent',
    'MemoryClassifierAgent',
    'ConversationManagerAgent',
    'AgentOrchestrator'
]

# Made with Bob
