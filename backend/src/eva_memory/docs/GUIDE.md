# EVA Memory — User Guide

A standalone Python package for **user-scoped long-term memory**: store, search, update, and delete facts about your users. Use it to give assistants and agents persistent context (preferences, identity, goals) and to learn from conversations over time.

---

## Table of contents

1. [What EVA Memory does](#1-what-eva-memory-does)
2. [Concepts](#2-concepts)
3. [Installation and dependencies](#3-installation-and-dependencies)
4. [Configuration](#4-configuration)
5. [Creating the client](#5-creating-the-client)
6. [Core API: add, get, update, delete, list](#6-core-api-add-get-update-delete-list)
7. [Search: semantic, text, and hybrid](#7-search-semantic-text-and-hybrid)
8. [Metadata and categories](#8-metadata-and-categories)
9. [Context for prompts](#9-context-for-prompts)
10. [LLM-assisted memory from conversation](#10-llm-assisted-memory-from-conversation)
11. [Integration patterns](#11-integration-patterns)
12. [Best practices](#12-best-practices)
13. [Environment variables and troubleshooting](#13-environment-variables-and-troubleshooting)

---

## 1. What EVA Memory does

- **Stores** user facts as text with optional metadata (e.g. category, importance).
- **Indexes** with vector embeddings for **semantic search** and with SQLite FTS for **full-text search**.
- **Searches** by meaning (semantic), by keywords (text), or **hybrid** (both combined).
- **Optionally uses an LLM** to extract facts from conversation turns and merge them (add/update/delete) into memory.

You create a **client** with a **config** (paths, embedding provider, optional LLM). All operations are **per user** via `user_id`.

---

## 2. Concepts

| Concept | Description |
|--------|-------------|
| **user_id** | Every memory belongs to a user. All API methods take `user_id`; data is isolated per user. |
| **Memory** | A single fact: `text` (required) plus optional `metadata` (e.g. `category`, `importance`). Stored in SQLite and as a vector in FAISS. |
| **Semantic search** | Vector similarity: finds memories that *mean* something similar to the query (e.g. “theme preference” matches “User prefers dark mode”). |
| **Text search** | Full-text search (FTS): matches keywords (e.g. “jazz” in “User loves jazz music”). |
| **Hybrid search** | Combines semantic and text scores (default weighting 0.6 semantic + 0.4 text) for better recall. |
| **LLM-assisted add** | You pass a short conversation; the LLM extracts durable facts and decides add/update/delete, then the client applies those changes. |

---

## 3. Installation and dependencies

Ensure these are available (e.g. in your `pyproject.toml` or `requirements.txt`):

- **Core:** `pydantic`, `numpy`, `faiss-cpu`, `ollama` (for Ollama embeddings)
- **Embeddings:** `ollama` and/or `openai` (depending on your `EmbeddingConfig`)
- **LLM (optional):** `openai` and/or `google-genai` (only if you use `add_from_messages`)

Example with `uv`:

```bash
uv add pydantic numpy faiss-cpu ollama openai
```

---

## 4. Configuration

All behaviour is driven by **EvaMemoryConfig**, which you pass when creating the client.

### 4.1 Required: storage paths

- **`sqlite_path`** — Path to the SQLite database file (e.g. `./data/memories.db`). Metadata and FTS index live here.
- **faiss_dir** — Directory for FAISS vector index files (one per user), e.g. `./data/faiss`.

### 4.2 Embedding: provider and model

Use **EmbeddingConfig** with a single `model` string in the form **`provider:model`**:

| Provider | Example `model` | API key / setup |
|----------|------------------|------------------|
| **Ollama** | `ollama:nomic-embed-text:latest` | Local Ollama; optional `base_url` (default `http://localhost:11434`) |
| **OpenAI** | `openai:text-embedding-3-small` | Set `OPENAI_API_KEY` in the environment |

- **`model`** (default: `ollama:nomic-embed-text:latest`): embedding provider and model name.
- **`base_url`** (optional): only for Ollama; leave unset for OpenAI.

API keys are **not** in config; they come from the environment (see [§13](#13-environment-variables-and-troubleshooting)).

### 4.3 LLM (optional): for fact extraction and merge

Used only by **`add_from_messages`**. Configure with **LLMConfig**:

- **`model`**: `provider:model`, e.g. `openai:gpt-4.1-mini`, `ollama:llama3`, `gemini:gemini-2.5-flash`.
- **`max_tokens`** (optional): cap on response length.
- **`temperature`** (default `0.2`): lower = more deterministic.

Relevant env vars: `OPENAI_API_KEY`, `GOOGLE_API_KEY` / `GEMINI_API_KEY` (see [§13](#13-environment-variables-and-troubleshooting)).

### 4.4 Full config example

```python
from pathlib import Path
from src.eva_memory import EvaMemoryConfig, EmbeddingConfig
from src.eva_memory.config import LLMConfig

config = EvaMemoryConfig(
    sqlite_path=Path("./data/memories.db"),
    faiss_dir=Path("./data/faiss"),
    embedding=EmbeddingConfig(
        model="openai:text-embedding-3-small",
        # base_url only for Ollama, e.g. base_url="http://localhost:11434",
    ),
    llm=LLMConfig(
        model="openai:gpt-4.1-mini",
        temperature=0.2,
        max_tokens=2048,
    ),
)
```

---

## 5. Creating the client

One client per configuration; reuse it across requests (e.g. in a web app).

```python
from pathlib import Path
from src.eva_memory import MemoryClient, EvaMemoryConfig

config = EvaMemoryConfig(
    sqlite_path=Path("./data/memories.db"),
    faiss_dir=Path("./data/faiss"),
)
client = MemoryClient(config=config)
```

The client creates the SQLite and FAISS directories if they do not exist. All operations below use this `client` and a **user_id** (string).

---

## 6. Core API: add, get, update, delete, list

### Add a memory

```python
record = client.add(
    user_id="user_123",
    text="User prefers dark mode and large font size.",
    metadata={"category": "assistant_preferences", "importance": "high"},
)
# record.memory_id, record.text, record.metadata, record.created_at
```

- **Returns:** `MemoryRecord` with `memory_id`, `user_id`, `text`, `metadata`, `created_at`, `updated_at`, `is_deleted`.

### Get one memory by id

```python
record = client.get(user_id="user_123", memory_id="uuid-here")
# None if not found or deleted
```

### Update a memory

```python
updated = client.update(
    user_id="user_123",
    memory_id=record.memory_id,
    new_text="User prefers dark mode, large font, and reduced motion.",
    metadata={"category": "assistant_preferences"},
)
```

- **Returns:** updated `MemoryRecord`. The vector index is updated to match the new text.

### Delete a memory

```python
client.delete(user_id="user_123", memory_id=record.memory_id)
```

- Soft-delete in SQLite and removal from the FAISS index. No return value.

### List memories

```python
records = client.list(user_id="user_123", limit=100, include_deleted=False)
# Most recent first; include_deleted=True to include soft-deleted
```

---

## 7. Search: semantic, text, and hybrid

All search methods return a list of **SearchHit**: `{ memory: MemoryRecord, score: float }`. You can restrict by **categories** (metadata `category`).

### Semantic search (vector similarity)

Best for “meaning” and paraphrases.

```python
hits = client.search(
    user_id="user_123",
    query="What are their UI preferences?",
    k=5,
    categories=["assistant_preferences"],  # optional filter
)
for h in hits:
    print(h.score, h.memory.text)
```

- **`client.search_semantic(...)`** is an alias for **`client.search(...)`**.

### Text search (full-text / keywords)

Best for exact words and phrases.

```python
hits = client.search_text(
    user_id="user_123",
    query="jazz music",
    k=5,
    categories=None,
)
```

### Hybrid search (semantic + text combined)

Often the best default for mixed queries.

```python
hits = client.search_hybrid(
    user_id="user_123",
    query="music and theme preferences",
    k=5,
)
```

- Internally: semantic and text runs are combined with a default weight (e.g. 0.6 semantic, 0.4 text); results are merged and re-ranked.

**When to use which**

- **Semantic:** “remind me what they said about deadlines”, “diet preferences”.
- **Text:** “jazz”, “Project Alpha”, “not after 6pm”.
- **Hybrid:** general-purpose or when you want both meaning and keyword match.

---

## 8. Metadata and categories

- **metadata** is a free-form dict. Common key: **`category`**, used for filtering in search and for LLM fact extraction.

Supported **categories** (use exactly, or normalize with dashes→underscores):

| Category | Use for |
|----------|--------|
| `identity_profile` | Identity, demographics, languages, location |
| `preferences_general` | Food, music, brands, products, media, style |
| `preferences_workstyle` | Work style, communication, meetings |
| `work_career` | Jobs, roles, employers, projects |
| `education_skills` | Education, courses, certifications, skills |
| `relationships_family` | Family members and facts |
| `relationships_social` | Friends, colleagues, social |
| `hobbies_interests` | Hobbies, sports, games, interests |
| `health_wellness` | Health, allergies, routines, fitness |
| `finance_life_admin` | Budgets, bills, subscriptions |
| `logistics_routines` | Routines, schedules, time zones, travel |
| `digital_life_tools` | Devices, apps, services |
| `goals_plans` | Goals, projects, milestones |
| `constraints_boundaries` | Limits and things to avoid |
| `assistant_preferences` | How the user wants the assistant to behave |

Example with metadata:

```python
client.add(
    user_id="user_123",
    text="User is allergic to peanuts.",
    metadata={"category": "health_wellness", "importance": "high"},
)
```

---

## 9. Context for prompts

To inject relevant memories into a system or user prompt, use **`get_context`**:

```python
context = client.get_context(
    user_id="user_123",
    query="user's current message or a short summary",
    k=5,
    mode="semantic",  # or "text" or "hybrid"
    categories=None,
)
# context is a string, e.g.:
# "Relevant user context:\n- User prefers dark mode.\n- User loves jazz."
```

- **Empty string** if no hits or invalid `user_id`/`query`.
- **mode:** `"semantic"` (default), `"text"`, or `"hybrid"`.
- Use the same `query` (or the last user message) so the context matches the current turn.

Example in a chat flow:

```python
user_message = "What did I tell you about my diet?"
context = client.get_context(user_id="user_123", query=user_message, k=5)
system_prompt = f"{base_system_prompt}\n\n{context}"
# Then call your LLM with system_prompt + conversation
```

---

## 10. LLM-assisted memory from conversation

**`add_from_messages`** lets the LLM extract durable facts from a short conversation and then **add**, **update**, or **delete** memories accordingly.

### When to use

- After a user/assistant exchange where the user (or assistant) revealed something worth remembering (preference, fact, constraint, goal).
- In a background task after sending the reply, so latency is not on the critical path.

### API

```python
from src.eva_memory import Message

messages = [
    Message(role="user", content="I’ve switched to a vegetarian diet."),
    Message(role="assistant", content="I’ll remember that. Any allergies I should know about?"),
]
changes = await client.add_from_messages(
    user_id="user_123",
    messages=messages,
    category_hint="health_wellness",  # optional
)
# changes: list of MemoryChange (event: ADD | UPDATE | DELETE, memory_id, new_text, etc.)
```

- **category_hint** (optional): nudges the LLM toward a category when it’s obvious (e.g. diet → `health_wellness`).
- **Returns:** list of **MemoryChange** describing what was added, updated, or deleted.

### How it works

1. The LLM gets the conversation and a list of categories; it returns **facts** (short sentences + category, importance, etc.).
2. The client finds existing memories that might overlap (semantic search per fact).
3. The LLM gets existing memories + new facts and returns **operations**: ADD / UPDATE / DELETE.
4. The client applies those operations (add/update/delete) in the store.

So you don’t write the fact strings yourself; the model decides what to store and how to merge.

### Example: run after each turn (e.g. FastAPI background task)

```python
# After sending the HTTP response, in a background task:
await client.add_from_messages(
    user_id=request.user_id,
    messages=[
        Message(role="user", content=request.message),
        Message(role="assistant", content=assistant_reply),
    ],
    category_hint=None,
)
```

---

## 11. Integration patterns

### Single shared client (recommended)

Create the client once at startup and reuse it (e.g. store in app state or a global):

```python
# At app startup
config = EvaMemoryConfig(sqlite_path=..., faiss_dir=...)
memory_client = MemoryClient(config=config)

# In request handlers
context = memory_client.get_context(user_id=user_id, query=message, k=5)
# ...
await memory_client.add_from_messages(user_id=user_id, messages=[...])
```

### FastAPI: dependency or app state

```python
from fastapi import FastAPI, Depends

app = FastAPI()
memory_client: MemoryClient | None = None

@app.on_event("startup")
def startup():
    global memory_client
    config = EvaMemoryConfig(sqlite_path=Path("..."), faiss_dir=Path("..."))
    memory_client = MemoryClient(config=config)

def get_memory():
    return memory_client

@app.post("/chat")
async def chat(user_id: str, message: str, mc: MemoryClient = Depends(get_memory)):
    context = mc.get_context(user_id=user_id, query=message, k=5)
    # ... call LLM, then e.g. background_tasks.add_task(add_turn, mc, user_id, message, reply)
```

### Background “add turn” helper

```python
async def add_turn_after_reply(client: MemoryClient, user_id: str, user_msg: str, reply: str):
    from src.eva_memory import Message
    await client.add_from_messages(
        user_id=user_id,
        messages=[Message(role="user", content=user_msg), Message(role="assistant", content=reply)],
    )

# After sending the response:
# background_tasks.add_task(add_turn_after_reply, client, user_id, user_message, assistant_reply)
```

---

## 12. Best practices

1. **Reuse one client** per process; don’t create a new `MemoryClient` per request.
2. **Use a stable user_id** (e.g. auth subject id) so the same user always sees the same memories.
3. **Inject context before the LLM call** with `get_context(user_id, query=current_message, k=5)` so the model sees relevant memories.
4. **Persist turns in the background** with `add_from_messages` after replying, so latency is not affected.
5. **Set `category` in metadata** when you add or update manually; it improves filtered search and LLM behaviour.
6. **Prefer hybrid search** when you’re not sure: `search_hybrid` or `get_context(..., mode="hybrid")`.
7. **Keep memory text short and factual** (e.g. “User prefers dark mode”) so retrieval stays precise.

---

## 13. Environment variables and troubleshooting

| Purpose | Variable | Used by |
|--------|----------|--------|
| OpenAI API (embeddings) | `OPENAI_API_KEY` | `EmbeddingConfig(model="openai:...")` |
| OpenAI API (LLM) | `OPENAI_API_KEY` | `LLMConfig(model="openai:...")` |
| OpenAI base URL (optional) | `OPENAI_BASE_URL` | OpenAI client (embeddings/LLM) |
| Google / Gemini API | `GOOGLE_API_KEY` or `GEMINI_API_KEY` | `LLMConfig(model="gemini:...")` |

- **Ollama** does not use API keys; ensure the server is running at `base_url` (default `http://localhost:11434`).
- **“Unknown embedding provider”**: use `ollama:...` or `openai:...` in `EmbeddingConfig.model`.
- **Empty search results**: check that you have added memories for that `user_id` and that the query is not empty. For semantic search, try a different phrasing or hybrid.
- **LLM errors in add_from_messages**: confirm the LLM provider (openai/gemini/ollama) is configured and the corresponding env vars are set.

---

## Quick reference

| Task | Method |
|------|--------|
| Create client | `MemoryClient(config)` |
| Add memory | `client.add(user_id, text, metadata=None)` |
| Get one | `client.get(user_id, memory_id)` |
| Update | `client.update(user_id, memory_id, new_text, metadata=None)` |
| Delete | `client.delete(user_id, memory_id)` |
| List | `client.list(user_id, limit=100, include_deleted=False)` |
| Semantic search | `client.search(user_id, query, k=5, categories=None)` |
| Text search | `client.search_text(user_id, query, k=5, categories=None)` |
| Hybrid search | `client.search_hybrid(user_id, query, k=5, categories=None)` |
| Context string | `client.get_context(user_id, query, k=5, mode="semantic", categories=None)` |
| LLM add from chat | `await client.add_from_messages(user_id, messages, category_hint=None)` |

For more detail on config and types, see **README.md** and the docstrings in **config**, **memory_client**, and **models**.
