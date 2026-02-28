from __future__ import annotations

from typing import Any, Tuple

from .config import DEFAULT_LLM_CORE_CONFIG, LLMCoreConfig
from .models import Message
from .providers import (
    GeminiProvider,
    LLMProvider,
    OllamaProvider,
    OpenAIProvider,
)

_provider_cache: dict[str, LLMProvider] = {}


def _get_provider_for_model(model: str | None, config: LLMCoreConfig) -> Tuple[LLMProvider, str]:
    """Resolve provider and underlying model name from a model string."""
    effective_model = model or config.model
    if ":" in effective_model:
        provider_name, raw_model = effective_model.split(":", 1)
        provider_name = provider_name.strip().lower()
        model_name = raw_model.strip() or config.model
    else:
        provider_name = "ollama"
        model_name = effective_model.strip() or config.model

    if provider_name not in _provider_cache:
        if provider_name == "openai":
            _provider_cache[provider_name] = OpenAIProvider()
        elif provider_name in ("gemini", "google"):
            _provider_cache[provider_name] = GeminiProvider()
        else:
            _provider_cache[provider_name] = OllamaProvider(default_model=model_name)

    return _provider_cache[provider_name], model_name


async def chat(
    messages: list[Message],
    *,
    model: str | None = None,
    config: LLMCoreConfig | None = None,
    **kwargs: Any,
) -> str:
    """Non-streaming chat helper for shared LLM usage."""
    cfg = config or DEFAULT_LLM_CORE_CONFIG
    provider, resolved_model = _get_provider_for_model(model, cfg)
    content, _tool_calls = await provider.chat(messages, model=resolved_model, tools=None, **kwargs)
    return content

