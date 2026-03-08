"""Configuration for the EVA Memory package. Pass when creating the client."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from pydantic import BaseModel, Field


class EmbeddingConfig(BaseModel):
    """
    Configuration for embeddings. Provider and model; API key from env.

    Use model string 'provider:model', e.g.:
    - ollama:nomic-embed-text:latest
    - openai:text-embedding-3-small
    API keys: OPENAI_API_KEY for openai (from env).
    """

    model: str = Field(
        default="ollama:nomic-embed-text:latest",
        description="Provider and model, e.g. ollama:nomic-embed-text:latest, openai:text-embedding-3-small",
    )
    base_url: Optional[str] = Field(
        default=None,
        description="Base URL for Ollama (default http://localhost:11434). Ignored for openai.",
    )


class LLMConfig(BaseModel):
    """Configuration for the LLM used for fact extraction and merge decisions."""

    model: str = Field(
        default="openai:gpt-4.1-mini",
        description="Model string: 'provider:model', e.g. openai:gpt-4.1-mini, ollama:llama3, gemini:gemini-2.5-flash",
    )
    max_tokens: Optional[int] = Field(default=None, description="Max tokens for LLM responses.")
    temperature: float = Field(default=0.2, description="Sampling temperature.")


class EvaMemoryConfig(BaseModel):
    """Top-level configuration for EVA Memory. Declare this when creating the client."""

    sqlite_path: Path = Field(
        ...,
        description="Path to the SQLite database file for memory metadata.",
    )
    faiss_dir: Path = Field(
        ...,
        description="Directory where FAISS index files are stored.",
    )
    embedding: EmbeddingConfig = Field(
        default_factory=EmbeddingConfig,
        description="Embedding provider and model (e.g. ollama:nomic-embed-text:latest, openai:text-embedding-3-small).",
    )
    llm: LLMConfig = Field(
        default_factory=LLMConfig,
        description="LLM settings for fact extraction and merge.",
    )

    def ensure_directories(self) -> None:
        """Create required directories if they do not exist."""
        self.sqlite_path.parent.mkdir(parents=True, exist_ok=True)
        self.faiss_dir.mkdir(parents=True, exist_ok=True)


# ---------------------------------------------------------------------------
# Internal: store config and legacy alias
# ---------------------------------------------------------------------------

class MemoryStoreConfig(BaseModel):
    """Internal store config (paths + embedding). Built from EvaMemoryConfig."""

    embedding: EmbeddingConfig = Field(default_factory=EmbeddingConfig)
    sqlite_path: Path = Field(...)
    faiss_dir: Path = Field(...)

    def ensure_directories(self) -> None:
        self.sqlite_path.parent.mkdir(parents=True, exist_ok=True)
        self.faiss_dir.mkdir(parents=True, exist_ok=True)


# Legacy alias for code that still references OllamaEmbeddingConfig
class OllamaEmbeddingConfig(BaseModel):
    """Legacy: use EmbeddingConfig with model='ollama:nomic-embed-text:latest'."""

    model: str = Field(default="nomic-embed-text:latest")
    base_url: str = Field(default="http://localhost:11434")


OllamaConfig = OllamaEmbeddingConfig


__all__ = [
    "EvaMemoryConfig",
    "EmbeddingConfig",
    "LLMConfig",
    "MemoryStoreConfig",
    "OllamaEmbeddingConfig",
    "OllamaConfig",
]
