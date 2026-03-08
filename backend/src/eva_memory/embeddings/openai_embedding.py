"""OpenAI embedding backend (e.g. text-embedding-3-small). API key from OPENAI_API_KEY env."""

from __future__ import annotations

import os
from typing import Literal, Optional

try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass

from .base import EmbeddingBase


class OpenAIEmbedding(EmbeddingBase):
    """Embedding via OpenAI API. Uses OPENAI_API_KEY from env."""

    def __init__(
        self,
        model: str = "text-embedding-3-small",
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
    ) -> None:
        self.model = model or "text-embedding-3-small"
        self._api_key = api_key or os.getenv("OPENAI_API_KEY") or ""
        self._base_url = base_url or os.getenv("OPENAI_BASE_URL")

    def _get_client(self):
        try:
            from openai import OpenAI
        except ImportError as e:
            raise RuntimeError(
                "openai package is not installed. pip install openai"
            ) from e
        kwargs: dict = {"api_key": self._api_key}
        if self._base_url:
            kwargs["base_url"] = self._base_url
        return OpenAI(**kwargs)

    def embed(
        self,
        text: str,
        memory_action: Optional[Literal["add", "search", "update"]] = None,
    ) -> list[float]:
        client = self._get_client()
        resp = client.embeddings.create(input=text, model=self.model)
        return resp.data[0].embedding
