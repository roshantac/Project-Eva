"""Context summarization when usage reaches 80% of context window."""

from __future__ import annotations

from .llm import chat
from .models import Message

# Chars per token estimate
CHARS_PER_TOKEN = 4

# How many recent messages to keep intact (turns: user + assistant pairs)
KEEP_LAST_TURNS = 2


def estimate_tokens(messages: list[Message]) -> int:
    """Rough token count for a message list."""
    total = 0
    for m in messages:
        content = m.content or ""
        if isinstance(content, str):
            total += len(content) // CHARS_PER_TOKEN
        total += 50  # overhead per message (role, structure)
    return total


def _format_messages_for_summary(messages: list[Message]) -> str:
    """Format messages as text for the summarizer."""
    parts = []
    for m in messages:
        role = m.role
        content = (m.content or "").strip()
        if content:
            parts.append(f"{role}: {content}")
    return "\n\n".join(parts)


async def summarize_middle(
    messages: list[Message],
    model: str = "llama3.2",
    max_summary_tokens: int = 500,
) -> str:
    """Use LLM to summarize a slice of messages. Returns summary string."""
    text = _format_messages_for_summary(messages)
    if not text.strip():
        return ""
    system = (
        "You are a conversation summarizer. Compress the following conversation into key points "
        "while preserving important information and context. Be concise. Output plain text only."
    )
    summarizer_messages = [
        Message(role="system", content=system),
        Message(role="user", content=text[: 4 * max_summary_tokens * 2]),  # cap input size
    ]
    summary, _ = await chat(summarizer_messages, model=model)
    return (summary or "").strip()


def apply_summarization(
    messages: list[Message],
    context_window: int,
    threshold: float = 0.8,
) -> list[Message]:
    """
    In-memory only: if estimated tokens >= threshold * context_window,
    return a new list with middle messages replaced by a summary placeholder.
    Caller must run summarize_middle and inject the actual summary.
    """
    if not messages:
        return messages
    estimated = estimate_tokens(messages)
    limit = int(context_window * threshold)
    if estimated < limit:
        return messages

    # Keep: system at start; last KEEP_LAST_TURNS turns at end.
    # One "turn" = we keep last N messages (e.g. 4 = 2 user + 2 assistant).
    keep_last_n = max(4, KEEP_LAST_TURNS * 2)
    if len(messages) <= keep_last_n + 2:
        return messages

    system_msgs: list[Message] = []
    rest: list[Message] = []
    for m in messages:
        if m.role == "system":
            system_msgs.append(m)
        else:
            rest.append(m)

    if len(rest) <= keep_last_n:
        return messages

    middle = rest[:-keep_last_n]
    tail = rest[-keep_last_n:]
    # Placeholder: will be replaced by caller with actual summary
    summary_placeholder = Message(
        role="system",
        content="[Previous conversation summary will be inserted here]",
    )
    return system_msgs + [summary_placeholder] + tail


async def maybe_summarize(
    messages: list[Message],
    context_window: int,
    threshold: float = 0.8,
    model: str = "llama3.2",
) -> list[Message]:
    """
    If estimated tokens >= threshold * context_window, summarize the middle
    and return a shortened list. Otherwise return messages unchanged.
    """
    if not messages:
        return messages
    estimated = estimate_tokens(messages)
    limit = int(context_window * threshold)
    if estimated < limit:
        return messages

    keep_last_n = max(4, KEEP_LAST_TURNS * 2)
    system_msgs = [m for m in messages if m.role == "system"]
    rest = [m for m in messages if m.role != "system"]
    if len(rest) <= keep_last_n:
        return messages

    middle = rest[:-keep_last_n]
    tail = rest[-keep_last_n:]
    summary = await summarize_middle(middle, model=model)
    summary_msg = Message(
        role="system",
        content=f"[Summary of earlier conversation]\n{summary}" if summary else "[Earlier messages omitted.]",
    )
    return system_msgs + [summary_msg] + tail
