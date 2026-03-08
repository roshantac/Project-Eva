"""Ollama embedding backend (e.g. nomic-embed-text)."""

from __future__ import annotations

from typing import Literal, Optional

from ollama import Client

from .base import EmbeddingBase


class OllamaEmbedding(EmbeddingBase):
    """Embedding via local Ollama server (e.g. nomic-embed-text)."""

    def __init__(
        self,
        model: str = "nomic-embed-text:latest",
        base_url: str = "http://localhost:11434",
    ) -> None:
        self.model = model or "nomic-embed-text:latest"
        self.base_url = base_url or "http://localhost:11434"
        self.client = Client(host=self.base_url)

    def embed(
        self,
        text: str,
        memory_action: Optional[Literal["add", "search", "update"]] = None,
    ) -> list[float]:
        response = self.client.embeddings(model=self.model, prompt=text)
        return response["embedding"]
