"""Ollama LLM provider implementation."""

from __future__ import annotations

import json
import uuid
from collections.abc import AsyncIterator
from typing import Any

from ollama import AsyncClient

from ..models import Message
from .base import LLMProvider, StreamChunk


def _message_to_chat(m: Message) -> dict[str, Any]:
    """Convert our Message to Ollama chat format."""
    out: dict[str, Any] = {"role": m.role, "content": m.content or ""}
    if m.tool_calls:
        out["tool_calls"] = [
            {
                "id": tc.get("id") or str(uuid.uuid4()),
                "type": "function",
                "function": {
                    "name": tc.get("name", ""),
                    "arguments": tc.get("params") or tc.get("arguments") or {},
                },
            }
            for tc in m.tool_calls
        ]
    if m.tool_call_id:
        out["tool_call_id"] = m.tool_call_id
    if m.name:
        out["name"] = m.name
    return out


def _tool_schema_to_ollama(tool: dict[str, Any]) -> dict[str, Any]:
    """Normalize tool def to Ollama/OpenAI format."""
    fn = tool.get("function", tool) if "function" in tool else tool
    if "function" in fn:
        return tool
    return {
        "type": "function",
        "function": {
            "name": fn.get("name", ""),
            "description": fn.get("description", ""),
            "parameters": fn.get("parameters", {"type": "object", "properties": {}}),
        },
    }


class OllamaProvider(LLMProvider):
    """Ollama-backed LLM provider."""

    def __init__(self, default_model: str = "llama3.2", base_url: str | None = None):
        self.default_model = default_model
        self.base_url = base_url or "http://localhost:11434"

    async def chat(
        self,
        messages: list[Message],
        *,
        model: str | None = None,
        tools: list[dict[str, Any]] | None = None,
        **kwargs: Any,
    ) -> tuple[str, list[dict[str, Any]]]:
        content_parts: list[str] = []
        tool_calls: list[dict[str, Any]] = []
        async for chunk in self.stream_chat(
            messages, model=model, tools=tools, **kwargs
        ):
            if chunk.type == "text_delta" and chunk.content:
                content_parts.append(chunk.content)
            if chunk.tool_calls:
                tool_calls = chunk.tool_calls
        return "".join(content_parts), tool_calls

    async def stream_chat(
        self,
        messages: list[Message],
        *,
        model: str | None = None,
        tools: list[dict[str, Any]] | None = None,
        **kwargs: Any,
    ) -> AsyncIterator[StreamChunk]:
        client = AsyncClient(host=self.base_url)
        chat_messages = [_message_to_chat(m) for m in messages]
        ollama_tools = (
            [_tool_schema_to_ollama(t) for t in (tools or [])] if tools else None
        )
        model_name = model or self.default_model
        content_parts: list[str] = []
        final_tool_calls: list[dict[str, Any]] = []

        try:
            stream = await client.chat(
                model=model_name,
                messages=chat_messages,
                tools=ollama_tools,
                stream=True,
            )
            async for chunk in stream:
                msg = getattr(chunk, "message", None)
                if msg is None:
                    continue
                delta = getattr(msg, "content", None) or ""
                if delta:
                    content_parts.append(delta)
                    yield StreamChunk(type="text_delta", content=delta)
                tool_calls = getattr(msg, "tool_calls", None)
                if tool_calls:
                    for tc in tool_calls:
                        fn = getattr(tc, "function", None)
                        if fn is None:
                            continue
                        name = getattr(fn, "name", "") or ""
                        args = getattr(fn, "arguments", None)
                        if isinstance(args, str):
                            try:
                                args = json.loads(args)
                            except Exception:
                                args = {}
                        if not isinstance(args, dict):
                            args = {}
                        final_tool_calls.append({
                            "id": str(uuid.uuid4()),
                            "name": name,
                            "params": args,
                        })
            if final_tool_calls:
                yield StreamChunk(
                    type="done",
                    content="".join(content_parts),
                    tool_calls=final_tool_calls,
                )
            else:
                yield StreamChunk(type="done", content="".join(content_parts))
        finally:
            aclose = getattr(client, "aclose", None)
            if callable(aclose):
                await aclose()
