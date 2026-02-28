"""Main agent–tool loop orchestrator."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .config import (
    CONTEXT_SUMMARY_THRESHOLD,
    DEFAULT_CONTEXT_WINDOW,
    DEFAULT_MAX_TOOL_ITERATIONS,
    DEFAULT_MODEL,
    SESSIONS_DIR,
)
from .context_summary import maybe_summarize
from .db import upsert_history, upsert_user
from .llm import chat, get_default_provider
from .models import Message, SessionData, ToolResult
from .providers import LLMProvider
from .session_store import create_session, load_session, save_session
from .system_prompt_loader import get_default_system_prompt
from .tools import BaseTool


@dataclass
class LoopOptions:
    """Options for the agent loop."""

    model: str = DEFAULT_MODEL
    context_window: int = DEFAULT_CONTEXT_WINDOW
    context_summary_threshold: float = CONTEXT_SUMMARY_THRESHOLD
    max_tool_iterations: int = DEFAULT_MAX_TOOL_ITERATIONS
    system_prompt: str | None = None
    llm_provider: LLMProvider | None = None


async def run_loop(
    user_id: str,
    user_message: str,
    session_id: str | None = None,
    tools: list[BaseTool] | None = None,
    options: LoopOptions | None = None,
) -> tuple[str, str, list[Message]]:
    """
    Run one agent–tool loop: append user message, optionally summarize context,
    then LLM → execute tools → repeat until no tool calls or max iterations.
    Persist session to db/sessions and update history/users DBs.

    Returns:
        (session_id, final_assistant_content, full_messages)
    """
    opts = options or LoopOptions()
    tools = tools or []
    tool_map = {t.name: t for t in tools}
    tool_schemas = [t.to_tool_schema() for t in tools]

    # Load or create session
    if session_id:
        messages, metadata = load_session(session_id)
        if not metadata.get("user_id"):
            metadata["user_id"] = user_id
    else:
        session_id, data = create_session(user_id, model=opts.model)
        messages = data.to_messages()
        metadata = dict(data.metadata)

    # Ensure a single system prompt is present at the start of the session.
    system_prompt = opts.system_prompt or get_default_system_prompt()
    if system_prompt and not any(m.role == "system" for m in messages):
        messages.insert(0, Message(role="system", content=system_prompt))

    messages.append(Message(role="user", content=user_message))

    iteration = 0
    while iteration < opts.max_tool_iterations:
        iteration += 1
        # In-memory summarization when over threshold
        messages = await maybe_summarize(
            messages,
            context_window=opts.context_window,
            threshold=opts.context_summary_threshold,
            model=opts.model,
        )
        content, tool_calls = await chat(
            messages,
            model=opts.model,
            tools=tool_schemas if tool_schemas else None,
            provider=opts.llm_provider,
        )

        if not tool_calls:
            messages.append(Message(role="assistant", content=content))
            break

        # Append assistant message with tool_calls for history
        messages.append(
            Message(role="assistant", content=content or "", tool_calls=[{"id": tc.get("id"), "name": tc.get("name"), "params": tc.get("params", {})} for tc in tool_calls])
        )
        for tc in tool_calls:
            name = tc.get("name", "")
            params = tc.get("params") or tc.get("arguments") or {}
            tid = tc.get("id", "")
            tool = tool_map.get(name)
            if tool is None:
                result = ToolResult(success=False, error=f"Unknown tool: {name}")
            else:
                try:
                    result = await tool.execute(params)
                except Exception as e:
                    result = ToolResult(success=False, error=str(e))
            text = result.content if result.success else f"Error: {result.error}"
            messages.append(
                Message(role="tool", content=text, tool_call_id=tid, name=name)
            )

    # Persist session
    metadata["model"] = opts.model
    metadata["message_count"] = len(messages)
    data = SessionData.from_messages(session_id, messages, metadata)
    save_session(data)

    # DB references
    session_file_path = str(SESSIONS_DIR / f"{session_id}.json")
    upsert_history(
        session_id=session_id,
        user_id=user_id,
        session_file_path=session_file_path,
        message_count=len(messages),
        model=opts.model,
        metadata=metadata,
    )
    upsert_user(user_id, metadata={})

    final_content = ""
    for m in reversed(messages):
        if m.role != "assistant":
            continue
        # Only treat assistant messages without tool calls and with non-empty content
        # as valid final replies to return to the client.
        if m.tool_calls:
            continue
        if not (m.content or "").strip():
            continue
        final_content = m.content
        break
    return session_id, final_content, messages
