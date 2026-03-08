"""App-level dependencies (e.g. memory client) built from project config."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

try:
    from main_config import MEMORY_DIR as _MEMORY_DIR_STR
    _MEMORY_DIR = Path(_MEMORY_DIR_STR)
except ImportError:
    _MEMORY_DIR = Path(__file__).resolve().parent.parent / "db" / "memory"

_memory_client: Optional["MemoryClient"] = None


def get_memory_client() -> Optional["MemoryClient"]:
    """Return a MemoryClient configured from main_config (or default paths). Lazy singleton."""
    global _memory_client
    if _memory_client is not None:
        return _memory_client
    try:
        from src.eva_memory import EvaMemoryConfig, MemoryClient
        config = EvaMemoryConfig(
            sqlite_path=_MEMORY_DIR / "sqlite" / "memories.db",
            faiss_dir=_MEMORY_DIR / "faiss",
        )
        _memory_client = MemoryClient(config=config)
        return _memory_client
    except Exception:
        return None


async def add_turn_background(
    user_id: str,
    user_message: str,
    assistant_message: str,
    category_hint: Optional[str] = None,
) -> None:
    """Add the last turn to memory (LLM-assisted). No-op if memory client unavailable."""
    client = get_memory_client()
    if client is None:
        return
    from src.eva_memory import Message
    messages = [
        Message(role="user", content=user_message or ""),
        Message(role="assistant", content=assistant_message or ""),
    ]
    try:
        await client.add_from_messages(
            user_id=user_id,
            messages=messages,
            category_hint=category_hint,
        )
    except Exception:
        pass


def get_context_sync(
    user_id: str,
    query: str,
    k: int = 5,
    mode: str = "semantic",
    categories: Optional[list] = None,
) -> str:
    """Return memory context string for prompt. Empty if client unavailable."""
    client = get_memory_client()
    if client is None:
        return ""
    return client.get_context(
        user_id=user_id,
        query=query,
        k=k,
        mode=mode,
        categories=categories,
    )
