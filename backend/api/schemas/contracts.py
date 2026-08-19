"""
BACKEND SCHEMAS — backend/api/schemas/contracts.py
Strongly-typed Pydantic contracts for Sherly API & WebSockets.
Maintains 1:1 parity with frontend TypeScript interfaces.
"""

from __future__ import annotations

import time
from typing import Any, Optional, Literal
from pydantic import BaseModel, Field


# ── Error Envelope ────────────────────────────────────────────────────────────
class ApiErrorDetail(BaseModel):
    code: str
    message: str
    request_id: Optional[str] = None
    details: Optional[dict[str, Any]] = None


class ApiErrorResponse(BaseModel):
    error: ApiErrorDetail


# ── Chat & Memory ─────────────────────────────────────────────────────────────
class ChatRequest(BaseModel):
    prompt: str = Field(..., min_length=1, max_length=100000)
    file_attachment: Optional[str] = None


class ChatResponse(BaseModel):
    user_prompt: str
    assistant_response: str
    timestamp: str
    attached_file: Optional[str] = None
    request_id: Optional[str] = None


class ChatHistoryResponse(BaseModel):
    messages: list[ChatResponse]


# ── Models & Scanner ──────────────────────────────────────────────────────────
class ModelInfo(BaseModel):
    name: str
    family: str
    tag: str
    size: int
    coding: bool
    local: bool


class ModelsListResponse(BaseModel):
    mode: Literal["auto", "manual"]
    current_model: Optional[str] = None
    pinned_model: Optional[str] = None
    is_ollama_running: bool
    models: list[ModelInfo]


class ModelSelectRequest(BaseModel):
    model_name: str = Field(..., min_length=1)


class ModelModeRequest(BaseModel):
    mode: Literal["auto", "manual"]


class ApiKeyRequest(BaseModel):
    provider: Literal["openai", "gemini", "groq"]
    api_key: str = Field(..., min_length=1)


# ── Voice ──────────────────────────────────────────────────────────────────────
class VoiceStatusResponse(BaseModel):
    is_listening: bool
    is_speaking: bool
    current_device: Optional[str] = None


class AudioDevicesResponse(BaseModel):
    devices: list[str]


# ── Files & Workspace ─────────────────────────────────────────────────────────
class FileNode(BaseModel):
    name: str
    path: str
    is_dir: bool
    children: Optional[list[FileNode]] = None


class FileReadResponse(BaseModel):
    path: str
    content: str


class FileWriteRequest(BaseModel):
    path: str = Field(..., min_length=1)
    content: str


class TerminalRunRequest(BaseModel):
    command: str = Field(..., min_length=1)


class TerminalRunResponse(BaseModel):
    output: str
    exit_code: int


# ── Actions, Approvals & Previews ─────────────────────────────────────────────
class PendingApproval(BaseModel):
    action_id: str
    command: str
    level: Literal["confirm", "dangerous"]
    timestamp: float


class ActionEntry(BaseModel):
    action_id: str
    action: str
    action_type: str
    timestamp: str
    undoable: bool


class PreviewChange(BaseModel):
    action_id: str
    file_path: str
    old_code: str
    new_code: str
    reason: Optional[str] = None


# ── Settings ──────────────────────────────────────────────────────────────────
class SettingsResponse(BaseModel):
    auto_mode: bool
    model_mode: Literal["auto", "manual"]
    current_model: Optional[str] = None
    api_keys_configured: dict[str, bool]
    plugins: dict[str, bool]


class SettingsUpdateRequest(BaseModel):
    auto_mode: Optional[bool] = None
    model_mode: Optional[Literal["auto", "manual"]] = None
    plugins: Optional[dict[str, bool]] = None


# ── Real-Time WebSocket Event Envelopes ───────────────────────────────────────
class StatusPayload(BaseModel):
    status: Literal["ready", "thinking", "listening", "speaking"]
    prompt: Optional[str] = None


class SttTextPayload(BaseModel):
    text: str
    is_final: Optional[bool] = True


class ActionUpdatePayload(BaseModel):
    action_id: str
    status: Literal["approved", "rejected", "preview_applied", "preview_rejected"]


class ModelChangedPayload(BaseModel):
    current_model: Optional[str] = None
    mode: Literal["auto", "manual"]


class SherlyEvent(BaseModel):
    event_type: Literal["status", "stt_text", "action_update", "model_changed", "pong"]
    payload: dict[str, Any]
    timestamp: float = Field(default_factory=time.time)
    request_id: Optional[str] = None
