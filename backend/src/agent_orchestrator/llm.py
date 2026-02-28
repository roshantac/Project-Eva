"""LLM facade: default provider and convenience functions for the orchestrator."""

from __future__ import annotations

from collections.abc import AsyncIterator
from typing import Any, Tuple

from .config import DEFAULT_MODEL
from .models import Message
from .providers import (
    LLMProvider,
    OllamaProvider,
    OpenAIProvider,
    GeminiProvider,
    StreamChunk,
)

_default_provider: LLMProvider | None = None
_provider_cache: dict[str, LLMProvider] = {}


def get_default_provider() -> LLMProvider:
    """Return the default LLM provider (Ollama)."""
    global _default_provider
    if _default_provider is None:
        _default_provider = OllamaProvider(default_model=DEFAULT_MODEL)
    return _default_provider


def set_default_provider(provider: LLMProvider) -> None:
    """Set the default LLM provider (used when no model hint is given)."""
    global _default_provider
    _default_provider = provider


def _get_provider_for_model(model: str | None) -> Tuple[LLMProvider, str]:
    """
    Resolve provider and underlying model name from a model string.

    Expected formats:
    - "provider:model_name" (e.g. "openai:gpt-5.1-nano", "gemini:gemini-2.5-flash")
    - "model_name" (no colon) → treated as an Ollama model.
    """
    if not model:
        # Fallback to default configuration (Ollama + DEFAULT_MODEL)
        provider = _provider_cache.get("ollama")
        if provider is None:
            provider = OllamaProvider(default_model=DEFAULT_MODEL)
            _provider_cache["ollama"] = provider
        return provider, DEFAULT_MODEL

    if ":" in model:
        provider_name, raw_model = model.split(":", 1)
        provider_name = provider_name.strip().lower()
        model_name = raw_model.strip() or DEFAULT_MODEL
    else:
        provider_name = "ollama"
        model_name = model.strip() or DEFAULT_MODEL

    if provider_name not in _provider_cache:
        if provider_name == "openai":
            _provider_cache[provider_name] = OpenAIProvider()
        elif provider_name in ("gemini", "google"):
            _provider_cache[provider_name] = GeminiProvider()
        else:
            # Unknown / fallback → Ollama
            _provider_cache[provider_name] = OllamaProvider(default_model=DEFAULT_MODEL)

    return _provider_cache[provider_name], model_name


async def chat(
    messages: list[Message],
    model: str | None = None,
    tools: list[dict[str, Any]] | None = None,
    provider: LLMProvider | None = None,
    **kwargs: Any,
) -> tuple[str, list[dict[str, Any]]]:
    """Non-streaming chat. Uses explicit provider if given, otherwise infers from model."""
    if provider is not None:
        return await provider.chat(messages, model=model, tools=tools, **kwargs)
    p, resolved_model = _get_provider_for_model(model)
    return await p.chat(messages, model=resolved_model, tools=tools, **kwargs)


async def stream_chat(
    messages: list[Message],
    model: str | None = None,
    tools: list[dict[str, Any]] | None = None,
    provider: LLMProvider | None = None,
    **kwargs: Any,
) -> AsyncIterator[StreamChunk]:
    """Stream chat. Uses explicit provider if given, otherwise infers from model."""
    if provider is not None:
        async for chunk in provider.stream_chat(
            messages, model=model, tools=tools, **kwargs
        ):
            yield chunk
        return

    p, resolved_model = _get_provider_for_model(model)
    async for chunk in p.stream_chat(
        messages, model=resolved_model, tools=tools, **kwargs
    ):
        yield chunk
