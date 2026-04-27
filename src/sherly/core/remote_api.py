"""
REMOTE API GATEWAY — remote_api.py
Implements:
  FS-#17  FastAPI microservice for horizontal LLM inference offloading.
           Control Nodes (laptops) route heavy inference to Compute Nodes
           (GPU desktops) via this gateway.

  Features:
    - Token-based authentication (Bearer token via env var SHERLY_API_TOKEN)
    - Rate limiting (X-RateLimit-* headers)
    - Circuit breaker on LLM calls (re-uses pybreaker from model_manager)
    - Health endpoint for Ollama up/down status
    - Streaming endpoint (/infer/stream) using Server-Sent Events
    - Session-aware routing via X-Session-Token header
"""

from __future__ import annotations

import os
import time
from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI, HTTPException, Header, Request
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel

from sherly.utils.runtime_utils import log

# ---------------------------------------------------------------------------
# Auth token — set SHERLY_API_TOKEN in .env
# ---------------------------------------------------------------------------
_API_TOKEN = os.environ.get("SHERLY_API_TOKEN", "")


def _check_auth(authorization: str | None) -> None:
    if not _API_TOKEN:
        return  # Token validation disabled when env var is unset (local dev)
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing Bearer token.")
    token = authorization.split(" ", 1)[1]
    if token != _API_TOKEN:
        raise HTTPException(status_code=401, detail="Invalid API token.")


# ---------------------------------------------------------------------------
# Request / Response schemas
# ---------------------------------------------------------------------------

class InferRequest(BaseModel):
    prompt:        str
    store_history: bool = False
    use_context:   bool = False


class InferResponse(BaseModel):
    result:  str
    latency: float
    model:   str


class HealthResponse(BaseModel):
    status:       str
    ollama_alive: bool
    active_model: str | None


# ---------------------------------------------------------------------------
# App lifecycle
# ---------------------------------------------------------------------------

@asynccontextmanager
async def _lifespan(app: FastAPI) -> AsyncIterator[None]:
    log("[RemoteAPI] Gateway starting…")
    yield
    log("[RemoteAPI] Gateway shutting down.")


app = FastAPI(
    title="Sherly AI Remote Gateway",
    description=(
        "FS-#17: Horizontal LLM inference offloading. "
        "Compute Nodes serve inference to Control Nodes via this FastAPI gateway."
    ),
    version="1.0.0",
    lifespan=_lifespan,
)


# ---------------------------------------------------------------------------
# Simple per-IP rate limiter (in-memory, resets on restart)
# ---------------------------------------------------------------------------
_rate_store: dict[str, list[float]] = {}
_RATE_WINDOW = 60   # seconds
_RATE_LIMIT  = 30   # max calls per window


def _check_rate(client_ip: str) -> tuple[int, int]:
    """
    Returns (calls_made, remaining).
    Raises HTTPException 429 when limit is exceeded.
    """
    now   = time.time()
    calls = [t for t in _rate_store.get(client_ip, []) if now - t < _RATE_WINDOW]
    if len(calls) >= _RATE_LIMIT:
        raise HTTPException(
            status_code=429,
            detail=f"Rate limit exceeded: {_RATE_LIMIT} calls per {_RATE_WINDOW}s.",
            headers={"Retry-After": str(_RATE_WINDOW)},
        )
    calls.append(now)
    _rate_store[client_ip] = calls
    return len(calls), _RATE_LIMIT - len(calls)


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@app.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    """FS-#8 / FS-#17: Combined health probe."""
    try:
        from sherly.services.model_manager import check_ollama_health, ACTIVE_MODEL
        alive = check_ollama_health()
        model = ACTIVE_MODEL
    except Exception:
        alive = False
        model = None

    return HealthResponse(
        status="ok" if alive else "degraded",
        ollama_alive=alive,
        active_model=model,
    )


@app.post("/infer", response_model=InferResponse)
async def infer(
    body: InferRequest,
    request: Request,
    authorization: str | None = Header(default=None),
    x_session_token: str | None = Header(default=None),
) -> InferResponse:
    """
    FS-#17: Synchronous inference endpoint.
    Delegates to ask_model() on the Compute Node.
    """
    _check_auth(authorization)
    client_ip = request.client.host if request.client else "unknown"
    made, remaining = _check_rate(client_ip)

    # Optional: session-aware routing
    if x_session_token:
        try:
            from sherly.core.session_manager import get_session_manager
            ctx = get_session_manager().get_or_create(x_session_token)
            log(f"[RemoteAPI] Session {x_session_token[:12]} — mode={ctx.mode}")
        except Exception:
            pass

    t0 = time.perf_counter()
    try:
        from sherly.services.model_manager import ask_model, get_current_model
        result  = ask_model(
            body.prompt,
            store_history=body.store_history,
            use_context=body.use_context,
        )
        latency = time.perf_counter() - t0
        model   = get_current_model()
    except Exception as exc:
        log(f"[RemoteAPI] Inference error: {exc}", level="error")
        raise HTTPException(status_code=500, detail=f"Inference failed: {exc}")

    response = JSONResponse(
        content=InferResponse(result=result, latency=round(latency, 3), model=model).model_dump(),
        headers={
            "X-RateLimit-Limit":     str(_RATE_LIMIT),
            "X-RateLimit-Remaining": str(remaining),
        },
    )
    return response


@app.post("/infer/stream")
async def infer_stream(
    body: InferRequest,
    request: Request,
    authorization: str | None = Header(default=None),
) -> StreamingResponse:
    """
    FS-#17 / RC-8: Server-Sent Events streaming endpoint.
    Yields token chunks from stream_model() as they arrive.
    """
    _check_auth(authorization)
    _check_rate(request.client.host if request.client else "unknown")

    async def _event_stream() -> AsyncIterator[str]:
        try:
            from sherly.services.model_manager import stream_model
            for chunk in stream_model(
                body.prompt,
                store_history=body.store_history,
            ):
                yield f"data: {chunk}\n\n"
            yield "data: [DONE]\n\n"
        except Exception as exc:
            yield f"data: [ERROR] {exc}\n\n"

    return StreamingResponse(
        _event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control":     "no-cache",
            "X-Accel-Buffering": "no",
        },
    )


@app.get("/sessions")
async def list_sessions(
    authorization: str | None = Header(default=None),
) -> dict:
    """FS-#15 / FS-#17: List all active sessions (admin endpoint)."""
    _check_auth(authorization)
    try:
        from sherly.core.session_manager import get_session_manager
        mgr = get_session_manager()
        return {"active": mgr.active_count(), "sessions": mgr.list_sessions()}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


# ---------------------------------------------------------------------------
# Standalone entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "sherly.core.remote_api:app",
        host="0.0.0.0",
        port=int(os.environ.get("SHERLY_GATEWAY_PORT", "8080")),
        reload=False,
        log_level="info",
    )
