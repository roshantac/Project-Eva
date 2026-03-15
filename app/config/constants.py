"""
Constants and configuration values for Eva AI
"""

from enum import Enum
from typing import List


class PersonaType(str, Enum):
    """Available persona types"""
    FRIEND = "friend"
    MENTOR = "mentor"
    ADVISOR = "advisor"


class EmotionType(str, Enum):
    """Available emotion types"""
    HAPPY = "happy"
    SAD = "sad"
    ANXIOUS = "anxious"
    EXCITED = "excited"
    ANGRY = "angry"
    NEUTRAL = "neutral"
    CONFUSED = "confused"
    GRATEFUL = "grateful"


class SentimentType(str, Enum):
    """Sentiment types"""
    POSITIVE = "positive"
    NEGATIVE = "negative"
    NEUTRAL = "neutral"


class CommunicationMode(str, Enum):
    """Communication modes"""
    VOICE = "voice"
    TEXT = "text"


class MemoryTag(str, Enum):
    """Memory tag types"""
    GOAL = "goal"
    ACHIEVEMENT = "achievement"
    EMOTIONAL_MOMENT = "emotional_moment"
    IMPORTANT = "important"
    CASUAL = "casual"


class WebSocketEvents:
    """WebSocket event names"""
    # Connection events
    CONNECTION_ESTABLISHED = "CONNECTION_ESTABLISHED"
    DISCONNECT = "disconnect"
    
    # User input events
    USER_TEXT = "USER_TEXT"
    USER_AUDIO_CHUNK = "USER_AUDIO_CHUNK"
    
    # Bot response events
    BOT_TEXT_RESPONSE = "BOT_TEXT_RESPONSE"
    BOT_AUDIO_STREAM = "BOT_AUDIO_STREAM"
    TRANSCRIPTION_RESULT = "TRANSCRIPTION_RESULT"
    
    # Emotion events
    EMOTION_DETECTED = "EMOTION_DETECTED"
    
    # Control events
    PERSONA_CHANGED = "PERSONA_CHANGED"
    MODE_CHANGED = "MODE_CHANGED"
    
    # Memory events
    MEMORY_REQUEST = "MEMORY_REQUEST"
    MEMORY_DATA = "MEMORY_DATA"
    MEMORY_ADD = "MEMORY_ADD"
    MEMORY_UPDATE = "MEMORY_UPDATE"
    MEMORY_DELETE = "MEMORY_DELETE"
    MEMORY_UPDATED = "MEMORY_UPDATED"
    
    # Tool events
    TOOL_USED = "TOOL_USED"
    
    # Processing events
    PROCESSING_START = "PROCESSING_START"
    PROCESSING_END = "PROCESSING_END"
    
    # Audio control
    STOP_AUDIO = "STOP_AUDIO"
    
    # Conversation events
    CONVERSATIONS_REQUEST = "CONVERSATIONS_REQUEST"
    CONVERSATIONS_LIST = "CONVERSATIONS_LIST"
    CONVERSATION_LOAD = "CONVERSATION_LOAD"
    CONVERSATION_LOADED = "CONVERSATION_LOADED"
    CONVERSATION_DELETE = "CONVERSATION_DELETE"
    CONVERSATION_DELETED = "CONVERSATION_DELETED"
    
    # Error events
    ERROR = "ERROR"


# Memory settings
MAX_SHORT_TERM_MEMORY = 20
MIN_MEMORY_IMPORTANCE = 7

# Audio settings
MAX_AUDIO_DURATION = 60  # seconds
AUDIO_SAMPLE_RATE = 16000
AUDIO_CHANNELS = 1
AUDIO_BIT_DEPTH = 16

# LLM settings
DEFAULT_MAX_TOKENS = 2000
DEFAULT_TEMPERATURE = 0.7
DEFAULT_TOP_P = 0.9

# Tool settings
TOOL_TIMEOUT = 30  # seconds

# Emotion detection keywords
EMOTION_KEYWORDS = {
    EmotionType.HAPPY: [
        "happy", "joy", "excited", "great", "wonderful", "amazing",
        "fantastic", "awesome", "love", "delighted", "pleased", "glad"
    ],
    EmotionType.SAD: [
        "sad", "unhappy", "depressed", "down", "miserable", "upset",
        "disappointed", "heartbroken", "lonely", "blue", "gloomy"
    ],
    EmotionType.ANXIOUS: [
        "anxious", "worried", "nervous", "stressed", "tense", "uneasy",
        "concerned", "afraid", "scared", "panic", "overwhelmed"
    ],
    EmotionType.EXCITED: [
        "excited", "thrilled", "enthusiastic", "eager", "pumped",
        "energized", "hyped", "stoked", "fired up"
    ],
    EmotionType.ANGRY: [
        "angry", "mad", "furious", "irritated", "annoyed", "frustrated",
        "rage", "outraged", "pissed", "livid"
    ],
    EmotionType.CONFUSED: [
        "confused", "puzzled", "perplexed", "bewildered", "lost",
        "uncertain", "unclear", "don't understand"
    ],
    EmotionType.GRATEFUL: [
        "grateful", "thankful", "appreciate", "thanks", "thank you",
        "blessed", "fortunate", "lucky"
    ]
}

# Sentiment keywords
SENTIMENT_KEYWORDS = {
    SentimentType.POSITIVE: [
        "good", "great", "excellent", "wonderful", "fantastic", "amazing",
        "love", "like", "enjoy", "happy", "pleased", "satisfied"
    ],
    SentimentType.NEGATIVE: [
        "bad", "terrible", "awful", "horrible", "hate", "dislike",
        "unhappy", "disappointed", "frustrated", "angry", "sad"
    ]
}
