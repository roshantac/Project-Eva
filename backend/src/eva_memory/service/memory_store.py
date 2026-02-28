from __future__ import annotations

from typing import Any, Dict, List, Optional

from ..config import MemoryStoreConfig
from ..embeddings.ollama import OllamaEmbedding
from ..models import MemoryRecord, SearchHit
from ..persistence.sqlite import SQLiteMetadataStore
from ..vector_stores.faiss_store import FaissStore


class MemoryStore:
    """High-level service that orchestrates embeddings, SQLite, and FAISS.

    This implements a simple user-scoped memory store with:
    - add
    - update
    - delete (soft delete in SQLite + vector removal in FAISS)
    - get
    - list
    - search
    """

    def __init__(self, config: Optional[MemoryStoreConfig] = None) -> None:
        self.config = config or MemoryStoreConfig()
        self.config.ensure_directories()

        self._embedder = OllamaEmbedding(self.config.ollama)
        self._metadata = SQLiteMetadataStore(self.config.sqlite_path)
        self._faiss = FaissStore(self.config.faiss_dir)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def add(self, user_id: str, text: str, metadata: Optional[Dict[str, Any]] = None) -> MemoryRecord:
        """Add a new memory for a user."""
        if not user_id:
            raise ValueError("user_id is required")
        if not text:
            raise ValueError("text is required")

        vector = self._embedder.embed(text, memory_action="add")
        faiss_id = self._metadata.allocate_faiss_id(user_id)
        self._faiss.add(user_id=user_id, faiss_id=faiss_id, vector=vector)

        row = self._metadata.insert_memory(
            user_id=user_id,
            text=text,
            metadata=metadata,
            faiss_id=faiss_id,
        )
        return self._to_record(row)

    def update(
        self,
        user_id: str,
        memory_id: str,
        new_text: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> MemoryRecord:
        """Update the text (and optional metadata) of an existing memory."""
        existing = self._metadata.get_memory(user_id=user_id, memory_id=memory_id)
        if existing is None or existing.is_deleted:
            raise ValueError("Memory not found or has been deleted")

        vector = self._embedder.embed(new_text, memory_action="update")
        self._faiss.update(user_id=user_id, faiss_id=existing.faiss_id, vector=vector)

        updated = self._metadata.update_memory(
            user_id=user_id,
            memory_id=memory_id,
            text=new_text,
            metadata=metadata,
        )
        if updated is None:
            raise ValueError("Failed to update memory")
        return self._to_record(updated)

    def delete(self, user_id: str, memory_id: str) -> None:
        """Soft-delete a memory and remove its vector from FAISS."""
        existing = self._metadata.get_memory(user_id=user_id, memory_id=memory_id)
        if existing is None or existing.is_deleted:
            return

        self._faiss.delete(user_id=user_id, faiss_id=existing.faiss_id)
        self._metadata.mark_deleted(user_id=user_id, memory_id=memory_id)

    def get(self, user_id: str, memory_id: str) -> Optional[MemoryRecord]:
        row = self._metadata.get_memory(user_id=user_id, memory_id=memory_id)
        return self._to_record(row) if row is not None else None

    def list(
        self,
        user_id: str,
        limit: int = 100,
        include_deleted: bool = False,
    ) -> List[MemoryRecord]:
        rows = self._metadata.list_memories(
            user_id=user_id,
            limit=limit,
            include_deleted=include_deleted,
        )
        return [self._to_record(r) for r in rows]

    def search(self, user_id: str, query: str, k: int = 5) -> List[SearchHit]:
        if not query:
            return []

        vector = self._embedder.embed(query, memory_action="search")
        hits = self._faiss.search(user_id=user_id, vector=vector, k=k)
        if not hits:
            return []

        faiss_ids = [fid for fid, _ in hits]
        rows_by_id = self._metadata.get_by_faiss_ids(user_id=user_id, faiss_ids=faiss_ids)

        results: List[SearchHit] = []
        for fid, score in hits:
            row = rows_by_id.get(fid)
            if row is None:
                continue
            results.append(
                SearchHit(
                    memory=self._to_record(row),
                    score=score,
                )
            )
        return results

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _to_record(row) -> MemoryRecord:
        return MemoryRecord(
            memory_id=row.memory_id,
            user_id=row.user_id,
            text=row.text,
            metadata=row.metadata,
            created_at=row.created_at,
            updated_at=row.updated_at,
            is_deleted=row.is_deleted,
        )

