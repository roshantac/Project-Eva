"""Base type for embedding backends."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Literal, Optional


class EmbeddingBase(ABC):
    """Base class for embedding backends used by the memory store."""

    @abstractmethod
    def embed(
        self,
        text: str,
        memory_action: Optional[Literal["add", "search", "update"]] = None,
    ) -> list[float]:
        """Return an embedding vector for the given text."""
        raise NotImplementedError
