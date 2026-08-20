"""
FASTAPI SERVER MAIN — backend/main.py
Main entry point for Sherly FastAPI backend API server, WebSockets, and Observability.
"""

from __future__ import annotations

import logging
import os
import sys
import uuid
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

# Ensure root project directory is on sys.path
_ROOT = str(Path(__file__).resolve().parent.parent)
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from backend.api.routes import chat, models, voice, files, actions, settings, health
from backend.api.websocket.ws_manager import manager
from sherly_core.model_resolver import resolve_model
from sherly_core.observability import (
    StructuredJsonFormatter,
    set_correlation_context,
    clear_correlation_context,
    get_or_create_timeline,
)
import config_manager
import model_scanner
import speech_to_text
import text_to_speech
import sounddevice as sd

# Configure Structured JSON Logging
_root_logger = logging.getLogger()
_root_logger.setLevel(logging.INFO)
for h in _root_logger.handlers[:]:
    _root_logger.removeHandler(h)
_ch = logging.StreamHandler(sys.stdout)
_ch.setFormatter(StructuredJsonFormatter())
_root_logger.addHandler(_ch)

logger = logging.getLogger("sherly.backend")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup phase
    logger.info("Sherly FastAPI Backend starting up...")
    try:
        resolved = resolve_model(config_manager, model_scanner)
        logger.info(f"Sherly model resolved on startup: {resolved}")
    except Exception as exc:
        logger.warning(f"Model resolution on startup warning: {exc}")

    yield

    # Shutdown phase
    logger.info("Sherly FastAPI Backend shutting down gracefully...")
    try:
        text_to_speech.stop_tts()
        sd.stop()
    except Exception as exc:
        logger.warning(f"Error releasing audio on shutdown: {exc}")


app = FastAPI(title="Sherly AI Assistant API", version="2.0.0", lifespan=lifespan)

# Correlation ID Middleware: Attaches trace_id and request_id to incoming requests
@app.middleware("http")
async def correlation_middleware(request: Request, call_next):
    trace_id = request.headers.get("x-trace-id", str(uuid.uuid4()))
    request_id = request.headers.get("x-request-id", str(uuid.uuid4())[:8])
    set_correlation_context(trace_id=trace_id, request_id=request_id)

    timeline = get_or_create_timeline(trace_id, request_id)
    timeline.record_event("request.received", {"path": request.url.path, "method": request.method})

    try:
        response = await call_next(request)
        timeline.record_event("response.sent", {"status_code": response.status_code})
        response.headers["x-trace-id"] = trace_id
        response.headers["x-request-id"] = request_id
        return response
    except Exception as exc:
        timeline.record_event("request.failed", {"error": str(exc)})
        logger.error(f"Unhandled request exception: {exc}", exc_info=True)
        return JSONResponse(status_code=500, content={"detail": "Internal server error"})
    finally:
        clear_correlation_context()

# CORS middleware for local Tauri / Vite frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173", "tauri://localhost", "http://tauri.localhost"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API Routers
app.include_router(chat.router)
app.include_router(models.router)
app.include_router(voice.router)
app.include_router(files.router)
app.include_router(actions.router)
app.include_router(settings.router)
app.include_router(health.router)


@app.get("/health")
def health_check():
    return {"status": "ok", "app": "Sherly AI Backend", "version": "2.0.0"}


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            await websocket.send_text(f'{{"event_type": "pong", "payload": {{}}}}')
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as exc:
        logger.warning(f"WebSocket error: {exc}")
        manager.disconnect(websocket)


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("SHERLY_PORT", "8000"))
    uvicorn.run(app, host="127.0.0.1", port=port)
