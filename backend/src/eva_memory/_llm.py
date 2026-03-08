"""Standalone LLM chat for eva_memory. No dependency on src.llm_core."""

from __future__ import annotations

import os
from typing import Any, List, Optional

from .models import Message

try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass


def _resolve_provider(model: str) -> tuple[str, str]:
    """Return (provider_name, model_name). Provider: openai, ollama, gemini."""
    model = (model or "").strip()
    if ":" in model:
        provider, name = model.split(":", 1)
        return provider.strip().lower(), name.strip() or model
    return "ollama", model or "llama3.2"


async def _chat_ollama(messages: List[Message], model: str, **kwargs: Any) -> str:
    from ollama import AsyncClient
    client = AsyncClient(host=kwargs.get("base_url") or "http://localhost:11434")
    try:
        chat_list = [{"role": m.role, "content": m.content or ""} for m in messages]
        stream = await client.chat(model=model, messages=chat_list, stream=True)
        parts: List[str] = []
        async for chunk in stream:
            msg = getattr(chunk, "message", None)
            if msg and getattr(msg, "content", None):
                parts.append(msg.content)
        return "".join(parts)
    finally:
        aclose = getattr(client, "aclose", None)
        if callable(aclose):
            await aclose()


async def _chat_openai(messages: List[Message], model: str, **kwargs: Any) -> str:
    try:
        from openai import AsyncOpenAI
    except ImportError as e:
        raise RuntimeError("openai package is not installed. pip install openai") from e
    api_key = kwargs.get("api_key") or os.getenv("OPENAI_API_KEY") or ""
    base_url = kwargs.get("base_url") or os.getenv("OPENAI_BASE_URL")
    client_kw: dict = {"api_key": api_key}
    if base_url:
        client_kw["base_url"] = base_url
    client = AsyncOpenAI(**client_kw)
    openai_messages = [{"role": m.role, "content": m.content or ""} for m in messages]
    params: dict = {
        "model": model,
        "messages": openai_messages,
        "stream": False,
    }
    if kwargs.get("max_tokens") is not None:
        params["max_tokens"] = kwargs["max_tokens"]
    if kwargs.get("temperature") is not None:
        params["temperature"] = kwargs["temperature"]
    resp = await client.chat.completions.create(**params)
    if not resp.choices:
        return ""
    content = resp.choices[0].message.content
    if isinstance(content, list):
        return "".join(
            p.get("text", "") if isinstance(p, dict) else str(p) for p in content
        )
    return content or ""


async def _chat_gemini(messages: List[Message], model: str, **kwargs: Any) -> str:
    try:
        from google import genai
        from google.genai import types as genai_types
    except ImportError as e:
        raise RuntimeError(
            "google-genai package is not installed. pip install google-genai"
        ) from e
    api_key = kwargs.get("api_key") or os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY") or ""
    client = genai.Client(api_key=api_key, http_options={"api_version": "v1beta"})
    contents: List[Any] = []
    system_instruction: Optional[str] = None
    for m in messages:
        if m.role == "system":
            system_instruction = (m.content or "").strip() or system_instruction
            continue
        role = "model" if m.role == "assistant" else "user"
        parts = [genai_types.Part(text=m.content or "")]
        contents.append(genai_types.Content(role=role, parts=parts))
    config_args: dict = {}
    if system_instruction:
        config_args["system_instruction"] = system_instruction
    config = genai_types.GenerateContentConfig(**config_args)
    resp = await client.aio.models.generate_content(
        model=model,
        contents=contents,
        config=config,
    )
    return resp.text or ""


async def chat(
    messages: List[Message],
    *,
    model: str = "openai:gpt-4.1-mini",
    max_tokens: Optional[int] = None,
    temperature: Optional[float] = None,
    base_url: Optional[str] = None,
    api_key: Optional[str] = None,
) -> str:
    """Non-streaming chat. Uses provider from model string (openai:, ollama:, gemini:)."""
    provider, model_name = _resolve_provider(model)
    kwargs: dict = {}
    if max_tokens is not None:
        kwargs["max_tokens"] = max_tokens
    if temperature is not None:
        kwargs["temperature"] = temperature
    if base_url:
        kwargs["base_url"] = base_url
    if api_key:
        kwargs["api_key"] = api_key

    if provider == "ollama":
        kwargs.setdefault("base_url", "http://localhost:11434")
        return await _chat_ollama(messages, model_name, **kwargs)
    if provider in ("openai", "openai_compatible"):
        return await _chat_openai(messages, model_name, **kwargs)
    if provider in ("gemini", "google"):
        return await _chat_gemini(messages, model_name, **kwargs)
    raise ValueError(f"Unknown LLM provider: {provider}. Use openai:, ollama:, or gemini:")
