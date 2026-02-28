"""OpenAI LLM provider implementation for the orchestrator."""

from __future__ import annotations

import json
import os
from collections.abc import AsyncIterator
from typing import Any

from ..models import Message
from .base import LLMProvider, StreamChunk

try:  # Best-effort .env loading
    from dotenv import load_dotenv

    load_dotenv()
except Exception:  # pragma: no cover - optional dependency
    pass

try:
    from openai import AsyncOpenAI
except ImportError as exc:  # pragma: no cover - dependency error surfaced at runtime
    AsyncOpenAI = None  # type: ignore[assignment]


class OpenAIProvider(LLMProvider):
    """OpenAI-backed LLM provider using the Chat Completions API."""

    def __init__(
        self,
        default_model: str = "gpt-4.1-nano",
        api_key: str | None = None,
        base_url: str | None = None,
    ) -> None:
        self.default_model = default_model
        self.api_key = api_key or os.getenv("OPENAI_API_KEY") or ""
        self.base_url = base_url or os.getenv("OPENAI_BASE_URL")
        self._client: Any | None = None

    def _get_client(self) -> Any:
        if AsyncOpenAI is None:
            raise RuntimeError(
                "openai package is not installed. Install it or remove OpenAIProvider usage."
            )
        if not self._client:
            kwargs: dict[str, Any] = {"api_key": self.api_key}
            if self.base_url:
                kwargs["base_url"] = self.base_url
            self._client = AsyncOpenAI(**kwargs)
        return self._client

    @staticmethod
    def _to_openai_messages(messages: list[Message]) -> list[dict[str, Any]]:
        """Convert internal Message objects into OpenAI chat message dicts."""
        out: list[dict[str, Any]] = []
        for m in messages:
            base: dict[str, Any] = {"role": m.role, "content": m.content or ""}
            # Assistant tool calls
            if m.role == "assistant" and m.tool_calls:
                oa_tool_calls: list[dict[str, Any]] = []
                for tc in m.tool_calls:
                    name = tc.get("name", "") or ""
                    if not name:
                        continue
                    raw_args = tc.get("params") or tc.get("arguments") or {}
                    if isinstance(raw_args, str):
                        args_str = raw_args
                    else:
                        try:
                            args_str = json.dumps(raw_args)
                        except Exception:
                            args_str = "{}"
                    oa_tool_calls.append(
                        {
                            "id": tc.get("id") or "",
                            "type": "function",
                            "function": {"name": name, "arguments": args_str},
                        }
                    )
                if oa_tool_calls:
                    base["tool_calls"] = oa_tool_calls
            # Tool response messages
            if m.role == "tool":
                if m.tool_call_id:
                    base["tool_call_id"] = m.tool_call_id
                if m.name:
                    base["name"] = m.name
            out.append(base)
        return out

    @staticmethod
    def _parse_tool_calls(choice_message: Any) -> list[dict[str, Any]]:
        """Map OpenAI tool_calls into orchestrator tool_call dicts."""
        tool_calls: list[dict[str, Any]] = []
        for tc in getattr(choice_message, "tool_calls", []) or []:
            fn = getattr(tc, "function", None)
            name = getattr(fn, "name", "") if fn is not None else ""
            raw_args = getattr(fn, "arguments", {}) if fn is not None else {}
            if isinstance(raw_args, str):
                try:
                    params = json.loads(raw_args)
                except Exception:
                    params = {}
            elif isinstance(raw_args, dict):
                params = raw_args
            else:
                params = {}
            tool_calls.append(
                {
                    "id": getattr(tc, "id", "") or "",
                    "name": name,
                    "params": params,
                }
            )
        return tool_calls

    async def chat(
        self,
        messages: list[Message],
        *,
        model: str | None = None,
        tools: list[dict[str, Any]] | None = None,
        **kwargs: Any,
    ) -> tuple[str, list[dict[str, Any]]]:
        """Non-streaming chat using OpenAI Chat Completions."""
        client = self._get_client()
        openai_messages = self._to_openai_messages(messages)
        model_name = model or self.default_model

        params: dict[str, Any] = {
            "model": model_name,
            "messages": openai_messages,
            **kwargs,
        }
        if tools:
            params["tools"] = tools

        resp = await client.chat.completions.create(**params)
        if not resp.choices:
            return "", []

        choice = resp.choices[0].message
        content = choice.content or ""
        if isinstance(content, list):
            # Multi-part content; join text fragments
            content = "".join(
                part.get("text", "") if isinstance(part, dict) else str(part)
                for part in content
            )

        tool_calls = self._parse_tool_calls(choice)
        return content or "", tool_calls

    async def stream_chat(
        self,
        messages: list[Message],
        *,
        model: str | None = None,
        tools: list[dict[str, Any]] | None = None,
        **kwargs: Any,
    ) -> AsyncIterator[StreamChunk]:
        """Streaming chat; yields text deltas and a final done chunk."""
        client = self._get_client()
        openai_messages = self._to_openai_messages(messages)
        model_name = model or self.default_model

        params: dict[str, Any] = {
            "model": model_name,
            "messages": openai_messages,
            "stream": True,
            **kwargs,
        }
        if tools:
            params["tools"] = tools

        stream = await client.chat.completions.create(**params)
        content_parts: list[str] = []
        final_tool_calls: list[dict[str, Any]] = []
        tool_calls_buffer: dict[int, dict[str, Any]] = {}

        async for chunk in stream:
            if not chunk.choices:
                continue
            choice = chunk.choices[0]
            delta = getattr(choice, "delta", None)
            if delta is None:
                continue

            # Text deltas
            if getattr(delta, "content", None):
                text_delta = delta.content or ""
                content_parts.append(text_delta)
                yield StreamChunk(type="text_delta", content=text_delta)

            # Tool call deltas
            if getattr(delta, "tool_calls", None):
                for tc in delta.tool_calls:
                    idx = getattr(tc, "index", 0)
                    buf = tool_calls_buffer.setdefault(
                        idx,
                        {
                            "id": getattr(tc, "id", "") or f"call_{idx}",
                            "name": "",
                            "arguments": "",
                        },
                    )
                    fn = getattr(tc, "function", None)
                    if fn is not None:
                        if getattr(fn, "name", None):
                            buf["name"] = fn.name
                        if getattr(fn, "arguments", None):
                            buf["arguments"] += fn.arguments

            # On finish, convert buffered tool calls
            if getattr(choice, "finish_reason", None):
                for buf in tool_calls_buffer.values():
                    raw_args = buf.get("arguments") or ""
                    try:
                        params_dict = json.loads(raw_args) if raw_args else {}
                    except Exception:
                        params_dict = {}
                    final_tool_calls.append(
                        {
                            "id": buf.get("id", ""),
                            "name": buf.get("name", ""),
                            "params": params_dict,
                        }
                    )

        if final_tool_calls:
            yield StreamChunk(
                type="done",
                content="".join(content_parts),
                tool_calls=final_tool_calls,
            )
        else:
            yield StreamChunk(type="done", content="".join(content_parts))

