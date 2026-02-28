"""Data models for messages, sessions, and tools."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Messages
# ---------------------------------------------------------------------------


class Message(BaseModel):
    """A single message in a conversation."""

    role: str  # "system" | "user" | "assistant" | "tool"
    content: str = ""
    tool_calls: list[dict[str, Any]] | None = None
    tool_call_id: str | None = None
    name: str | None = None

    def to_chat_dict(self) -> dict[str, Any]:
        """Format for LLM chat API."""
        out: dict[str, Any] = {"role": self.role, "content": self.content or ""}
        if self.tool_calls is not None:
            out["tool_calls"] = self.tool_calls
        if self.tool_call_id is not None:
            out["tool_call_id"] = self.tool_call_id
        if self.name is not None:
            out["name"] = self.name
        return out


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
