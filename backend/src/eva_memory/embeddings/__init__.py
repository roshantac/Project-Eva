"""Embedding backends: Ollama (nomic) and OpenAI. Configurable via EmbeddingConfig."""

from __future__ import annotations

from typing import TYPE_CHECKING

from .base import EmbeddingBase

if TYPE_CHECKING:
    from ..config import EmbeddingConfig

from .ollama import OllamaEmbedding
from .openai_embedding import OpenAIEmbedding


def get_embedder(config: "EmbeddingConfig") -> EmbeddingBase:
    """
    Return an embedder from EmbeddingConfig.
    config.model format: 'provider:model', e.g. ollama:nomic-embed-text:latest, openai:text-embedding-3-small.
    """
    raw = (config.model or "").strip()
    if ":" in raw:
        provider, model = raw.split(":", 1)
        provider = provider.strip().lower()
        model = model.strip() or raw
    else:
        provider = "ollama"
        model = raw or "nomic-embed-text:latest"

    base_url = config.base_url or "http://localhost:11434"

    if provider == "ollama":
        return OllamaEmbedding(model=model, base_url=base_url)
    if provider == "openai":
        return OpenAIEmbedding(model=model)
    raise ValueError(
        f"Unknown embedding provider: {provider}. Use ollama:model or openai:model."
    )


__all__ = [
    "EmbeddingBase",
    "OllamaEmbedding",
    "OpenAIEmbedding",
    "get_embedder",
]
