"""
WEBSOCKET MANAGER — backend/api/websocket/ws_manager.py
Manages real-time WebSocket connections to broadcast assistant status updates,
speech transcription text, task progress, and pending approvals.
"""

from __future__ import annotations

import json
import logging
from typing import Any
from fastapi import WebSocket, WebSocketDisconnect

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

    async def broadcast_event(self, event_type: str, payload: dict[str, Any]) -> None:
        data = json.dumps({"event_type": event_type, "payload": payload})
        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_text(data)
            except Exception as exc:
                logger.warning(f"Error sending WebSocket message: {exc}")
                disconnected.append(connection)

        for conn in disconnected:
            self.disconnect(conn)


manager = ConnectionManager()
