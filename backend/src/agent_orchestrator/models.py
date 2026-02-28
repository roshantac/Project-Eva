"""Data models for messages, sessions, and tools."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from pydantic import BaseModel, Field

from src.llm_core.models import Message


# ---------------------------------------------------------------------------
# Session
# ---------------------------------------------------------------------------


class SessionData(BaseModel):
    """Session payload stored in db/sessions/{session_id}.json."""

    session_id: str
    messages: list[dict[str, Any]] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @classmethod
    def from_messages(cls, session_id: str, messages: list[Message], metadata: dict[str, Any] | None = None) -> SessionData:
        """Build from Message list."""
        return cls(
            session_id=session_id,
            messages=[m.model_dump() for m in messages],
            metadata=metadata or {},
        )

    def to_messages(self) -> list[Message]:
        """Convert stored messages to Message list."""
        return [Message(**m) for m in self.messages]


# ---------------------------------------------------------------------------
# Tools
# ---------------------------------------------------------------------------


@dataclass
class ToolResult:
    """Result of a single tool execution."""

    success: bool
    content: str | None = None
    error: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class ToolDef:
    """Tool definition for the orchestrator and LLM."""

    name: str
    description: str
    parameters: dict[str, Any]  # JSON Schema

    def to_tool_schema(self) -> dict[str, Any]:
        """Standard function-calling schema (OpenAI-style) for any LLM provider."""
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.parameters,
            },
        }

    def to_ollama_tool(self) -> dict[str, Any]:
        """Alias for to_tool_schema(); kept for backward compatibility."""
        return self.to_tool_schema()
