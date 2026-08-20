"""
HEALTH & OBSERVABILITY ROUTES — backend/api/routes/health.py
Provides fast, non-blocking application health probes, provider status, and diagnostic telemetry.
"""

from __future__ import annotations

import time
from typing import Any, Dict
from fastapi import APIRouter
from pydantic import BaseModel

import config_manager
import model_scanner
from sherly_core.observability import _timelines

router = APIRouter(prefix="/api/health", tags=["health"])

_START_TIME = time.time()


class HealthResponse(BaseModel):
    status: str
    uptime_seconds: float
    model_mode: str
    current_model: str | None


class ProviderStatusResponse(BaseModel):
    ollama_running: bool
    configured_providers: list[str]


@router.get("", response_model=HealthResponse)
def get_application_health():
    """Fast, deterministic health check for process readiness."""
    cfg = config_manager.load_config()
    return HealthResponse(
        status="healthy",
        uptime_seconds=round(time.time() - _START_TIME, 2),
        model_mode=cfg.get("model_mode", "auto"),
        current_model=cfg.get("model", None),
    )


@router.get("/providers", response_model=ProviderStatusResponse)
def get_provider_health():
    """Non-blocking provider availability check without loading models."""
    cfg = config_manager.load_config()
    api_keys = cfg.get("api_keys", {})
    configured = [k for k, v in api_keys.items() if v]

    return ProviderStatusResponse(
        ollama_running=model_scanner.is_ollama_running(),
        configured_providers=configured,
    )


@router.get("/diagnostics")
def get_diagnostics() -> Dict[str, Any]:
    """Diagnostic timelines for internal debugging."""
    summaries = [t.get_summary() for t in list(_timelines.values())[-10:]]
    return {
        "recent_timelines": summaries,
    }
