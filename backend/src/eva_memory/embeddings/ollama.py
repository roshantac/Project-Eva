from __future__ import annotations

from typing import Literal, Optional

from ollama import Client

from ..config import OllamaConfig
from .base import EmbeddingBase


class OllamaEmbedding(EmbeddingBase):
    """Embedding backend that uses a local Ollama server.

    - Uses a dedicated `OllamaConfig`.
    - Removes any interactive installation logic.
    - Defaults the model to `nomic-embed-text:latest`.
    """

    def __init__(self, config: Optional[OllamaConfig] = None) -> None:
        super().__init__(config)

        # Ensure sensible defaults
        if not self.config.model:
            self.config.model = "nomic-embed-text:latest"

        self.client = Client(host=self.config.base_url)

    def embed(
        self,
        text: str,
        memory_action: Optional[Literal["add", "search", "update"]] = None,
    ) -> list[float]:
        """Return an embedding vector for the given text."""
        response = self.client.embeddings(model=self.config.model, prompt=text)
        return response["embedding"]

