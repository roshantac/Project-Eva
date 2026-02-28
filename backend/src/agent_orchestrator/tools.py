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
# Memory tools (require eva_memory in src)
# ---------------------------------------------------------------------------

def _get_memory_store():
    """Lazy import to avoid circular dependency and allow eva_memory to live under src."""
    try:
        from src.eva_memory import MemoryStore
        from src.eva_memory.config import MemoryStoreConfig
        return MemoryStore(MemoryStoreConfig())
    except Exception:
        return None


class AddMemoryTool(BaseTool):
    """Store a memory for the user (text and optional metadata)."""

    def __init__(self, user_id: str, store: Any = None):
        self._user_id = user_id
        self._store = store or _get_memory_store()

    @property
    def name(self) -> str:
        return "add_memory"

    @property
    def description(self) -> str:
        return "Store a memory for the user. Use this when the user shares something to remember (e.g. name, preference, fact)."

    @property
    def parameters(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "text": {"type": "string", "description": "The memory content to store"},
                "metadata": {"type": "object", "description": "Optional key-value metadata (e.g. category)"},
            },
            "required": ["text"],
        }

    async def execute(self, params: dict[str, Any]) -> ToolResult:
        if self._store is None:
            return ToolResult(success=False, error="Memory store not available")
        text = (params.get("text") or "").strip()
        if not text:
            return ToolResult(success=False, error="text is required")
        metadata = params.get("metadata")
        if isinstance(metadata, str):
            try:
                metadata = json.loads(metadata)
            except Exception:
                metadata = None
        try:
            record = await asyncio.to_thread(
                self._store.add,
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
    """Search the user's memories by semantic similarity."""

    def __init__(self, user_id: str, store: Any = None):
        self._user_id = user_id
        self._store = store or _get_memory_store()

    @property
    def name(self) -> str:
        return "search_memory"

    @property
    def description(self) -> str:
        return "Search the user's stored memories by a query. Returns the most relevant memories."

    @property
    def parameters(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Search query"},
                "k": {"type": "integer", "description": "Max number of results (default 5)", "default": 5},
            },
            "required": ["query"],
        }

    async def execute(self, params: dict[str, Any]) -> ToolResult:
        if self._store is None:
            return ToolResult(success=False, error="Memory store not available")
        query = (params.get("query") or "").strip()
        if not query:
            return ToolResult(success=False, error="query is required")
        k = params.get("k", 5)
        if not isinstance(k, int) or k < 1:
            k = 5
        try:
            hits = await asyncio.to_thread(
                self._store.search,
                self._user_id,
                query,
                k,
            )
            if not hits:
                return ToolResult(success=True, content="No matching memories found.")
            lines = [f"- [{h.score:.2f}] {h.memory.text}" for h in hits]
            return ToolResult(success=True, content="\n".join(lines))
        except Exception as e:
            return ToolResult(success=False, error=str(e))


def get_tools_for_user(user_id: str, store: Any = None) -> list[BaseTool]:
    """Return the default tool list for a user (includes memory tools bound to user_id)."""
    s = store or _get_memory_store()
    return [
        GetTimeTool(),
        AddMemoryTool(user_id, s),
        SearchMemoryTool(user_id, s),
    ]
