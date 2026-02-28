"""Google Gemini LLM provider implementation for the orchestrator."""

from __future__ import annotations

import os
from collections.abc import AsyncIterator
from typing import Any

from ..models import Message
from .base import LLMProvider, StreamChunk

try:  # Best-effort .env loading
    from dotenv import load_dotenv

    load_dotenv()
except Exception:  # pragma: no cover
    pass

try:
    from google import genai
    from google.genai import types as genai_types

    _GENAI_AVAILABLE = True
except Exception:  # pragma: no cover - optional dependency
    genai = None  # type: ignore[assignment]
    genai_types = None  # type: ignore[assignment]
    _GENAI_AVAILABLE = False


class GeminiProvider(LLMProvider):
    """Gemini provider using the google-genai SDK."""

    def __init__(
        self,
        default_model: str = "gemini-2.5-flash",
        api_key: str | None = None,
    ) -> None:
        self.default_model = default_model
        self.api_key = api_key or os.getenv("GOOGLE_API_KEY") or os.getenv(
            "GEMINI_API_KEY",
            "",
        )
        self._client: Any | None = None

    def _get_client(self) -> Any:
        if not _GENAI_AVAILABLE or genai is None:
            raise RuntimeError(
                "google-genai package is not installed. Install it or remove GeminiProvider usage."
            )
        if not self._client:
            self._client = genai.Client(
                api_key=self.api_key,
                http_options={"api_version": "v1beta"},
            )
        return self._client

    @staticmethod
    def _to_gemini_contents(messages: list[Message]) -> tuple[list[Any], str | None]:
        """Convert internal Message objects into Gemini contents and system instruction."""
        if not _GENAI_AVAILABLE or genai_types is None:
            # Fallback plain format (used only for basic text calls if SDK missing)
            contents: list[dict[str, Any]] = []
            system_instruction: str | None = None
            for m in messages:
                if m.role == "system":
                    system_instruction = (m.content or "").strip() or system_instruction
                    continue
                contents.append({"role": m.role, "content": m.content or ""})
            return contents, system_instruction

        contents: list[genai_types.Content] = []
        system_instruction: str | None = None

        for m in messages:
            if m.role == "system":
                system_instruction = (m.content or "").strip() or system_instruction
                continue
            role = "model" if m.role == "assistant" else "user"
            parts: list[genai_types.Part] = []
            if m.content:
                # Construct Part directly to avoid signature issues with from_text()
                parts.append(genai_types.Part(text=m.content))
            if parts:
                contents.append(genai_types.Content(role=role, parts=parts))

        return contents, system_instruction

    @staticmethod
    def _to_gemini_tools(tools: list[dict[str, Any]] | None) -> list[Any] | None:
        """Convert function tools into Gemini Tool declarations."""
        if not tools or not _GENAI_AVAILABLE or genai_types is None:
            return None
        function_declarations: list[genai_types.FunctionDeclaration] = []
        for t in tools:
            fn = t.get("function") if "function" in t else t
            name = fn.get("name")
            if not name:
                continue
            params = fn.get("parameters") or {}
            function_declarations.append(
                genai_types.FunctionDeclaration(
                    name=name,
                    description=fn.get("description", ""),
                    parameters=params,
                )
            )
        if not function_declarations:
            return None
        return [genai_types.Tool(function_declarations=function_declarations)]

    async def chat(
        self,
        messages: list[Message],
        *,
        model: str | None = None,
        tools: list[dict[str, Any]] | None = None,
        **kwargs: Any,
    ) -> tuple[str, list[dict[str, Any]]]:
        """Non-streaming chat using Gemini generate_content."""
        client = self._get_client()
        contents, system_instruction = self._to_gemini_contents(messages)
        model_name = model or self.default_model

        gemini_tools = self._to_gemini_tools(tools)
        config_args: dict[str, Any] = {}
        if gemini_tools:
            config_args["tools"] = gemini_tools
            if genai_types is not None:
                config_args["tool_config"] = genai_types.ToolConfig(
                    function_calling_config=genai_types.FunctionCallingConfig(
                        mode=genai_types.FunctionCallingConfigMode.AUTO
                    )
                )

        if system_instruction:
            config_args["system_instruction"] = system_instruction

        if genai_types is not None:
            config = genai_types.GenerateContentConfig(**config_args)
            resp = await client.aio.models.generate_content(
                model=model_name,
                contents=contents,
                config=config,
            )
            text = resp.text or ""
            tool_calls: list[dict[str, Any]] = []
            # Collect function calls from the final response (if any)
            for cand in getattr(resp, "candidates", []) or []:
                content = getattr(cand, "content", None)
                if content and getattr(content, "parts", None):
                    for part in content.parts:
                        fc = getattr(part, "function_call", None)
                        if not fc:
                            continue
                        tool_calls.append(
                            {
                                "id": f"call_{fc.name}",
                                "name": fc.name,
                                "params": dict(fc.args) if fc.args else {},
                            }
                        )
            return text, tool_calls

        # Fallback basic text-only call if types are unavailable
        resp = await client.aio.models.generate_content(
            model=model_name,
            contents=contents,
        )
        text = getattr(resp, "text", "") or ""
        return text, []

    async def stream_chat(
        self,
        messages: list[Message],
        *,
        model: str | None = None,
        tools: list[dict[str, Any]] | None = None,
        **kwargs: Any,
    ) -> AsyncIterator[StreamChunk]:
        """Streaming chat for Gemini; yields text deltas and a final done chunk."""
        client = self._get_client()
        contents, system_instruction = self._to_gemini_contents(messages)
        model_name = model or self.default_model

        gemini_tools = self._to_gemini_tools(tools)
        config_args: dict[str, Any] = {}
        if gemini_tools:
            config_args["tools"] = gemini_tools
            if genai_types is not None:
                config_args["tool_config"] = genai_types.ToolConfig(
                    function_calling_config=genai_types.FunctionCallingConfig(
                        mode=genai_types.FunctionCallingConfigMode.AUTO
                    )
                )
        if system_instruction:
            config_args["system_instruction"] = system_instruction

        content_parts: list[str] = []
        tool_calls: list[dict[str, Any]] = []

        if genai_types is not None:
            config = genai_types.GenerateContentConfig(**config_args)
            stream = await client.aio.models.generate_content_stream(
                model=model_name,
                contents=contents,
                config=config,
            )
        else:
            # Fallback: non-streaming call, then emit as a single done chunk
            resp = await client.aio.models.generate_content(
                model=model_name,
                contents=contents,
            )
            text = getattr(resp, "text", "") or ""
            yield StreamChunk(type="done", content=text)
            return

        async for chunk in stream:
            text = getattr(chunk, "text", None)
            if text:
                content_parts.append(text)
                yield StreamChunk(type="text_delta", content=text)

            # Collect function calls from streamed candidates
            for cand in getattr(chunk, "candidates", []) or []:
                content = getattr(cand, "content", None)
                if content and getattr(content, "parts", None):
                    for part in content.parts:
                        fc = getattr(part, "function_call", None)
                        if not fc:
                            continue
                        tool_calls.append(
                            {
                                "id": f"call_{fc.name}_{len(tool_calls)}",
                                "name": fc.name,
                                "params": dict(fc.args) if fc.args else {},
                            }
                        )

        if tool_calls:
            yield StreamChunk(
                type="done",
                content="".join(content_parts),
                tool_calls=tool_calls,
            )
        else:
            yield StreamChunk(type="done", content="".join(content_parts))

