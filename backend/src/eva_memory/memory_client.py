"""Memory client: search context before LLM, add turn after response (e.g. in background)."""

from __future__ import annotations

import asyncio
from typing import Any, List, Optional

from src.llm_core import Message

from .engine import LlmAwareMemoryEngine
from .service.memory_store import MemoryStore


def get_memory_client() -> Optional["MemoryClient"]:
    """Lazy singleton memory client (store + engine). Returns None if eva_memory unavailable."""
    try:
        from src.eva_memory import MemoryStore
        from src.eva_memory.config import MemoryStoreConfig
        from src.eva_memory.engine import LlmAwareMemoryEngine
        from src.eva_memory.llm_client import MemoryLLMClient
        config = MemoryStoreConfig()
        config.ensure_directories()
        store = MemoryStore(config=config)
        engine = LlmAwareMemoryEngine(store=store, llm_client=MemoryLLMClient())
        return MemoryClient(store=store, engine=engine)
    except Exception:
        return None


class MemoryClient:
    """Facade for per-turn memory: get context (before LLM) and add turn (after, e.g. in background)."""

    def __init__(self, store: MemoryStore, engine: LlmAwareMemoryEngine) -> None:
        self._store = store
        self._engine = engine

    def get_context(
        self,
        user_id: str,
        query: str,
        k: int = 5,
        mode: str = "semantic",
        categories: Optional[List[str]] = None,
    ) -> str:
        """
        Sync search: run memory search and return a single string to inject into the prompt.
        Use before the LLM call so the agent has relevant user context.
        """
        if not query or not user_id:
            return ""
        if mode == "text":
            hits = self._store.search_text(user_id=user_id, query=query, k=k, categories=categories)
        elif mode == "hybrid":
            hits = self._store.search_hybrid(user_id=user_id, query=query, k=k, categories=categories)
        else:
            hits = self._store.search(user_id=user_id, query=query, k=k, categories=categories)
        if not hits:
            return ""
        lines = [f"- {h.memory.text}" for h in hits]
        return "Relevant user context:\n" + "\n".join(lines)

    async def add_turn(
        self,
        user_id: str,
        user_message: str,
        assistant_message: str,
        category_hint: Optional[str] = None,
    ) -> None:
        """
        Add the last turn to memory with inference (extract facts and merge).
        Intended to be run in a background task after the HTTP response is sent.
        """
        if not user_id:
            return
        user_message = (user_message or "").strip()
        assistant_message = (assistant_message or "").strip()
        if not user_message and not assistant_message:
            return
        messages = [
            Message(role="user", content=user_message),
            Message(role="assistant", content=assistant_message),
        ]
        await self._engine.infer_and_update_from_messages(
            user_id, messages, category_hint=category_hint
        )


async def add_turn_background(
    user_id: str,
    user_message: str,
    assistant_message: str,
    category_hint: Optional[str] = None,
) -> None:
    """
    Standalone background task: get client and add turn. No-op if client unavailable.
    Use from FastAPI: background_tasks.add_task(add_turn_background, user_id, user_msg, reply).
    """
    client = get_memory_client()
    if client is None:
        return
    try:
        await client.add_turn(
            user_id=user_id,
            user_message=user_message,
            assistant_message=assistant_message,
            category_hint=category_hint,
        )
    except Exception:
        pass


def get_context_sync(
    user_id: str,
    query: str,
    k: int = 5,
    mode: str = "semantic",
    categories: Optional[List[str]] = None,
) -> str:
    """
    Sync helper: get memory context string. Returns "" if client unavailable.
    Run in thread from async code: context = await asyncio.to_thread(get_context_sync, ...).
    """
    client = get_memory_client()
    if client is None:
        return ""
    return client.get_context(user_id=user_id, query=query, k=k, mode=mode, categories=categories)


__all__ = [
    "MemoryClient",
    "get_memory_client",
    "get_context_sync",
    "add_turn_background",
]
