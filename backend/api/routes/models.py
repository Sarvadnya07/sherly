"""
MODELS ROUTES — backend/api/routes/models.py
Handles local Ollama model scanning, selection, auto-detection toggle,
unloading, and remote API provider keys.
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from backend.api.schemas.contracts import (
    ModelsListResponse, ModelInfo, ModelSelectRequest, ModelModeRequest, ApiKeyRequest
)
from backend.api.websocket.ws_manager import manager
import config_manager
import model_scanner
import model_manager
from sherly_core.model_resolver import resolve_model

router = APIRouter(prefix="/api/models", tags=["models"])


@router.get("", response_model=ModelsListResponse)
def get_models():
    mode = config_manager.get_model_mode()
    current = config_manager.get_current_model()
    pinned = config_manager.get_pinned_model()
    is_running = model_scanner.is_ollama_running()
    raw_models = model_scanner.scan_ollama_models()

    models = [
        ModelInfo(
            name=m.get("name", ""),
            family=m.get("family", ""),
            tag=m.get("tag", ""),
            size=m.get("size", 0),
            coding=m.get("coding", False),
            local=m.get("local", True),
        )
        for m in raw_models
    ]

    return ModelsListResponse(
        mode=mode,
        current_model=current,
        pinned_model=pinned,
        is_ollama_running=is_running,
        models=models,
    )


@router.post("/select")
async def select_model(req: ModelSelectRequest):
    res = config_manager.set_current_model(req.model_name)
    await manager.broadcast_event("model_changed", {"current_model": req.model_name, "mode": "manual"})
    return {"message": res, "current_model": req.model_name}


@router.post("/mode")
async def set_mode(req: ModelModeRequest):
    if req.mode == "auto":
        config_manager.enable_auto_detection()
        resolved = resolve_model(config_manager, model_scanner)
        await manager.broadcast_event("model_changed", {"current_model": resolved, "mode": "auto"})
        return {"mode": "auto", "current_model": resolved}
    else:
        config_manager.set_model_mode("manual")
        current = config_manager.get_current_model()
        await manager.broadcast_event("model_changed", {"current_model": current, "mode": "manual"})
        return {"mode": "manual", "current_model": current}


@router.post("/refresh")
async def refresh_models():
    models = model_scanner.scan_ollama_models()
    resolved = resolve_model(config_manager, model_scanner)
    await manager.broadcast_event("model_changed", {"current_model": resolved, "mode": config_manager.get_model_mode()})
    return {"count": len(models), "resolved": resolved}


@router.post("/unload")
def unload_model():
    model_manager.unload_model()
    return {"message": "Active model unloaded"}


@router.post("/key")
def set_api_key(req: ApiKeyRequest):
    config_manager.set_api_key(req.provider, req.api_key)
    return {"message": f"API Key for {req.provider} updated"}
