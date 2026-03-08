# EVA Memory

Standalone Python package for user-scoped memory: **add**, **search**, **update**, and **delete**. No dependency on the rest of the project; config is passed when creating the client.

## Usage

```python
from pathlib import Path
from src.eva_memory import MemoryClient, EvaMemoryConfig
from src.eva_memory.config import EmbeddingConfig, LLMConfig

# Config is required when creating the client
config = EvaMemoryConfig(
    sqlite_path=Path("./data/memories.db"),
    faiss_dir=Path("./data/faiss"),
    # Optional: embedding (provider:model); API keys from env (OPENAI_API_KEY)
    embedding=EmbeddingConfig(model="ollama:nomic-embed-text:latest"),
    # Or OpenAI: embedding=EmbeddingConfig(model="openai:text-embedding-3-small"),
    # Optional: LLM for fact extraction
    llm=LLMConfig(model="openai:gpt-4.1-mini", temperature=0.2),
)
client = MemoryClient(config=config)

# Core API
client.add(user_id="user1", text="User prefers dark mode", metadata={"category": "assistant_preferences"})
hits = client.search(user_id="user1", query="theme preference", k=5)
record = client.update(user_id="user1", memory_id=id, new_text="User prefers dark mode and large font")
client.delete(user_id="user1", memory_id=id)

# Helpers
one = client.get(user_id="user1", memory_id=id)
all_records = client.list(user_id="user1", limit=100)
context_str = client.get_context(user_id="user1", query="preferences", k=5, mode="semantic")

# LLM-assisted: extract facts from conversation and merge into memory
from src.eva_memory import Message
messages = [Message(role="user", content="I love jazz."), Message(role="assistant", content="Noted!")]
changes = await client.add_from_messages(user_id="user1", messages=messages, category_hint="preferences_general")
```

## Config

- **EvaMemoryConfig**: Pass `sqlite_path` and `faiss_dir` (required). Optionally:
  - **embedding**: `EmbeddingConfig(model="provider:model")` — e.g. `ollama:nomic-embed-text:latest`, `openai:text-embedding-3-small`. API key for OpenAI from `OPENAI_API_KEY` env. For Ollama, optional `base_url` (default `http://localhost:11434`).
  - **llm**: `LLMConfig(model="provider:model", ...)` — e.g. `openai:gpt-4.1-mini`, `ollama:llama3`, `gemini:gemini-2.5-flash`.

## Dependencies

Package uses: `pydantic`, `ollama`, `faiss-cpu`, `numpy`. For embeddings: `ollama` (Ollama) or `openai` (OpenAI). For LLM: `openai` and/or `google-genai` depending on `llm.model`.
