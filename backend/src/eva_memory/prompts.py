from __future__ import annotations

import json
from typing import Any, Dict, List

from src.llm_core import Message

from .categories import PERSONAL_MEMORY_CATEGORIES


def build_fact_extraction_messages(transcript: str) -> List[Message]:
    """Build messages for extracting structured user facts from a transcript."""
    categories_text = "\n".join(
        f"- {name}: {desc}" for name, desc in PERSONAL_MEMORY_CATEGORIES.items()
    )

    system_content = (
        "You manage long-term user memory for a personal assistant named EVA. "
        "Your job is to read conversations and extract only durable, re-usable facts "
        "about the user and their world. You must output a single JSON object."
    )

    user_content = (
        "From the conversation below, extract enduring facts that will still matter "
        "later (identity, preferences, habits, goals, relationships, constraints, and other stable details).\n\n"
        "Ignore generic chit-chat or one-off ephemeral details that are not helpful later.\n\n"
        "Use the following categories for each fact:\n"
        f"{categories_text}\n\n"
        "Output format (JSON only):\n"
        "{\n"
        '  \"facts\": [\n'
        "    {\n"
        '      \"fact\": string,                      // concise natural-language fact\n'
        '      \"category\": string,                  // one of the allowed categories\n'
        '      \"subcategory\": string | null,        // optional short refinement like \"music\", \"sleep\", \"diet\"\n'
        '      \"source_role\": string,               // \"user\", \"assistant\", or \"system\"\n'
        '      \"time_scope\": string | null,         // e.g. \"current\", \"past\", \"future_plan\", \"habit\"\n'
        '      \"importance\": string,                // \"low\", \"medium\", or \"high\"\n'
        '      \"confidence\": number,                // 0.0 to 1.0\n'
        '      \"tags\": array<string> | null         // optional keywords (e.g. [\"music\", \"jazz\"])\n'
        "    }\n"
        "  ]\n"
        "}\n\n"
        "Guidelines:\n"
        "- Prefer one fact per entry and keep each fact self-contained.\n"
        "- Mark health, safety, money, deadlines, and strong preferences as high importance when appropriate.\n"
        "- Only include facts you infer with reasonable confidence.\n\n"
        "Return JSON only, with no extra commentary.\n\n"
        "Conversation:\n"
        f"{transcript}"
    )

    return [
        Message(role="system", content=system_content),
        Message(role="user", content=user_content),
    ]


def build_update_messages(
    existing_memories: List[Dict[str, Any]],
    new_facts: List[Dict[str, Any]],
) -> List[Message]:
    """Build messages for deciding how to apply new facts to existing memories."""
    existing_json = json.dumps(existing_memories, ensure_ascii=False, indent=2)
    new_json = json.dumps(new_facts, ensure_ascii=False, indent=2)

    system_content = (
        "You maintain a set of user memories for a personal assistant named EVA. "
        "Each memory is a single fact about the user or their world. "
        "Your job is to decide which memories to add, update, delete, or leave unchanged "
        "when new facts arrive. You must output a single JSON object."
    )

    user_content = (
        "You are given the current stored memories and newly extracted facts.\n\n"
        "Current memories (array of objects):\n"
        f"{existing_json}\n\n"
        "New facts (array of objects with the same shape as in extraction):\n"
        f"{new_json}\n\n"
        "Decide which operations to perform. Use these rules:\n"
        "- ADD when a new fact is not covered by any existing memory.\n"
        "- UPDATE when a new fact refines or replaces an existing memory (for example, a new job title or a changed preference).\n"
        "- DELETE when an existing memory is clearly no longer true and should be removed.\n"
        "- NONE when no action is required for a memory.\n"
        "- Keep the number of changes as small as possible while keeping memories accurate and up to date.\n\n"
        "Output format (JSON only):\n"
        "{\n"
        '  \"operations\": [\n'
        "    {\n"
        '      \"event\": \"ADD\" | \"UPDATE\" | \"DELETE\" | \"NONE\",\n'
        '      \"target_id\": string | null,         // memory_id to update/delete; null for new memories\n'
        '      \"fact\": string | null,              // new fact text for ADD/UPDATE; null for DELETE/NONE\n'
        '      \"category\": string | null,\n'
        '      \"subcategory\": string | null,\n'
        '      \"time_scope\": string | null,\n'
        '      \"importance\": string | null,        // \"low\", \"medium\", \"high\"\n'
        '      \"confidence\": number | null,        // 0.0 to 1.0\n'
        '      \"tags\": array<string> | null\n'
        "    }\n"
        "  ]\n"
        "}\n\n"
        "Only return operations that actually do something (ADD, UPDATE, or DELETE). "
        "You can omit explicit NONE entries.\n"
        "Return JSON only, with no extra commentary."
    )

    return [
        Message(role="system", content=system_content),
        Message(role="user", content=user_content),
    ]


__all__ = ["build_fact_extraction_messages", "build_update_messages"]

