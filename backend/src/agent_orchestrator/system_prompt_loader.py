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

    Includes the base prompt from disk plus all skills' frontmatter (text between ---)
    so the agent has skill names and descriptions by default.
    If the prompt file does not exist or cannot be read, returns an empty string.
    """
    global _cached_prompt
    if _cached_prompt is None:
        base = _read_file(DEFAULT_SYSTEM_PROMPT_PATH)
        from .builtin_tools import get_all_skills_frontmatter

        frontmatter = get_all_skills_frontmatter()
        if base and frontmatter:
            _cached_prompt = base.rstrip() + "\n\n## Available skills (metadata)\n\n" + frontmatter
        elif frontmatter:
            _cached_prompt = "## Available skills (metadata)\n\n" + frontmatter
        else:
            _cached_prompt = base or ""
    return _cached_prompt or ""

