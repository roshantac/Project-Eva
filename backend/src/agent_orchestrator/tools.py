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


def _get_memory_engine():
    """Lazy import for LLM-aware memory engine (used when infer=True)."""
    try:
        from src.eva_memory.engine import LlmAwareMemoryEngine
        from src.eva_memory.llm_client import MemoryLLMClient
        store = _get_memory_store()
        if store is None:
            return None
        return LlmAwareMemoryEngine(store=store, llm_client=MemoryLLMClient())
    except Exception:
        return None


class AddMemoryTool(BaseTool):
    """Store a memory for the user (text and optional metadata). When infer=True, extract facts from messages and update memory via LLM."""

    def __init__(self, user_id: str, store: Any = None):
        self._user_id = user_id
        self._store = store or _get_memory_store()

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
        if self._store is None:
            return ToolResult(success=False, error="Memory store not available")
        infer = params.get("infer") is True
        if infer:
            engine = _get_memory_engine()
            if engine is None:
                return ToolResult(success=False, error="Memory engine (LLM) not available for infer")
            raw_messages = params.get("messages") or []
            if not raw_messages:
                text = (params.get("text") or "").strip()
                if text:
                    raw_messages = [{"role": "user", "content": text}]
            if not raw_messages:
                return ToolResult(success=False, error="When infer is true, provide messages or text")
            from src.llm_core import Message
            messages = [Message(role=m.get("role", "user"), content=m.get("content") or "") for m in raw_messages]
            category_hint = params.get("category_hint")
            try:
                changes = await engine.infer_and_update_from_messages(
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
    """Search the user's memories by query. Supports semantic, text, or hybrid mode and optional category filter."""

    def __init__(self, user_id: str, store: Any = None):
        self._user_id = user_id
        self._store = store or _get_memory_store()

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
        if self._store is None:
            return ToolResult(success=False, error="Memory store not available")
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
                    self._store.search_text,
                    self._user_id,
                    query,
                    k,
                    categories,
                )
            elif mode == "hybrid":
                hits = await asyncio.to_thread(
                    self._store.search_hybrid,
                    self._user_id,
                    query,
                    k,
                    categories,
                )
            else:
                hits = await asyncio.to_thread(
                    self._store.search,
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


def get_tools_for_user(user_id: str, store: Any = None) -> list[BaseTool]:
    """Return the default tool list for a user (includes memory tools bound to user_id)."""
    s = store or _get_memory_store()
    return [
        GetTimeTool(),
        AddMemoryTool(user_id, s),
        SearchMemoryTool(user_id, s),
    ]
