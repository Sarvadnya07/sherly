"""
BACKEND SCHEMAS — backend/api/schemas/contracts.py
Strongly-typed Pydantic contracts for Sherly API & WebSockets.
Kept in 1:1 parity with React TypeScript interfaces.
"""

from __future__ import annotations
from typing import Any, Optional
from pydantic import BaseModel, Field


# ── Chat & Memory ─────────────────────────────────────────────────────────────
class ChatRequest(BaseModel):
    prompt: str
    file_attachment: Optional[str] = None


class ChatResponse(BaseModel):
    user_prompt: str
    assistant_response: str
    timestamp: str
    attached_file: Optional[str] = None


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
    mode: str                          # "auto" | "manual"
    current_model: Optional[str]
    pinned_model: Optional[str]
    is_ollama_running: bool
    models: list[ModelInfo]


class ModelSelectRequest(BaseModel):
    model_name: str


class ModelModeRequest(BaseModel):
    mode: str                          # "auto" | "manual"


class ApiKeyRequest(BaseModel):
    provider: str                      # "openai" | "gemini" | "groq"
    api_key: str


# ── Voice ──────────────────────────────────────────────────────────────────────
class VoiceStatusResponse(BaseModel):
    is_listening: bool
    is_speaking: bool
    current_device: Optional[str]


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
    path: str
    content: str


class TerminalRunRequest(BaseModel):
    command: str


class TerminalRunResponse(BaseModel):
    output: str
    exit_code: int


# ── Actions, Approvals & Previews ─────────────────────────────────────────────
class PendingApproval(BaseModel):
    action_id: str
    command: str
    level: str                          # "confirm" | "dangerous"
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
    model_mode: str
    current_model: Optional[str]
    api_keys_configured: dict[str, bool]
    plugins: dict[str, bool]


class SettingsUpdateRequest(BaseModel):
    auto_mode: Optional[bool] = None
    model_mode: Optional[str] = None
    plugins: Optional[dict[str, bool]] = None


# ── Real-Time WebSocket Event ─────────────────────────────────────────────────
class SherlyEvent(BaseModel):
    event_type: str                     # "status", "stt_text", "action_update", "model_changed"
    payload: dict[str, Any]
