"""Public client for EVA Memory. Create with config, then add / search / update / delete."""

from __future__ import annotations

import asyncio
from typing import Any, Dict, List, Optional

from .config import EvaMemoryConfig, MemoryStoreConfig
from .engine import LlmAwareMemoryEngine
from .models import MemoryChange, MemoryRecord, Message, SearchHit
from .llm_client import MemoryLLMClient
from .service.memory_store import MemoryStore


class MemoryClient:
    """
    Client for EVA Memory. Create with EvaMemoryConfig; then use add, search, update, delete.

    Example:
        config = EvaMemoryConfig(
            sqlite_path=Path("./data/memories.db"),
            faiss_dir=Path("./data/faiss"),
        )
        client = MemoryClient(config=config)
        client.add(user_id="user1", text="User prefers dark mode")
        hits = client.search(user_id="user1", query="theme preference", k=5)
    """

    def __init__(self, config: EvaMemoryConfig) -> None:
        if not isinstance(config, EvaMemoryConfig):
            raise TypeError("MemoryClient requires EvaMemoryConfig")
        config.ensure_directories()
        store_config = MemoryStoreConfig(
            embedding=config.embedding,
            sqlite_path=config.sqlite_path,
            faiss_dir=config.faiss_dir,
        )
        store_config.ensure_directories()
        self._config = config
        self._store = MemoryStore(config=store_config)
        self._engine = LlmAwareMemoryEngine(
            store=self._store,
            llm_client=MemoryLLMClient(config=config.llm),
        )

    # -------------------------------------------------------------------------
    # Core API: add, search, update, delete, get, list
    # -------------------------------------------------------------------------

    def add(
        self,
        user_id: str,
        text: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> MemoryRecord:
        """Add a new memory for the user. Returns the created record."""
        return self._store.add(user_id=user_id, text=text, metadata=metadata)

    def search(
        self,
        user_id: str,
        query: str,
        k: int = 5,
        categories: Optional[List[str]] = None,
    ) -> List[SearchHit]:
        """Semantic (vector) search. Optionally filter by metadata category."""
        return self._store.search(
            user_id=user_id,
            query=query,
            k=k,
            categories=categories,
        )

    def update(
        self,
        user_id: str,
        memory_id: str,
        new_text: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> MemoryRecord:
        """Update an existing memory's text and optional metadata."""
        return self._store.update(
            user_id=user_id,
            memory_id=memory_id,
            new_text=new_text,
            metadata=metadata,
        )

    def delete(self, user_id: str, memory_id: str) -> None:
        """Delete a memory (soft delete + vector removal)."""
        self._store.delete(user_id=user_id, memory_id=memory_id)

    def get(self, user_id: str, memory_id: str) -> Optional[MemoryRecord]:
        """Get a single memory by id."""
        return self._store.get(user_id=user_id, memory_id=memory_id)

    def list(
        self,
        user_id: str,
        limit: int = 100,
        include_deleted: bool = False,
    ) -> List[MemoryRecord]:
        """List memories for the user, most recent first."""
        return self._store.list(
            user_id=user_id,
            limit=limit,
            include_deleted=include_deleted,
        )

    # -------------------------------------------------------------------------
    # Search variants
    # -------------------------------------------------------------------------

    def search_semantic(
        self,
        user_id: str,
        query: str,
        k: int = 5,
        categories: Optional[List[str]] = None,
    ) -> List[SearchHit]:
        """Alias for search(); semantic (vector) search."""
        return self.search(user_id=user_id, query=query, k=k, categories=categories)

    def search_text(
        self,
        user_id: str,
        query: str,
        k: int = 5,
        categories: Optional[List[str]] = None,
    ) -> List[SearchHit]:
        """Full-text (FTS) search with optional category filter."""
        return self._store.search_text(
            user_id=user_id,
            query=query,
            k=k,
            categories=categories,
        )

    def search_hybrid(
        self,
        user_id: str,
        query: str,
        k: int = 5,
        categories: Optional[List[str]] = None,
    ) -> List[SearchHit]:
        """Hybrid semantic + text search."""
        return self._store.search_hybrid(
            user_id=user_id,
            query=query,
            k=k,
            categories=categories,
        )

    # -------------------------------------------------------------------------
    # LLM-assisted: add from conversation
    # -------------------------------------------------------------------------

    async def add_from_messages(
        self,
        user_id: str,
        messages: List[Message],
        category_hint: Optional[str] = None,
    ) -> List[MemoryChange]:
        """
        Extract facts from messages and merge into memory (add/update/delete).
        Use after a conversation turn to persist user facts.
        """
        return await self._engine.infer_and_update_from_messages(
            user_id,
            messages,
            category_hint=category_hint,
        )

    def get_context(
        self,
        user_id: str,
        query: str,
        k: int = 5,
        mode: str = "semantic",
        categories: Optional[List[str]] = None,
    ) -> str:
        """
        Return a single string of relevant memory lines for prompt injection.
        Modes: "semantic", "text", "hybrid".
        """
        if not query or not user_id:
            return ""
        if mode == "text":
            hits = self.search_text(
                user_id=user_id, query=query, k=k, categories=categories
            )
        elif mode == "hybrid":
            hits = self.search_hybrid(
                user_id=user_id, query=query, k=k, categories=categories
            )
        else:
            hits = self.search(
                user_id=user_id, query=query, k=k, categories=categories
            )
        if not hits:
            return ""
        lines = [f"- {h.memory.text}" for h in hits]
        return "Relevant user context:\n" + "\n".join(lines)


__all__ = ["MemoryClient"]
