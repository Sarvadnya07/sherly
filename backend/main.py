"""
FASTAPI SERVER MAIN — backend/main.py
Main entry point for Sherly FastAPI backend API server and WebSockets.
"""

from __future__ import annotations

import logging
import os
import sys
from pathlib import Path

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

# Ensure root project directory is on sys.path
_ROOT = str(Path(__file__).resolve().parent.parent)
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from backend.api.routes import chat, models, voice, files, actions, settings
from backend.api.websocket.ws_manager import manager
from model_scanner import scan_ollama_models
from sherly_core.model_resolver import resolve_model
import config_manager
import model_scanner

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("sherly.backend")

app = FastAPI(title="Sherly AI Assistant API", version="2.0.0")

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


@app.on_event("startup")
async def startup_event():
    logger.info("Sherly FastAPI Backend starting up...")
    resolved = resolve_model(config_manager, model_scanner)
    logger.info(f"Sherly model resolved on startup: {resolved}")


@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Sherly FastAPI Backend shutting down...")


@app.get("/health")
def health_check():
    return {"status": "ok", "app": "Sherly AI Backend", "version": "2.0.0"}


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            # Echo or process client ping/messages if needed
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
