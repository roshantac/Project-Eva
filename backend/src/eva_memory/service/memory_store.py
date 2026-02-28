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

    def search(
        self,
        user_id: str,
        query: str,
        k: int = 5,
        categories: Optional[List[str]] = None,
    ) -> List[SearchHit]:
        """Semantic (vector) search. Optionally filter by metadata category."""
        if not query:
            return []

        vector = self._embedder.embed(query, memory_action="search")
        fetch_k = k * 3 if categories else k
        hits = self._faiss.search(user_id=user_id, vector=vector, k=fetch_k)
        if not hits:
            return []

        faiss_ids = [fid for fid, _ in hits]
        rows_by_id = self._metadata.get_by_faiss_ids(user_id=user_id, faiss_ids=faiss_ids)

        results: List[SearchHit] = []
        for fid, score in hits:
            row = rows_by_id.get(fid)
            if row is None:
                continue
            record = self._to_record(row)
            if categories:
                cat = (record.metadata or {}).get("category")
                if cat not in categories:
                    continue
            results.append(SearchHit(memory=record, score=score))
            if len(results) >= k:
                break
        return results

    def search_semantic(
        self,
        user_id: str,
        query: str,
        k: int = 5,
        categories: Optional[List[str]] = None,
    ) -> List[SearchHit]:
        """Alias for search(); semantic (vector) search with optional category filter."""
        return self.search(user_id=user_id, query=query, k=k, categories=categories)

    def search_text(
        self,
        user_id: str,
        query: str,
        k: int = 5,
        categories: Optional[List[str]] = None,
    ) -> List[SearchHit]:
        """Full-text (FTS5/BM25) search with optional category filter."""
        if not query:
            return []
        raw = self._metadata.search_text(user_id=user_id, query=query, limit=k * 3 if categories else k)
        results: List[SearchHit] = []
        for row, score in raw:
            record = self._to_record(row)
            if categories:
                cat = (record.metadata or {}).get("category")
                if cat not in categories:
                    continue
            results.append(SearchHit(memory=record, score=score))
            if len(results) >= k:
                break
        return results

    def search_hybrid(
        self,
        user_id: str,
        query: str,
        k: int = 5,
        categories: Optional[List[str]] = None,
    ) -> List[SearchHit]:
        """Combine semantic and text search; normalize scores and merge (0.6 semantic + 0.4 text)."""
        if not query:
            return []
        k_fetch = max(k * 2, 10)
        sem_hits = self.search_semantic(user_id=user_id, query=query, k=k_fetch, categories=categories)
        txt_hits = self.search_text(user_id=user_id, query=query, k=k_fetch, categories=categories)

        sem_scores = {h.memory.memory_id: h.score for h in sem_hits}
        txt_scores = {h.memory.memory_id: h.score for h in txt_hits}
        all_ids = set(sem_scores) | set(txt_scores)

        def norm(vals: List[float]) -> tuple[float, float]:
            if not vals:
                return 0.0, 1.0
            lo, hi = min(vals), max(vals)
            span = hi - lo if hi > lo else 1.0
            return lo, span

        sem_lo, sem_span = norm(list(sem_scores.values()))
        txt_lo, txt_span = norm(list(txt_scores.values()))

        combined: List[tuple[str, float, MemoryRecord]] = []
        for mid in all_ids:
            s = sem_scores.get(mid)
            t = txt_scores.get(mid)
            ns = (s - sem_lo) / sem_span if sem_span else 0.0
            nt = (t - txt_lo) / txt_span if txt_span else 0.0
            comb = 0.6 * ns + 0.4 * nt
            record = next((h.memory for h in sem_hits + txt_hits if h.memory.memory_id == mid), None)
            if record:
                combined.append((mid, comb, record))
        combined.sort(key=lambda x: -x[1])
        return [SearchHit(memory=r, score=score) for _, score, r in combined[:k]]

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

