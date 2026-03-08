"""EVA Memory: standalone package for add / search / update / delete memory."""

from .config import EvaMemoryConfig, EmbeddingConfig
from .memory_client import MemoryClient
from .models import MemoryChange, MemoryRecord, Message, SearchHit
from .service.memory_store import MemoryStore

__all__ = [
    "EvaMemoryConfig",
    "EmbeddingConfig",
    "MemoryClient",
    "MemoryChange",
    "MemoryRecord",
    "Message",
    "SearchHit",
    "MemoryStore",
]
