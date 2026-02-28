# Agent Orchestrator

Agent–tool loop with session storage and context summarization.

## Features

- **Agent–tool loop**: User message → LLM (Ollama, default model `llama3.2`) → optional tool calls → repeat until done or max iterations.
- **Session storage**: One JSON file per session under `db/sessions/{session_id}.json` with full message history and metadata (e.g. `created_at`, `updated_at`, `user_id`, `model`).
- **DB references**: `db/history.db` (session id, user id, session file path, metadata); `db/users.db` (user id, metadata).
- **Context summarization**: When estimated token count reaches 80% of the context window, older messages are summarized in-memory before the next LLM call; the session file keeps full history.

## Usage

### Programmatic

```python
import asyncio
from agent_orchestrator import run_loop
from agent_orchestrator.tools import GetTimeTool, get_tools_for_user

async def main():
    session_id, reply, messages = await run_loop(
        user_id="user1",
        user_message="What time is it?",
        tools=get_tools_for_user("user1"),
    )
    print(reply)

asyncio.run(main())
```

### API

Start the server:

```bash
uv run python -m agent_orchestrator.main
```

Then `POST /chat` with JSON body:

- `user_id` (required)
- `message` (required)
- `session_id` (optional, to continue a session)
- `system_prompt` (optional)

## Configuration

See `agent_orchestrator.config`: `DB_DIR`, `SESSIONS_DIR`, `DEFAULT_MODEL`, `DEFAULT_CONTEXT_WINDOW`, `CONTEXT_SUMMARY_THRESHOLD`, `DEFAULT_MAX_TOOL_ITERATIONS`.

## Adding tools

Implement `BaseTool` from `agent_orchestrator.tools` (name, description, parameters as JSON Schema, `async execute(params) -> ToolResult`) and pass a list of instances to `run_loop(..., tools=[...])`.
