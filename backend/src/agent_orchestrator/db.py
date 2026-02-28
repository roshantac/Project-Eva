"""SQLite layer for history and users DBs."""

from __future__ import annotations

import json
import sqlite3
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .config import ensure_dirs, HISTORY_DB_PATH, USERS_DB_PATH


def _iso_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _conn(path: Path) -> sqlite3.Connection:
    ensure_dirs()
    conn = sqlite3.connect(str(path), check_same_thread=False)
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA synchronous=NORMAL;")
    return conn


# ---------------------------------------------------------------------------
# History DB
# ---------------------------------------------------------------------------

_HISTORY_LOCK = threading.Lock()


def _init_history(conn: sqlite3.Connection) -> None:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS history (
            session_id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            session_file_path TEXT NOT NULL,
            message_count INTEGER NOT NULL DEFAULT 0,
            model TEXT,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            metadata_json TEXT
        )
        """
    )
    conn.commit()


def upsert_history(
    session_id: str,
    user_id: str,
    session_file_path: str,
    message_count: int,
    model: str | None = None,
    metadata: dict[str, Any] | None = None,
) -> None:
    """Insert or update a history row."""
    now = _iso_now()
    meta_json = json.dumps(metadata or {}) if metadata else None
    with _HISTORY_LOCK:
        conn = _conn(HISTORY_DB_PATH)
        _init_history(conn)
        conn.execute(
            """
            INSERT INTO history (
                session_id, user_id, session_file_path, message_count, model,
                created_at, updated_at, metadata_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(session_id) DO UPDATE SET
                user_id = excluded.user_id,
                session_file_path = excluded.session_file_path,
                message_count = excluded.message_count,
                model = excluded.model,
                updated_at = excluded.updated_at,
                metadata_json = excluded.metadata_json
            """,
            (
                session_id,
                user_id,
                session_file_path,
                message_count,
                model or "",
                now,
                now,
                meta_json,
            ),
        )
        conn.commit()
        conn.close()


def get_history_by_session(session_id: str) -> dict[str, Any] | None:
    """Return one history row by session_id or None."""
    with _HISTORY_LOCK:
        conn = _conn(HISTORY_DB_PATH)
        _init_history(conn)
        row = conn.execute(
            "SELECT session_id, user_id, session_file_path, message_count, model, created_at, updated_at, metadata_json FROM history WHERE session_id = ?",
            (session_id,),
        ).fetchone()
        conn.close()
    if not row:
        return None
    return {
        "session_id": row[0],
        "user_id": row[1],
        "session_file_path": row[2],
        "message_count": row[3],
        "model": row[4],
        "created_at": row[5],
        "updated_at": row[6],
        "metadata": json.loads(row[7]) if row[7] else {},
    }


def list_history_by_user(user_id: str, limit: int = 50) -> list[dict[str, Any]]:
    """List history rows for a user, newest first."""
    with _HISTORY_LOCK:
        conn = _conn(HISTORY_DB_PATH)
        _init_history(conn)
        rows = conn.execute(
            "SELECT session_id, user_id, session_file_path, message_count, model, created_at, updated_at, metadata_json FROM history WHERE user_id = ? ORDER BY updated_at DESC LIMIT ?",
            (user_id, limit),
        ).fetchall()
        conn.close()
    return [
        {
            "session_id": r[0],
            "user_id": r[1],
            "session_file_path": r[2],
            "message_count": r[3],
            "model": r[4],
            "created_at": r[5],
            "updated_at": r[6],
            "metadata": json.loads(r[7]) if r[7] else {},
        }
        for r in rows
    ]


# ---------------------------------------------------------------------------
# Users DB
# ---------------------------------------------------------------------------

_USERS_LOCK = threading.Lock()


def _init_users(conn: sqlite3.Connection) -> None:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            user_id TEXT PRIMARY KEY,
            metadata_json TEXT,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
        """
    )
    conn.commit()


def upsert_user(user_id: str, metadata: dict[str, Any] | None = None) -> None:
    """Insert or update a user row."""
    now = _iso_now()
    meta_json = json.dumps(metadata or {}) if metadata else None
    with _USERS_LOCK:
        conn = _conn(USERS_DB_PATH)
        _init_users(conn)
        conn.execute(
            """
            INSERT INTO users (user_id, metadata_json, created_at, updated_at)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(user_id) DO UPDATE SET
                metadata_json = excluded.metadata_json,
                updated_at = excluded.updated_at
            """,
            (user_id, meta_json, now, now),
        )
        conn.commit()
        conn.close()


def get_user(user_id: str) -> dict[str, Any] | None:
    """Return one user row or None."""
    with _USERS_LOCK:
        conn = _conn(USERS_DB_PATH)
        _init_users(conn)
        row = conn.execute(
            "SELECT user_id, metadata_json, created_at, updated_at FROM users WHERE user_id = ?",
            (user_id,),
        ).fetchone()
        conn.close()
    if not row:
        return None
    return {
        "user_id": row[0],
        "metadata": json.loads(row[1]) if row[1] else {},
        "created_at": row[2],
        "updated_at": row[3],
    }
