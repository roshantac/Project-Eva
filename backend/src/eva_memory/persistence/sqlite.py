from __future__ import annotations

import json
import sqlite3
import threading
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional


@dataclass
class MemoryRow:
    memory_id: str
    user_id: str
    text: str
    metadata: Optional[Dict[str, Any]]
    faiss_id: int
    created_at: str
    updated_at: Optional[str]
    is_deleted: bool


class SQLiteMetadataStore:
    """SQLite-backed metadata store for memories.

    Tailored for a single `memories` table that is the source of truth for:
    - memory_id (UUID string)
    - user_id (string)
    - raw text
    - optional metadata JSON
    - faiss_id (integer id used in FAISS)
    """

    def __init__(self, db_path: Path) -> None:
        self.db_path = str(db_path)
        db_path.parent.mkdir(parents=True, exist_ok=True)

        self._lock = threading.Lock()
        self._conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self._conn.execute("PRAGMA journal_mode=WAL;")
        self._conn.execute("PRAGMA synchronous=NORMAL;")
        self._create_schema()

    def _create_schema(self) -> None:
        with self._lock:
            cur = self._conn.cursor()
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS memories (
                    memory_id    TEXT PRIMARY KEY,
                    user_id      TEXT NOT NULL,
                    text         TEXT NOT NULL,
                    metadata_json TEXT,
                    faiss_id     INTEGER NOT NULL UNIQUE,
                    created_at   TEXT NOT NULL,
                    updated_at   TEXT,
                    is_deleted   INTEGER NOT NULL DEFAULT 0
                )
                """
            )
            cur.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_memories_user_id
                ON memories (user_id)
                """
            )
            cur.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_memories_user_id_deleted
                ON memories (user_id, is_deleted)
                """
            )
            cur.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_memories_faiss_id
                ON memories (faiss_id)
                """
            )
            self._conn.commit()

    def _row_to_memory(self, row: sqlite3.Row) -> MemoryRow:
        metadata = json.loads(row["metadata_json"]) if row["metadata_json"] is not None else None
        return MemoryRow(
            memory_id=row["memory_id"],
            user_id=row["user_id"],
            text=row["text"],
            metadata=metadata,
            faiss_id=row["faiss_id"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
            is_deleted=bool(row["is_deleted"]),
        )

    def allocate_faiss_id(self, user_id: str) -> int:
        """Allocate the next FAISS id globally (unique across all users) to satisfy UNIQUE(faiss_id)."""
        with self._lock:
            self._conn.row_factory = None
            cur = self._conn.cursor()
            cur.execute("SELECT COALESCE(MAX(faiss_id), 0) FROM memories")
            (max_id,) = cur.fetchone()
            next_id = int(max_id) + 1
            return next_id

    def insert_memory(
        self,
        user_id: str,
        text: str,
        metadata: Optional[Dict[str, Any]],
        faiss_id: int,
    ) -> MemoryRow:
        now = datetime.now(timezone.utc).isoformat()
        memory_id = str(uuid.uuid4())
        metadata_json = json.dumps(metadata) if metadata is not None else None

        with self._lock:
            self._conn.row_factory = sqlite3.Row
            cur = self._conn.cursor()
            cur.execute(
                """
                INSERT INTO memories (
                    memory_id, user_id, text, metadata_json,
                    faiss_id, created_at, updated_at, is_deleted
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, 0)
                """,
                (memory_id, user_id, text, metadata_json, faiss_id, now, None),
            )
            self._conn.commit()

            cur.execute(
                "SELECT * FROM memories WHERE memory_id = ?",
                (memory_id,),
            )
            row = cur.fetchone()
            return self._row_to_memory(row)

    def update_memory(
        self,
        user_id: str,
        memory_id: str,
        text: str,
        metadata: Optional[Dict[str, Any]],
    ) -> Optional[MemoryRow]:
        now = datetime.now(timezone.utc).isoformat()
        metadata_json = json.dumps(metadata) if metadata is not None else None

        with self._lock:
            self._conn.row_factory = sqlite3.Row
            cur = self._conn.cursor()
            cur.execute(
                """
                UPDATE memories
                SET text = ?, metadata_json = ?, updated_at = ?
                WHERE memory_id = ? AND user_id = ? AND is_deleted = 0
                """,
                (text, metadata_json, now, memory_id, user_id),
            )
            if cur.rowcount == 0:
                self._conn.commit()
                return None

            self._conn.commit()
            cur.execute(
                "SELECT * FROM memories WHERE memory_id = ?",
                (memory_id,),
            )
            row = cur.fetchone()
            return self._row_to_memory(row)

    def mark_deleted(self, user_id: str, memory_id: str) -> Optional[MemoryRow]:
        with self._lock:
            self._conn.row_factory = sqlite3.Row
            cur = self._conn.cursor()
            cur.execute(
                """
                UPDATE memories
                SET is_deleted = 1, updated_at = ?
                WHERE memory_id = ? AND user_id = ? AND is_deleted = 0
                """,
                (datetime.now(timezone.utc).isoformat(), memory_id, user_id),
            )
            if cur.rowcount == 0:
                self._conn.commit()
                return None

            self._conn.commit()
            cur.execute(
                "SELECT * FROM memories WHERE memory_id = ?",
                (memory_id,),
            )
            row = cur.fetchone()
            return self._row_to_memory(row)

    def get_memory(self, user_id: str, memory_id: str) -> Optional[MemoryRow]:
        with self._lock:
            self._conn.row_factory = sqlite3.Row
            cur = self._conn.cursor()
            cur.execute(
                """
                SELECT * FROM memories
                WHERE memory_id = ? AND user_id = ?
                """,
                (memory_id, user_id),
            )
            row = cur.fetchone()
            return self._row_to_memory(row) if row else None

    def list_memories(
        self,
        user_id: str,
        limit: int = 100,
        include_deleted: bool = False,
    ) -> List[MemoryRow]:
        with self._lock:
            self._conn.row_factory = sqlite3.Row
            cur = self._conn.cursor()
            if include_deleted:
                cur.execute(
                    """
                    SELECT * FROM memories
                    WHERE user_id = ?
                    ORDER BY created_at DESC
                    LIMIT ?
                    """,
                    (user_id, limit),
                )
            else:
                cur.execute(
                    """
                    SELECT * FROM memories
                    WHERE user_id = ? AND is_deleted = 0
                    ORDER BY created_at DESC
                    LIMIT ?
                    """,
                    (user_id, limit),
                )
            rows = cur.fetchall()
            return [self._row_to_memory(r) for r in rows]

    def get_by_faiss_ids(
        self,
        user_id: str,
        faiss_ids: Iterable[int],
    ) -> Dict[int, MemoryRow]:
        ids = list(faiss_ids)
        if not ids:
            return {}

        placeholders = ",".join("?" for _ in ids)
        params: List[Any] = [user_id, *ids]

        with self._lock:
            self._conn.row_factory = sqlite3.Row
            cur = self._conn.cursor()
            cur.execute(
                f"""
                SELECT * FROM memories
                WHERE user_id = ? AND faiss_id IN ({placeholders}) AND is_deleted = 0
                """,
                params,
            )
            rows = cur.fetchall()
            return {row["faiss_id"]: self._row_to_memory(row) for row in rows}

    def close(self) -> None:
        with self._lock:
            if self._conn:
                self._conn.close()
                self._conn = None

    def __del__(self) -> None:
        self.close()

