from __future__ import annotations

import asyncio
from typing import Any, Dict, List, Optional

from src.llm_core import Message

from .categories import CATEGORY_LIST, normalize_category
from .llm_client import MemoryLLMClient
from .models import ExtractedFact, MemoryChange, MemoryRecord
from .prompts import build_fact_extraction_messages, build_update_messages
from .service.memory_store import MemoryStore


def _flatten_messages(messages: List[Message]) -> str:
    parts: List[str] = []
    for m in messages:
        content = (m.content or "").strip()
        if not content:
            continue
        if m.role == "system":
            continue
        parts.append(f"{m.role}: {content}")
    return "\n".join(parts)


def _build_metadata_from_fact(fact: ExtractedFact) -> Dict[str, Any]:
    meta: Dict[str, Any] = {
        "category": fact.category,
        "subcategory": fact.subcategory,
        "source_role": fact.source_role,
        "time_scope": fact.time_scope,
        "importance": fact.importance,
        "confidence": fact.confidence,
        "tags": fact.tags or [],
    }
    return {k: v for k, v in meta.items() if v is not None}


class LlmAwareMemoryEngine:
    """LLM-assisted memory engine on top of MemoryStore."""

    def __init__(
        self,
        store: MemoryStore,
        llm_client: Optional[MemoryLLMClient] = None,
    ) -> None:
        self._store = store
        self._llm = llm_client or MemoryLLMClient()

    async def infer_and_update_from_messages(
        self,
        user_id: str,
        messages: List[Message],
        *,
        category_hint: Optional[str] = None,
    ) -> List[MemoryChange]:
        transcript = _flatten_messages(messages)
        if not transcript.strip():
            return []

        extraction_messages = build_fact_extraction_messages(transcript)
        extraction_json = await self._llm.chat_json(extraction_messages)
        raw_facts = extraction_json.get("facts") or []

        facts: List[ExtractedFact] = []
        for item in raw_facts:
            if not isinstance(item, dict):
                continue
            text = (item.get("fact") or "").strip()
            if not text:
                continue
            cat_raw = item.get("category") or category_hint
            cat_norm = normalize_category(cat_raw)
            if cat_norm is None:
                # Default to preferences_general when the category is unclear.
                cat_norm = "preferences_general"

            fact = ExtractedFact(
                fact=text,
                category=cat_norm,
                subcategory=item.get("subcategory"),
                source_role=item.get("source_role") or "user",
                time_scope=item.get("time_scope"),
                importance=item.get("importance") or "medium",
                confidence=item.get("confidence"),
                tags=item.get("tags") or None,
            )
            facts.append(fact)

        if not facts:
            return []

        # Collect candidate existing memories for all facts.
        existing_by_id: Dict[str, MemoryRecord] = {}
        for fact in facts:
            # Use the fact text itself as a semantic search query.
            hits = await asyncio.to_thread(
                self._store.search,
                user_id,
                fact.fact,
                5,
            )
            for hit in hits:
                m = hit.memory
                existing_by_id[m.memory_id] = m

        existing_payload: List[Dict[str, Any]] = []
        for m in existing_by_id.values():
            existing_payload.append(
                {
                    "id": m.memory_id,
                    "fact": m.text,
                    "metadata": m.metadata or {},
                }
            )

        new_payload: List[Dict[str, Any]] = []
        for fact in facts:
            new_payload.append(
                {
                    "fact": fact.fact,
                    "category": fact.category,
                    "subcategory": fact.subcategory,
                    "source_role": fact.source_role,
                    "time_scope": fact.time_scope,
                    "importance": fact.importance,
                    "confidence": fact.confidence,
                    "tags": fact.tags or [],
                }
            )

        update_messages = build_update_messages(existing_payload, new_payload)
        update_json = await self._llm.chat_json(update_messages)
        ops = update_json.get("operations") or []

        changes: List[MemoryChange] = []

        for op in ops:
            if not isinstance(op, dict):
                continue
            event = str(op.get("event") or "").upper()
            if event not in {"ADD", "UPDATE", "DELETE"}:
                continue

            target_id = op.get("target_id")
            fact_text = (op.get("fact") or "").strip()
            category = normalize_category(op.get("category")) or (
                category_hint or (facts[0].category if facts else "preferences_general")
            )
            subcategory = op.get("subcategory")
            time_scope = op.get("time_scope")
            importance = op.get("importance")
            confidence = op.get("confidence")
            tags = op.get("tags") or []

            meta: Dict[str, Any] = {
                "category": category,
                "subcategory": subcategory,
                "time_scope": time_scope,
                "importance": importance,
                "confidence": confidence,
                "tags": tags,
            }
            meta = {k: v for k, v in meta.items() if v is not None}

            if event == "ADD":
                if not fact_text:
                    continue
                record = await asyncio.to_thread(
                    self._store.add,
                    user_id,
                    fact_text,
                    meta,
                )
                changes.append(
                    MemoryChange(
                        event="ADD",
                        memory_id=record.memory_id,
                        new_text=record.text,
                        metadata=record.metadata,
                    )
                )
            elif event == "UPDATE" and target_id:
                existing = existing_by_id.get(target_id)
                if existing is None:
                    continue
                new_text = fact_text or existing.text
                record = await asyncio.to_thread(
                    self._store.update,
                    user_id,
                    target_id,
                    new_text,
                    meta or existing.metadata,
                )
                changes.append(
                    MemoryChange(
                        event="UPDATE",
                        memory_id=record.memory_id,
                        old_text=existing.text,
                        new_text=record.text,
                        metadata=record.metadata,
                    )
                )
            elif event == "DELETE" and target_id:
                existing = existing_by_id.get(target_id)
                await asyncio.to_thread(self._store.delete, user_id, target_id)
                changes.append(
                    MemoryChange(
                        event="DELETE",
                        memory_id=target_id,
                        old_text=existing.text if existing else None,
                    )
                )

        return changes


__all__ = ["LlmAwareMemoryEngine"]

