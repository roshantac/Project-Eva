from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Dict, List

from src.llm_core import LLMCoreConfig, Message, chat as llm_chat


@dataclass
class MemoryLLMConfig:
    """Configuration for EVA memory LLM usage."""

    model: str = "openai:gpt-4.1-mini"
    max_tokens: int | None = None
    temperature: float = 0.2

    def to_core_config(self) -> LLMCoreConfig:
        return LLMCoreConfig(model=self.model)


class MemoryLLMClient:
    """Thin wrapper around the shared LLM core for eva_memory."""

    def __init__(self, config: MemoryLLMConfig | None = None) -> None:
        self._config = config or MemoryLLMConfig()

    async def chat_json(self, messages: List[Message]) -> Dict[str, Any]:
        """Call the LLM and parse a JSON object from the response."""
        extra: Dict[str, Any] = {}
        if self._config.max_tokens is not None:
            extra["max_tokens"] = self._config.max_tokens
        if self._config.temperature is not None:
            extra["temperature"] = self._config.temperature

        text = await llm_chat(
            messages,
            model=self._config.model,
            config=self._config.to_core_config(),
            **extra,
        )
        return self._parse_json(text)

    @staticmethod
    def _parse_json(raw: str) -> Dict[str, Any]:
        """Best-effort JSON extraction from a model response."""
        raw = raw.strip()
        if not raw:
            return {}
        # Remove common markdown code fences
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
            # Fallback: attempt to locate the first and last JSON braces
            start = raw.find("{")
            end = raw.rfind("}")
            if start != -1 and end != -1 and end > start:
                snippet = raw[start : end + 1]
                try:
                    parsed = json.loads(snippet)
                    if isinstance(parsed, dict):
                        return parsed
                    return {"data": parsed}
                except Exception:
                    pass
        return {}


__all__ = ["MemoryLLMConfig", "MemoryLLMClient"]

