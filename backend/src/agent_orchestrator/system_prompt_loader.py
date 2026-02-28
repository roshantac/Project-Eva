"""Utilities for loading the default system prompt from disk."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from .config import DEFAULT_SYSTEM_PROMPT_PATH

_cached_prompt: Optional[str] = None


def _read_file(path: Path) -> str:
    try:
        text = path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return ""
    except OSError:
        return ""
    return text.strip()


def get_default_system_prompt() -> str:
    """Return the default system prompt text, cached after first read.

    If the prompt file does not exist or cannot be read, returns an empty string.
    """
    global _cached_prompt
    if _cached_prompt is None:
        _cached_prompt = _read_file(DEFAULT_SYSTEM_PROMPT_PATH)
    return _cached_prompt or ""

