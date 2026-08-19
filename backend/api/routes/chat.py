"""
CHAT ROUTES — backend/api/routes/chat.py
Handles chat messages, command routing, and conversation memory.
"""

from __future__ import annotations

from datetime import datetime
from fastapi import APIRouter, HTTPException

from fastapi.concurrency import run_in_threadpool

from backend.api.schemas.contracts import ChatRequest, ChatResponse, ChatHistoryResponse
from backend.api.websocket.ws_manager import manager
from command_router import route_command
from memory import get_context
from input_validator import is_valid_input, record_command

router = APIRouter(prefix="/api/chat", tags=["chat"])


@router.post("", response_model=ChatResponse)
async def send_chat(req: ChatRequest):
    valid, cleaned = is_valid_input(req.prompt)
    if not valid:
        raise HTTPException(status_code=400, detail=cleaned)

    record_command(cleaned)

    # Broadcast thinking state
    await manager.broadcast_event("status", {"status": "thinking", "prompt": cleaned})

    # Route command in thread pool; always broadcast ready in finally so clients
    # never get stuck in the "thinking" state if route_command raises.
    full_prompt = f"File: {req.file_attachment}\n{cleaned}" if req.file_attachment else cleaned
    try:
        response_text = await run_in_threadpool(route_command, full_prompt)
    except Exception as exc:
        await manager.broadcast_event("status", {"status": "ready"})
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    finally:
        # Broadcast ready unconditionally (guard against double-broadcast on error path)
        await manager.broadcast_event("status", {"status": "ready"})

    time_str = datetime.now().strftime("%I:%M %p")
    return ChatResponse(
        user_prompt=req.prompt,
        assistant_response=response_text,
        timestamp=time_str,
        attached_file=req.file_attachment,
    )


@router.get("/history", response_model=ChatHistoryResponse)
def get_chat_history():
    raw_context = get_context(limit=20)
    messages = []
    if raw_context:
        lines = raw_context.split("\n")
        user_msg = ""
        for line in lines:
            if line.startswith("User: "):
                user_msg = line[6:]
            elif line.startswith("Assistant: "):
                ai_msg = line[11:]
                if user_msg:
                    messages.append(
                        ChatResponse(
                            user_prompt=user_msg,
                            assistant_response=ai_msg,
                            timestamp=datetime.now().strftime("%I:%M %p"),
                        )
                    )
                    user_msg = ""
    return ChatHistoryResponse(messages=messages)
