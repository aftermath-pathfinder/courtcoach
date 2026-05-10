"""Chat route: POST /api/chat — multi-turn coaching conversation."""

import logging
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.services.chat_service import get_chat_reply

logger = logging.getLogger(__name__)

router = APIRouter()


class ChatMessage(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    messages: list[ChatMessage]
    analysis_context: dict[str, Any] | None = None


@router.post("/chat")
def chat(req: ChatRequest) -> dict[str, str]:
    messages = [{"role": m.role, "content": m.content} for m in req.messages]

    try:
        reply = get_chat_reply(messages, req.analysis_context)
    except RuntimeError as exc:
        raise HTTPException(
            status_code=500,
            detail={"status": "error", "message": str(exc)},
        ) from exc

    return {"reply": reply}
