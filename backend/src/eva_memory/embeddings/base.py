from abc import ABC, abstractmethod
from typing import Literal, Optional

from ..config import OllamaConfig


class EmbeddingBase(ABC):
    """Base class for embedding backends used by the memory store."""

    def __init__(self, config: Optional[OllamaConfig] = None) -> None:
        self.config = config or OllamaConfig()

    @abstractmethod
    def embed(
        self,
        text: str,
        memory_action: Optional[Literal["add", "search", "update"]] = None,
    ) -> list[float]:
        """Return an embedding vector for the given text."""
        raise NotImplementedError

