"""
WEBSOCKET MANAGER — backend/api/websocket/ws_manager.py
Manages real-time WebSocket connections to broadcast assistant status updates,
speech transcription text, task progress, and pending approvals.
"""

from __future__ import annotations

import json
import logging
import time
from typing import Any

from fastapi import WebSocket

logger = logging.getLogger(__name__)


class ConnectionManager:
    def __init__(self) -> None:
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket) -> None:
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"WebSocket client connected. Total clients: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket) -> None:
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
            logger.info(f"WebSocket client disconnected. Total clients: {len(self.active_connections)}")

    async def broadcast_event(
        self,
        event_type: str,
        payload: dict[str, Any],
        request_id: str | None = None,
    ) -> None:
        envelope = {
            "event_type": event_type,
            "payload": payload,
            "timestamp": time.time(),
        }
        if request_id:
            envelope["request_id"] = request_id

        try:
            data = json.dumps(envelope, default=str)
        except Exception as exc:
            logger.error("Failed to serialize WebSocket payload for %s: %s", event_type, exc)
            return

        disconnected = []
        for connection in list(self.active_connections):  # copy to avoid mutation during iteration
            try:
                await connection.send_text(data)
            except Exception as exc:
                logger.warning(f"Error sending WebSocket message: {exc}")
                disconnected.append(connection)

        for conn in disconnected:
            self.disconnect(conn)


manager = ConnectionManager()
