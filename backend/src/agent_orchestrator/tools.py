"""Tool protocol and example tools."""

from __future__ import annotations

import asyncio
import json
from abc import ABC, abstractmethod
from typing import Any

from .models import ToolDef, ToolResult


class BaseTool(ABC):
    """Base class for orchestrator tools."""

    @property
    @abstractmethod
    def name(self) -> str:
        ...

    @property
    @abstractmethod
    def description(self) -> str:
        ...

    @property
    @abstractmethod
    def parameters(self) -> dict[str, Any]:
        """JSON Schema for parameters."""
        ...

    @abstractmethod
    async def execute(self, params: dict[str, Any]) -> ToolResult:
        ...

    def to_def(self) -> ToolDef:
        return ToolDef(name=self.name, description=self.description, parameters=self.parameters)

    def to_tool_schema(self) -> dict[str, Any]:
        """Standard function-calling schema for any LLM provider."""
        return self.to_def().to_tool_schema()

    def to_ollama_tool(self) -> dict[str, Any]:
        """Alias for to_tool_schema(); kept for backward compatibility."""
        return self.to_tool_schema()


# ---------------------------------------------------------------------------
# Example tool: get current time
# ---------------------------------------------------------------------------

from datetime import datetime, timezone


class GetTimeTool(BaseTool):
    """Returns current UTC time as ISO string."""

    @property
    def name(self) -> str:
        return "get_time"

    @property
    def description(self) -> str:
        return "Get the current UTC date and time in ISO format."

    @property
    def parameters(self) -> dict[str, Any]:
        return {"type": "object", "properties": {}, "required": []}

    async def execute(self, params: dict[str, Any]) -> ToolResult:
        now = datetime.now(timezone.utc).isoformat()
        return ToolResult(success=True, content=now)


# ---------------------------------------------------------------------------
# Memory tools (use eva_memory MemoryClient from app deps)
# ---------------------------------------------------------------------------

def _get_memory_client():
    """Lazy import: MemoryClient from app deps (config from main_config)."""
    try:
        from src.deps import get_memory_client
        return get_memory_client()
    except Exception:
        return None


class AddMemoryTool(BaseTool):
    """Store a memory for the user (text and optional metadata). When infer=True, extract facts from messages and update memory via LLM."""

    def __init__(self, user_id: str, client: Any = None):
        self._user_id = user_id
        self._client = client or _get_memory_client()

    @property
    def name(self) -> str:
        return "add_memory"

    @property
    def description(self) -> str:
        return "Store a memory for the user. Use when the user shares something to remember (e.g. name, preference, fact). If infer is true, pass messages to extract and merge facts automatically."

    @property
    def parameters(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "text": {"type": "string", "description": "The memory content to store (used when infer is false)"},
                "metadata": {"type": "object", "description": "Optional key-value metadata (e.g. category)"},
                "infer": {"type": "boolean", "description": "If true, extract facts from messages and update memory using LLM", "default": False},
                "messages": {
                    "type": "array",
                    "description": "Conversation messages for fact extraction when infer is true",
                    "items": {
                        "type": "object",
                        "properties": {"role": {"type": "string"}, "content": {"type": "string"}},
                        "required": ["role", "content"],
                    },
                },
                "category_hint": {"type": "string", "description": "Optional category hint when infer is true"},
            },
            "required": [],
        }

    async def execute(self, params: dict[str, Any]) -> ToolResult:
        if self._client is None:
            return ToolResult(success=False, error="Memory client not available")
        infer = params.get("infer") is True
        if infer:
            from src.eva_memory import Message
            raw_messages = params.get("messages") or []
            if not raw_messages:
                text = (params.get("text") or "").strip()
                if text:
                    raw_messages = [{"role": "user", "content": text}]
            if not raw_messages:
                return ToolResult(success=False, error="When infer is true, provide messages or text")
            messages = [Message(role=m.get("role", "user"), content=m.get("content") or "") for m in raw_messages]
            category_hint = params.get("category_hint")
            try:
                changes = await self._client.add_from_messages(
                    self._user_id, messages, category_hint=category_hint
                )
                add_n = sum(1 for c in changes if c.event == "ADD")
                up_n = sum(1 for c in changes if c.event == "UPDATE")
                del_n = sum(1 for c in changes if c.event == "DELETE")
                content = f"Inferred memory updates: {add_n} added, {up_n} updated, {del_n} deleted."
                return ToolResult(success=True, content=content, metadata={"changes": len(changes)})
            except Exception as e:
                return ToolResult(success=False, error=str(e))
        text = (params.get("text") or "").strip()
        if not text:
            return ToolResult(success=False, error="text is required when infer is false")
        metadata = params.get("metadata")
        if isinstance(metadata, str):
            try:
                metadata = json.loads(metadata)
            except Exception:
                metadata = None
        try:
            record = await asyncio.to_thread(
                self._client.add,
                self._user_id,
                text,
                metadata,
            )
            return ToolResult(
                success=True,
                content=f"Stored memory: {record.memory_id}",
                metadata={"memory_id": record.memory_id},
            )
        except Exception as e:
            return ToolResult(success=False, error=str(e))


class SearchMemoryTool(BaseTool):
    """Search the user's memories by query. Supports semantic, text, or hybrid mode and optional category filter."""

    def __init__(self, user_id: str, client: Any = None):
        self._user_id = user_id
        self._client = client or _get_memory_client()

    @property
    def name(self) -> str:
        return "search_memory"

    @property
    def description(self) -> str:
        return "Search the user's stored memories. Use mode semantic (default), text, or hybrid. Optionally filter by category."

    @property
    def parameters(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Search query"},
                "k": {"type": "integer", "description": "Max number of results (default 5)", "default": 5},
                "limit": {"type": "integer", "description": "Alias for k"},
                "mode": {
                    "type": "string",
                    "enum": ["semantic", "text", "hybrid"],
                    "description": "Search mode: semantic (vector), text (FTS), or hybrid (both combined)",
                    "default": "semantic",
                },
                "category": {"type": "string", "description": "Filter by one category (e.g. work_career, health_wellness)"},
                "categories": {"type": "array", "items": {"type": "string"}, "description": "Filter by multiple categories"},
            },
            "required": ["query"],
        }

    async def execute(self, params: dict[str, Any]) -> ToolResult:
        if self._client is None:
            return ToolResult(success=False, error="Memory client not available")
        query = (params.get("query") or "").strip()
        if not query:
            return ToolResult(success=False, error="query is required")
        k = params.get("k") or params.get("limit") or 5
        if not isinstance(k, int) or k < 1:
            k = 5
        mode = (params.get("mode") or "semantic").strip().lower()
        if mode not in ("semantic", "text", "hybrid"):
            mode = "semantic"
        categories = params.get("categories")
        if categories is None and params.get("category"):
            categories = [params["category"]]
        if categories is not None and not isinstance(categories, list):
            categories = [categories] if categories else None
        try:
            if mode == "text":
                hits = await asyncio.to_thread(
                    self._client.search_text,
                    self._user_id,
                    query,
                    k,
                    categories,
                )
            elif mode == "hybrid":
                hits = await asyncio.to_thread(
                    self._client.search_hybrid,
                    self._user_id,
                    query,
                    k,
                    categories,
                )
            else:
                hits = await asyncio.to_thread(
                    self._client.search,
                    self._user_id,
                    query,
                    k,
                    categories,
                )
            if not hits:
                return ToolResult(success=True, content="No matching memories found.")
            lines = []
            for h in hits:
                cat = (h.memory.metadata or {}).get("category", "")
                prefix = f"[{h.score:.2f}]" + (f" [{cat}]" if cat else "")
                lines.append(f"- {prefix} {h.memory.text}")
            return ToolResult(success=True, content="\n".join(lines))
        except Exception as e:
            return ToolResult(success=False, error=str(e))


def get_tools_for_user(user_id: str, memory_client: Any = None) -> list[BaseTool]:
    """Return the default tool list for a user (includes memory tools bound to user_id)."""
    client = memory_client or _get_memory_client()
    return [
        GetTimeTool(),
        AddMemoryTool(user_id, client),
        SearchMemoryTool(user_id, client),
    ]
