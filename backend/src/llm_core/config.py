from __future__ import annotations

from dataclasses import dataclass


@dataclass
class LLMCoreConfig:
    """Configuration for shared LLM usage."""

    model: str = "openai:gpt-4.1-nano"


DEFAULT_LLM_CORE_CONFIG = LLMCoreConfig()

