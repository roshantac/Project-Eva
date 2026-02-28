from __future__ import annotations

"""
Minimal smoke test for the MemoryStore.

This is not a formal test suite; it's a small script you can run manually:

    python -m eva_memory.smoke_test

It assumes a local Ollama server is running and serving the
`nomic-embed-text:latest` model.
"""

from . import MemoryStore


def run() -> None:
    store = MemoryStore()
    user_id = "smoke-user"

    print("Adding memory...")
    rec = store.add(user_id=user_id, text="I live in Bangalore.", metadata={"kind": "profile"})
    print("Added:", rec)

    print("Searching for 'Where do I live?'...")
    hits = store.search(user_id=user_id, query="Where do I live?", k=3)
    print("Search hits:", hits)

    print("Updating memory...")
    updated = store.update(
        user_id=user_id,
        memory_id=rec.memory_id,
        new_text="I live in Bangalore, India.",
        metadata={"kind": "profile"},
    )
    print("Updated:", updated)

    print("Deleting memory...")
    store.delete(user_id=user_id, memory_id=rec.memory_id)
    print("Deleted.")

    print("Listing memories (should be empty or deleted)...")
    print(store.list(user_id=user_id, include_deleted=True))


if __name__ == "__main__":
    run()

