"""Chat route — AI financial assistant endpoint."""
from __future__ import annotations

import traceback
from datetime import datetime
from typing import Optional, List, Any
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, ConfigDict
from supabase import Client

from auth import get_current_user
from database import get_supabase
from models import User
from services.agent_service import generate_response, generate_response_stream


def _camel_alias(field_name: str) -> str:
    parts = field_name.split("_")
    return parts[0] + "".join(w.capitalize() for w in parts[1:])


class ChatMessage(BaseModel):
    """Incoming chat message from the user."""
    model_config = ConfigDict(alias_generator=_camel_alias, populate_by_name=True)

    message: str
    conversation_history: Optional[List[dict]] = None


class ActionResult(BaseModel):
    """Result of an executed action."""
    model_config = ConfigDict(alias_generator=_camel_alias, populate_by_name=True)

    type: str
    success: bool
    details: Optional[dict] = None
    error: Optional[str] = None


class ChatResponse(BaseModel):
    """Response from the AI assistant."""
    model_config = ConfigDict(alias_generator=_camel_alias, populate_by_name=True)

    id: str
    role: str = "assistant"
    content: str
    timestamp: datetime
    actions: List[ActionResult] = []


router = APIRouter(tags=["chat"])


@router.post("/chat", response_model=ChatResponse)
async def chat(
    body: ChatMessage,
    supabase: Client = Depends(get_supabase),
    user: User = Depends(get_current_user),
):
    """Send a message to the AI financial assistant and get a response."""
    try:
        response_content, executed_actions = await generate_response(
            supabase=supabase,
            user_id=user.id,
            username=user.username,
            user_message=body.message,
            conversation_history=body.conversation_history,
        )

        # Convert action dicts to ActionResult models
        action_results = [ActionResult(**action) for action in executed_actions]

        return ChatResponse(
            id=uuid4().hex,
            role="assistant",
            content=response_content,
            timestamp=datetime.utcnow(),
            actions=action_results,
        )
    except Exception as e:
        print(f"[CHAT ERROR] {type(e).__name__}: {e!r}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to generate response: {str(e)}")


@router.post("/chat/stream")
async def chat_stream(
    body: ChatMessage,
    supabase: Client = Depends(get_supabase),
    user: User = Depends(get_current_user),
):
    """Stream AI assistant responses as Server-Sent Events."""
    return StreamingResponse(
        generate_response_stream(
            supabase=supabase,
            user_id=user.id,
            username=user.username,
            user_message=body.message,
            conversation_history=body.conversation_history,
        ),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
