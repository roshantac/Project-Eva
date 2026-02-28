"""Chat router: agent loop endpoint."""

from __future__ import annotations

import asyncio

from fastapi import APIRouter, BackgroundTasks, HTTPException
from pydantic import BaseModel, Field

from src.agent_orchestrator.loop import LoopOptions, run_loop
from src.agent_orchestrator.system_prompt_loader import get_default_system_prompt
from src.agent_orchestrator.tools import get_tools_for_user

try:
    from src.eva_memory.memory_client import add_turn_background, get_context_sync
except ImportError:
    add_turn_background = None
    get_context_sync = None


router = APIRouter(prefix="/chat", tags=["chat"])


class ChatRequest(BaseModel):
    """Request body for POST /chat."""

    user_id: str = Field(..., description="User identifier")
    message: str = Field(..., description="User message")
    session_id: str | None = Field(None, description="Optional session id to continue")
    system_prompt: str | None = Field(None, description="Optional system prompt")
    model: str = Field(
        "openai:gpt-5.1-nano",
        description=(
            "LLM model in 'provider:model' format (e.g. 'openai:gpt-4o-mini', "
            "'gemini:gemini-2.5-flash'). If no ':' is present, the value is "
            "treated as an Ollama model name."
        ),
    )


class ChatResponse(BaseModel):
    """Response for POST /chat."""

    session_id: str
    reply: str
    message_count: int = 0


@router.post("", response_model=ChatResponse)
async def chat(request: ChatRequest, background_tasks: BackgroundTasks) -> ChatResponse:
    """Run the agent loop and return the assistant reply. Memory context is injected before the LLM call; the turn is added to memory in a background task after the response is sent."""
    base_prompt = request.system_prompt or get_default_system_prompt()
    if get_context_sync is not None:
        memory_context = await asyncio.to_thread(
            get_context_sync,
            request.user_id,
            request.message,
            k=5,
            mode="semantic",
        )
        if memory_context:
            base_prompt = f"{base_prompt}\n\n{memory_context}".strip()
    opts = LoopOptions(system_prompt=base_prompt or None, model=request.model)
    try:
        tools = get_tools_for_user(request.user_id)
        session_id, reply, messages = await run_loop(
            user_id=request.user_id,
            user_message=request.message,
            session_id=request.session_id,
            tools=tools,
            options=opts,
        )
        response = ChatResponse(
            session_id=session_id,
            reply=reply,
            message_count=len(messages),
        )
        if add_turn_background is not None and (request.message.strip() or reply.strip()):
            background_tasks.add_task(
                add_turn_background,
                request.user_id,
                request.message,
                reply,
            )
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e
