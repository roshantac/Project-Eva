from __future__ import annotations

from pathlib import Path
from typing import Optional

from pydantic import BaseModel, Field

# Align with main_config: memory data under BASE_DIR/db/memory/
try:
    from main_config import MEMORY_DIR as _MEMORY_DIR_STR

    BASE_MEMORY_DIR = Path(_MEMORY_DIR_STR)
except ImportError:
    # Fallback: backend/db/memory relative to this file
    BASE_MEMORY_DIR = (
        Path(__file__).resolve().parent.parent.parent / "db" / "memory"
    )

FAISS_DIR = BASE_MEMORY_DIR / "faiss"
SQLITE_DIR = BASE_MEMORY_DIR / "sqlite"
SQLITE_PATH = SQLITE_DIR / "memories.db"


class OllamaConfig(BaseModel):
    """Configuration for the Ollama embedding backend."""

    model: str = Field(
        default="nomic-embed-text:latest",
        description="Embedding model name served by Ollama.",
    )
    base_url: str = Field(
        default="http://localhost:11434",
        description="Base URL for the local Ollama server.",
    )


class MemoryStoreConfig(BaseModel):
    """Top-level configuration for the memory store."""

    ollama: OllamaConfig = Field(default_factory=OllamaConfig)
    sqlite_path: Path = Field(
        default=SQLITE_PATH,
        description="Path to the SQLite database file for memory metadata.",
    )
    faiss_dir: Path = Field(
        default=FAISS_DIR,
        description="Directory where FAISS index files are stored.",
    )

    def ensure_directories(self) -> None:
        """Create required directories if they do not exist."""
        self.sqlite_path.parent.mkdir(parents=True, exist_ok=True)
        self.faiss_dir.mkdir(parents=True, exist_ok=True)

