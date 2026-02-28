"""Orchestrator configuration: paths and defaults."""

from __future__ import annotations

from pathlib import Path

from main_config import (
    DB_DIR as _DB_DIR,
    DEFAULT_SYSTEM_PROMPT_PATH as _DEFAULT_SYSTEM_PROMPT_PATH,
    HISTORY_DB_PATH as _HISTORY_DB_PATH,
    SESSIONS_DIR as _SESSIONS_DIR,
    USERS_DB_PATH as _USERS_DB_PATH,
    USER_DIR as _USER_DIR,
)

# Path objects for use in this package (main_config uses os.path strings)
DB_DIR = Path(_DB_DIR)
USER_DIR = Path(_USER_DIR)
SESSIONS_DIR = Path(_SESSIONS_DIR)
HISTORY_DB_PATH = Path(_HISTORY_DB_PATH)
USERS_DB_PATH = Path(_USERS_DB_PATH)
DEFAULT_SYSTEM_PROMPT_PATH = Path(_DEFAULT_SYSTEM_PROMPT_PATH)

DEFAULT_MODEL = "gpt-4.1-nano"
DEFAULT_CONTEXT_WINDOW = 128000
CONTEXT_SUMMARY_THRESHOLD = 0.8
DEFAULT_MAX_TOOL_ITERATIONS = 10


def ensure_dirs() -> None:
    """Create db, user, and sessions directories if they do not exist."""
    DB_DIR.mkdir(parents=True, exist_ok=True)
    USER_DIR.mkdir(parents=True, exist_ok=True)
    SESSIONS_DIR.mkdir(parents=True, exist_ok=True)
