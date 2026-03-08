"""LLM client for fact extraction and merge. Uses only eva_memory internals."""

from __future__ import annotations

import json
from typing import Any, Dict, List

from .config import LLMConfig
from .models import Message
from . import _llm


class MemoryLLMClient:
    """Calls the LLM for JSON extraction/merge. Config passed in; no dependency on src."""

    def __init__(self, config: LLMConfig | None = None) -> None:
        self._config = config or LLMConfig()

    async def chat_json(self, messages: List[Message]) -> Dict[str, Any]:
        """Call the LLM and parse a JSON object from the response."""
        text = await _llm.chat(
            messages,
            model=self._config.model,
            max_tokens=self._config.max_tokens,
            temperature=self._config.temperature,
        )
        return self._parse_json(text)

    @staticmethod
    def _parse_json(raw: str) -> Dict[str, Any]:
        """Best-effort JSON extraction from a model response."""
        raw = raw.strip()
        if not raw:
            return {}
        if raw.startswith("```"):
            raw = raw.strip("`")
            parts = raw.split("\n", 1)
            if len(parts) == 2:
                raw = parts[1]
        raw = raw.strip()
        try:
            parsed = json.loads(raw)
            if isinstance(parsed, dict):
                return parsed
            return {"data": parsed}
        except Exception:
            start = raw.find("{")
            end = raw.rfind("}")
            if start != -1 and end != -1 and end > start:
                try:
                    parsed = json.loads(raw[start : end + 1])
                    if isinstance(parsed, dict):
                        return parsed
                    return {"data": parsed}
                except Exception:
                    pass
        return {}


__all__ = ["MemoryLLMClient"]
