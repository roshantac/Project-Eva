"""Abstract LLM provider interface for the agent orchestrator."""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import AsyncIterator
from dataclasses import dataclass
from typing import Any

from ..models import Message


@dataclass
class StreamChunk:
    """One chunk from an LLM stream."""

    type: str  # "text_delta" | "done"
    content: str = ""
    tool_calls: list[dict[str, Any]] | None = None


class LLMProvider(ABC):
    """
    Abstract LLM provider. Implement this to plug in any backend (Ollama, OpenAI, etc.).

    The orchestrator only depends on this interface.
    """

    @abstractmethod
    async def chat(
        self,
        messages: list[Message],
        *,
        model: str | None = None,
        tools: list[dict[str, Any]] | None = None,
        **kwargs: Any,
    ) -> tuple[str, list[dict[str, Any]]]:
        """
        Non-streaming chat. Returns (content, tool_calls).

        tool_calls: list of {"id", "name", "params"} (or "arguments").
        """
        ...

    @abstractmethod
    async def stream_chat(
        self,
        messages: list[Message],
        *,
        model: str | None = None,
        tools: list[dict[str, Any]] | None = None,
        **kwargs: Any,
    ) -> AsyncIterator[StreamChunk]:
        """Stream chat; yields text deltas and a final done chunk (with optional tool_calls)."""
        ...
