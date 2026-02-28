from __future__ import annotations

from typing import Any

from pydantic import BaseModel


class Message(BaseModel):
    """A single message in a conversation."""

    role: str  # "system" | "user" | "assistant" | "tool"
    content: str = ""
    tool_calls: list[dict[str, Any]] | None = None
    tool_call_id: str | None = None
    name: str | None = None

    def to_chat_dict(self) -> dict[str, Any]:
        """Format for LLM chat APIs."""
        out: dict[str, Any] = {"role": self.role, "content": self.content or ""}
        if self.tool_calls is not None:
            out["tool_calls"] = self.tool_calls
        if self.tool_call_id is not None:
            out["tool_call_id"] = self.tool_call_id
        if self.name is not None:
            out["name"] = self.name
        return out


__all__ = ["Message"]

