"""FastAPI router for the agent orchestrator."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from src.agent_orchestrator.loop import LoopOptions, run_loop
from src.agent_orchestrator.tools import get_tools_for_user


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
async def chat(request: ChatRequest) -> ChatResponse:
    """Run the agent loop and return the assistant reply."""
    opts = LoopOptions(system_prompt=request.system_prompt, model=request.model)
    try:
        tools = get_tools_for_user(request.user_id)
        session_id, reply, messages = await run_loop(
            user_id=request.user_id,
            user_message=request.message,
            session_id=request.session_id,
            tools=tools,
            options=opts,
        )
        return ChatResponse(
            session_id=session_id,
            reply=reply,
            message_count=len(messages),
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e
