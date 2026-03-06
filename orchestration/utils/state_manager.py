"""
State manager for EVA conversation state
Manages conversation history, context, emotional state, and user preferences
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
from enum import Enum
import json


class Role(Enum):
    """EVA's behavioral roles"""
    FRIEND = "friend"
    ADVISOR = "advisor"
    ASSISTANT = "assistant"


class EmotionalState(Enum):
    """User emotional states"""
    HAPPY = "happy"
    SAD = "sad"
    ANXIOUS = "anxious"
    EXCITED = "excited"
    FRUSTRATED = "frustrated"
    NEUTRAL = "neutral"
    ANGRY = "angry"
    CONFUSED = "confused"


class ConversationState:
    """Manages the state of a conversation session"""
    
    def __init__(self, user_id: str = "default_user", conversation_id: Optional[str] = None):
        self.user_id = user_id
        self.conversation_id = conversation_id or self._generate_conversation_id()
        self.current_role = Role.FRIEND
        self.emotional_state = {
            "current": EmotionalState.NEUTRAL,
            "intensity": 5,  # 1-10 scale
            "history": []
        }
        self.conversation_history: List[Dict[str, Any]] = []
        self.conversation_summary: str = ""  # Summary of older messages
        self.last_summarized_index: int = 0  # Track what's been summarized
        self.active_context: Dict[str, Any] = {}
        self.pending_actions: List[Dict[str, Any]] = []
        self.session_memories: List[Dict[str, Any]] = []
        self.user_preferences: Dict[str, Any] = {}
        self.user_profile: Dict[str, Any] = {}  # User profile from onboarding
        self.onboarding_completed: bool = False
        self.created_at = datetime.now()
        self.last_updated = datetime.now()
    
    def _generate_conversation_id(self) -> str:
        """Generate unique conversation ID"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return f"conv_{self.user_id}_{timestamp}"
    
    def add_message(self, role: str, content: str, metadata: Optional[Dict[str, Any]] = None) -> None:
        """
        Add a message to conversation history
        
        Args:
            role: 'user' or 'assistant'
            content: Message content
            metadata: Additional metadata (intent, tools used, etc.)
        """
        message = {
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat(),
            "metadata": metadata or {}
        }
        self.conversation_history.append(message)
        self.last_updated = datetime.now()
    
    def get_recent_messages(self, count: int = 10) -> List[Dict[str, Any]]:
        """Get the most recent N messages"""
        return self.conversation_history[-count:] if self.conversation_history else []
    
    def get_conversation_context(self, max_messages: int = 10, include_summary: bool = True) -> str:
        """
        Get formatted conversation context for LLM
        Includes summary of older messages + recent messages
        
        Args:
            max_messages: Maximum number of recent messages to include
            include_summary: Whether to include summary of older messages
        
        Returns:
            Formatted conversation history string with summary
        """
        recent = self.get_recent_messages(max_messages)
        
        context_parts = []
        
        # Add summary of older messages if available
        if include_summary and self.conversation_summary:
            context_parts.append("=== Previous Conversation Summary ===")
            context_parts.append(self.conversation_summary)
            context_parts.append("\n=== Recent Messages ===")
        
        # Add recent messages
        if not recent:
            if not self.conversation_summary:
                return "No previous conversation."
            # If we have summary but no recent messages, just return summary
            return self.conversation_summary
        
        for msg in recent:
            role_label = "User" if msg["role"] == "user" else "EVA"
            context_parts.append(f"{role_label}: {msg['content']}")
        
        return "\n".join(context_parts)
    
    def set_conversation_summary(self, summary: str) -> None:
        """
        Set the summary of older conversation messages
        
        Args:
            summary: Summary text of older messages
        """
        self.conversation_summary = summary
        self.last_summarized_index = len(self.conversation_history)
        self.last_updated = datetime.now()
    
    def needs_summarization(self, threshold: int = 20) -> bool:
        """
        Check if conversation needs summarization
        
        Args:
            threshold: Number of messages before summarization is needed
        
        Returns:
            True if summarization is needed
        """
        total_messages = len(self.conversation_history)
        unsummarized_messages = total_messages - self.last_summarized_index
        return unsummarized_messages >= threshold
    
    def get_messages_for_summarization(self, keep_recent: int = 10) -> List[Dict[str, Any]]:
        """
        Get messages that should be summarized (excluding recent ones)
        
        Args:
            keep_recent: Number of recent messages to keep unsummarized
        
        Returns:
            List of messages to summarize
        """
        total_messages = len(self.conversation_history)
        if total_messages <= keep_recent:
            return []
        
        # Get messages from last_summarized_index to (total - keep_recent)
        end_index = total_messages - keep_recent
        return self.conversation_history[self.last_summarized_index:end_index]
    
    def set_role(self, role: Role) -> None:
        """Set EVA's current behavioral role"""
        self.current_role = role
        self.last_updated = datetime.now()
    
    def get_role(self) -> Role:
        """Get current role"""
        return self.current_role
    
    def update_emotional_state(self, emotion: EmotionalState, intensity: int) -> None:
        """
        Update user's emotional state
        
        Args:
            emotion: The detected emotion
            intensity: Intensity level (1-10)
        """
        # Add to history
        self.emotional_state["history"].append({
            "emotion": emotion.value,
            "intensity": intensity,
            "timestamp": datetime.now().isoformat()
        })
        
        # Update current state
        self.emotional_state["current"] = emotion
        self.emotional_state["intensity"] = max(1, min(10, intensity))
        self.last_updated = datetime.now()
    
    def get_emotional_state(self) -> Dict[str, Any]:
        """Get current emotional state"""
        return {
            "emotion": self.emotional_state["current"].value,
            "intensity": self.emotional_state["intensity"]
        }
    
    def add_pending_action(self, action_type: str, parameters: Dict[str, Any]) -> None:
        """Add an action to be executed"""
        action = {
            "type": action_type,
            "parameters": parameters,
            "timestamp": datetime.now().isoformat(),
            "status": "pending"
        }
        self.pending_actions.append(action)
        self.last_updated = datetime.now()
    
    def get_pending_actions(self) -> List[Dict[str, Any]]:
        """Get all pending actions"""
        return [a for a in self.pending_actions if a["status"] == "pending"]
    
    def mark_action_completed(self, action_index: int) -> None:
        """Mark an action as completed"""
        if 0 <= action_index < len(self.pending_actions):
            self.pending_actions[action_index]["status"] = "completed"
            self.last_updated = datetime.now()
    
    def add_session_memory(self, memory_type: str, content: str, importance: int = 5) -> None:
        """
        Add a memory for this session
        
        Args:
            memory_type: Type of memory (fact, preference, event, etc.)
            content: Memory content
            importance: Importance level (1-10)
        """
        memory = {
            "type": memory_type,
            "content": content,
            "importance": importance,
            "timestamp": datetime.now().isoformat()
        }
        self.session_memories.append(memory)
        self.last_updated = datetime.now()
    
    def cleanup_old_messages(self, keep_recent: int = 10) -> int:
        """
        Remove old messages from memory after they've been summarized
        Keeps only recent messages to save memory
        
        Args:
            keep_recent: Number of recent messages to keep
        
        Returns:
            Number of messages removed
        """
        total_messages = len(self.conversation_history)
        if total_messages <= keep_recent:
            return 0
        
        # Keep only the last N messages
        messages_to_remove = total_messages - keep_recent
        self.conversation_history = self.conversation_history[-keep_recent:]
        
        # Update the summarized index to reflect the cleanup
        self.last_summarized_index = 0
        self.last_updated = datetime.now()
        
        return messages_to_remove
    
    def set_user_profile(self, profile: Dict[str, Any]) -> None:
        """
        Set user profile from onboarding
        
        Args:
            profile: User profile data
        """
        self.user_profile = profile
        self.onboarding_completed = True
        self.last_updated = datetime.now()
    
    def get_user_profile(self) -> Dict[str, Any]:
        """Get user profile"""
        return self.user_profile
    
    def is_onboarding_completed(self) -> bool:
        """Check if onboarding is completed"""
        return self.onboarding_completed
    
    def get_session_memories(self, min_importance: int = 0) -> List[Dict[str, Any]]:
        """Get session memories above a certain importance threshold"""
        return [m for m in self.session_memories if m["importance"] >= min_importance]
    
    def update_context(self, key: str, value: Any) -> None:
        """Update active context with key-value pair"""
        self.active_context[key] = value
        self.last_updated = datetime.now()
    
    def get_context(self, key: str, default: Any = None) -> Any:
        """Get value from active context"""
        return self.active_context.get(key, default)
    
    def clear_context(self) -> None:
        """Clear active context"""
        self.active_context = {}
        self.last_updated = datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert state to dictionary for serialization"""
        return {
            "user_id": self.user_id,
            "conversation_id": self.conversation_id,
            "current_role": self.current_role.value,
            "emotional_state": {
                "current": self.emotional_state["current"].value,
                "intensity": self.emotional_state["intensity"],
                "history": self.emotional_state["history"]
            },
            "conversation_history": self.conversation_history,
            "conversation_summary": self.conversation_summary,
            "last_summarized_index": self.last_summarized_index,
            "active_context": self.active_context,
            "pending_actions": self.pending_actions,
            "session_memories": self.session_memories,
            "user_preferences": self.user_preferences,
            "user_profile": self.user_profile,
            "onboarding_completed": self.onboarding_completed,
            "created_at": self.created_at.isoformat(),
            "last_updated": self.last_updated.isoformat()
        }
    
    def to_json(self) -> str:
        """Convert state to JSON string"""
        return json.dumps(self.to_dict(), indent=2)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ConversationState':
        """Create ConversationState from dictionary"""
        state = cls(
            user_id=data.get("user_id", "default_user"),
            conversation_id=data.get("conversation_id")
        )
        
        # Restore role
        role_value = data.get("current_role", "friend")
        state.current_role = Role(role_value)
        
        # Restore emotional state
        emotional_data = data.get("emotional_state", {})
        emotion_value = emotional_data.get("current", "neutral")
        state.emotional_state["current"] = EmotionalState(emotion_value)
        state.emotional_state["intensity"] = emotional_data.get("intensity", 5)
        state.emotional_state["history"] = emotional_data.get("history", [])
        
        # Restore other fields
        state.conversation_history = data.get("conversation_history", [])
        state.conversation_summary = data.get("conversation_summary", "")
        state.last_summarized_index = data.get("last_summarized_index", 0)
        state.active_context = data.get("active_context", {})
        state.pending_actions = data.get("pending_actions", [])
        state.session_memories = data.get("session_memories", [])
        state.user_preferences = data.get("user_preferences", {})
        state.user_profile = data.get("user_profile", {})
        state.onboarding_completed = data.get("onboarding_completed", False)
        
        return state

# Made with Bob
