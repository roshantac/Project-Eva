"""Unit tests for eva_memory: categories, prompts, engine (mocked LLM), search."""
from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

from src.eva_memory.categories import (
    CATEGORY_LIST,
    PERSONAL_MEMORY_CATEGORIES,
    normalize_category,
)
from src.eva_memory.persistence.sqlite import SQLiteMetadataStore
from src.eva_memory.prompts import build_fact_extraction_messages, build_update_messages
from src.llm_core import Message


class TestCategories(unittest.TestCase):
    def test_category_list_non_empty(self) -> None:
        self.assertIsInstance(CATEGORY_LIST, list)
        self.assertGreater(len(CATEGORY_LIST), 0)

    def test_personal_memory_categories_has_expected_keys(self) -> None:
        for key in ("identity_profile", "work_career", "health_wellness", "goals_plans"):
            self.assertIn(key, PERSONAL_MEMORY_CATEGORIES)

    def test_normalize_category_exact(self) -> None:
        self.assertEqual(normalize_category("work_career"), "work_career")

    def test_normalize_category_dash_to_underscore(self) -> None:
        self.assertEqual(normalize_category("work-career"), "work_career")

    def test_normalize_category_none_or_empty(self) -> None:
        self.assertIsNone(normalize_category(None))
        self.assertIsNone(normalize_category(""))

    def test_normalize_category_unknown_returns_none(self) -> None:
        self.assertIsNone(normalize_category("unknown_category_xyz"))


class TestPrompts(unittest.TestCase):
    def test_build_fact_extraction_messages_returns_two_messages(self) -> None:
        messages = build_fact_extraction_messages("user: I love jazz.\nassistant: Nice!")
        self.assertEqual(len(messages), 2)
        self.assertEqual(messages[0].role, "system")
        self.assertEqual(messages[1].role, "user")
        self.assertIn("jazz", messages[1].content)
        self.assertIn("facts", messages[1].content)

    def test_build_update_messages_contains_existing_and_new(self) -> None:
        existing = [{"id": "m1", "fact": "User likes tea.", "metadata": {}}]
        new_facts = [{"fact": "User prefers green tea.", "category": "preferences_general"}]
        messages = build_update_messages(existing, new_facts)
        self.assertEqual(len(messages), 2)
        self.assertIn("operations", messages[1].content)
        self.assertIn("m1", messages[1].content)
        self.assertIn("green tea", messages[1].content)


class TestSQLiteFTS(unittest.TestCase):
    def test_fts_create_and_search(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            db_path = Path(tmp) / "mem.db"
            store = SQLiteMetadataStore(db_path)
            faiss_id = store.allocate_faiss_id("u1")
            row = store.insert_memory("u1", "Hello world and coffee", None, faiss_id)
            self.assertIsNotNone(row)
            results = store.search_text("u1", "coffee", limit=5)
            self.assertEqual(len(results), 1)
            self.assertIn("coffee", results[0][0].text)
            store.close()


class TestEngineWithMockedLLM(unittest.IsolatedAsyncioTestCase):
    async def test_infer_and_update_from_messages_empty_transcript_returns_empty(self) -> None:
        from src.eva_memory.engine import LlmAwareMemoryEngine
        from src.eva_memory.service.memory_store import MemoryStore
        from src.eva_memory.config import MemoryStoreConfig

        with tempfile.TemporaryDirectory() as tmp:
            config = MemoryStoreConfig(
                sqlite_path=Path(tmp) / "mem.db",
                faiss_dir=Path(tmp) / "faiss",
            )
            config.ensure_directories()
            store = MemoryStore(config=config)
            mock_llm = AsyncMock()
            mock_llm.chat_json = AsyncMock(return_value={"facts": []})
            engine = LlmAwareMemoryEngine(store=store, llm_client=mock_llm)
            messages: list[Message] = [Message(role="system", content="")]
            changes = await engine.infer_and_update_from_messages("u1", messages)
            self.assertEqual(changes, [])

    async def test_infer_and_update_from_messages_adds_when_llm_returns_add(self) -> None:
        from src.eva_memory.engine import LlmAwareMemoryEngine
        from src.eva_memory.llm_client import MemoryLLMClient
        from src.eva_memory.models import MemoryRecord
        from src.eva_memory.service.memory_store import MemoryStore

        mock_store = MagicMock(spec=MemoryStore)
        mock_store.search = MagicMock(return_value=[])
        added: list[tuple] = []

        def capture_add(user_id: str, text: str, metadata: dict | None) -> MemoryRecord:
            rec = MemoryRecord(
                memory_id="mock-id",
                user_id=user_id,
                text=text,
                metadata=metadata,
                created_at="",
                updated_at=None,
                is_deleted=False,
            )
            added.append((user_id, text, metadata))
            return rec

        mock_store.add = MagicMock(side_effect=capture_add)

        call_count = 0

        async def mock_chat_json(msgs: list) -> dict:
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return {
                    "facts": [
                        {
                            "fact": "User loves jazz.",
                            "category": "preferences_general",
                            "source_role": "user",
                            "importance": "medium",
                            "confidence": 0.9,
                        }
                    ]
                }
            return {
                "operations": [
                    {
                        "event": "ADD",
                        "target_id": None,
                        "fact": "User loves jazz.",
                        "category": "preferences_general",
                        "subcategory": None,
                        "time_scope": None,
                        "importance": "medium",
                        "confidence": 0.9,
                        "tags": None,
                    }
                ]
            }

        mock_client = MagicMock(spec=MemoryLLMClient)
        mock_client.chat_json = AsyncMock(side_effect=mock_chat_json)
        engine = LlmAwareMemoryEngine(store=mock_store, llm_client=mock_client)
        messages = [Message(role="user", content="I really love jazz music.")]
        changes = await engine.infer_and_update_from_messages("u1", messages)
        self.assertGreater(len(changes), 0)
        self.assertTrue(any(c.event == "ADD" for c in changes))
        self.assertEqual(len(added), 1)
        self.assertEqual(added[0][1], "User loves jazz.")


if __name__ == "__main__":
    unittest.main()
