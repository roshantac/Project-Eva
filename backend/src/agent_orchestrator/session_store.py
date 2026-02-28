"""Session load/save to db/sessions/*.json."""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .config import SESSIONS_DIR, ensure_dirs
from .models import Message, SessionData


def _iso_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _session_path(session_id: str) -> Path:
    ensure_dirs()
    return SESSIONS_DIR / f"{session_id}.json"


def create_session(user_id: str, model: str | None = None) -> tuple[str, SessionData]:
    """Create a new session with a new UUID. Returns (session_id, SessionData)."""
    session_id = str(uuid.uuid4())
    now = _iso_now()
    metadata: dict[str, Any] = {
        "created_at": now,
        "updated_at": now,
        "user_id": user_id,
        "model": model or "llama3.2",
    }
    data = SessionData(session_id=session_id, messages=[], metadata=metadata)
    save_session(data)
    return session_id, data


def get_session(session_id: str) -> SessionData | None:
    """Load session by id; returns None if file does not exist."""
    path = _session_path(session_id)
    if not path.exists():
        return None
    with open(path) as f:
        raw = json.load(f)
    return SessionData(**raw)


def load_session(session_id: str) -> tuple[list[Message], dict[str, Any]]:
    """Load session and return (messages, metadata). Returns empty list and metadata if not found."""
    data = get_session(session_id)
    if data is None:
        return [], {"created_at": _iso_now(), "updated_at": _iso_now(), "user_id": "", "model": "llama3.2"}
    return data.to_messages(), data.metadata


def save_session(data: SessionData) -> None:
    """Persist session to db/sessions/{session_id}.json."""
    path = _session_path(data.session_id)
    meta = dict(data.metadata)
    meta["updated_at"] = _iso_now()
    if "message_count" not in meta:
        meta["message_count"] = len(data.messages)
    payload = {
        "session_id": data.session_id,
        "messages": data.messages,
        "metadata": meta,
    }
    with open(path, "w") as f:
        json.dump(payload, f, indent=2, default=str)
