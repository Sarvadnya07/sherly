"""
CLOUD RELAY SERVER — cloud_relay.py
Implements:
  FS-#14  Self-hostable Sherly Cloud Relay.
           Bridges a remote mobile/browser client to a local Sherly daemon
           over an encrypted WebSocket. No payload is stored on the relay.

  Architecture:
    [Mobile Client]  ←—WebSocket—→  [Relay Server]  ←—WebSocket—→  [Local Daemon]
                        encrypted                    local network

  The relay is a pure passthrough — it only routes JSON frames between the
  two WebSocket connections. All application logic stays in the daemon.

  Security:
    - Client must present a valid SHERLY_RELAY_TOKEN as Bearer in the handshake.
    - All frames are forwarded verbatim; the relay never reads payload contents.
    - TLS is handled by the reverse proxy (nginx/caddy) in production.

  Usage:
    # Start the relay (on a cloud VM or home server):
    SHERLY_RELAY_TOKEN=<secret> python -m sherly.core.cloud_relay

    # Connect the daemon to the relay:
    SHERLY_RELAY_URL=wss://relay.example.com/daemon \
    SHERLY_RELAY_TOKEN=<secret> python -m sherly.core.cloud_relay --mode daemon

    # Mobile/browser client connects to:
    wss://relay.example.com/client
"""

from __future__ import annotations

import asyncio
import json
import os
import time
from typing import Any

from sherly.utils.runtime_utils import log

# FS-#24: Heavy imports are lazy
_websockets_available: bool | None = None


def _require_websockets():
    global _websockets_available
    if _websockets_available is None:
        try:
            import websockets  # noqa: F401
            _websockets_available = True
        except ImportError:
            _websockets_available = False
    if not _websockets_available:
        raise ImportError(
            "websockets not installed. Run: pip install websockets"
        )


# ---------------------------------------------------------------------------
# Relay state
# ---------------------------------------------------------------------------

_RELAY_TOKEN = os.environ.get("SHERLY_RELAY_TOKEN", "")
_DEFAULT_HOST = "0.0.0.0"
_DEFAULT_PORT = int(os.environ.get("SHERLY_RELAY_PORT", "8765"))

# Connected daemon WebSocket (only one daemon per relay instance)
_daemon_ws: Any = None
# Connected client WebSockets (many clients can connect)
_client_ws_set: set = set()
_relay_lock = asyncio.Lock()


def _auth_ok(headers) -> bool:
    """Check Bearer token from WebSocket handshake headers."""
    if not _RELAY_TOKEN:
        return True  # No token configured → open relay (dev mode)
    auth = headers.get("Authorization", "")
    return auth == f"Bearer {_RELAY_TOKEN}"


# ---------------------------------------------------------------------------
# WebSocket handlers
# ---------------------------------------------------------------------------

async def _daemon_handler(websocket) -> None:
    """Handle the incoming connection from the local Sherly daemon."""
    global _daemon_ws

    if not _auth_ok(websocket.request_headers):
        await websocket.close(code=4001, reason="Unauthorized")
        log("[Relay] Daemon connection rejected: invalid token.", level="warning")
        return

    async with _relay_lock:
        _daemon_ws = websocket
    log(f"[Relay] Daemon connected from {websocket.remote_address}")

    try:
        async for raw_msg in websocket:
            # Forward daemon messages to ALL connected clients
            if _client_ws_set:
                dead = set()
                for client in list(_client_ws_set):
                    try:
                        await client.send(raw_msg)
                    except Exception:
                        dead.add(client)
                _client_ws_set.difference_update(dead)
    except Exception as exc:
        log(f"[Relay] Daemon connection error: {exc}", level="error")
    finally:
        async with _relay_lock:
            _daemon_ws = None
        log("[Relay] Daemon disconnected.")


async def _client_handler(websocket) -> None:
    """Handle incoming connection from a remote client (mobile / browser)."""
    if not _auth_ok(websocket.request_headers):
        await websocket.close(code=4001, reason="Unauthorized")
        log("[Relay] Client connection rejected: invalid token.", level="warning")
        return

    _client_ws_set.add(websocket)
    log(f"[Relay] Client connected: {websocket.remote_address}. Total clients: {len(_client_ws_set)}")

    try:
        async for raw_msg in websocket:
            # Forward client messages to the daemon
            if _daemon_ws:
                try:
                    await _daemon_ws.send(raw_msg)
                except Exception as exc:
                    log(f"[Relay] Failed to forward to daemon: {exc}", level="error")
            else:
                await websocket.send(json.dumps({
                    "error": "Daemon not connected. Start Sherly locally first."
                }))
    except Exception as exc:
        log(f"[Relay] Client connection error: {exc}", level="error")
    finally:
        _client_ws_set.discard(websocket)
        log(f"[Relay] Client disconnected. Remaining: {len(_client_ws_set)}")


async def _router(websocket) -> None:
    """Route connections to daemon or client handler based on path."""
    path = getattr(websocket, "path", "") or ""
    if path.startswith("/daemon"):
        await _daemon_handler(websocket)
    else:
        await _client_handler(websocket)


# ---------------------------------------------------------------------------
# Daemon-side client (connects local Sherly to a remote relay)
# ---------------------------------------------------------------------------

async def _run_daemon_client(relay_url: str, command_callback) -> None:
    """
    FS-#14: Connect the local Sherly daemon to a remote relay server.
    Reads commands from the relay and routes them through command_callback.
    """
    import websockets
    headers = {"Authorization": f"Bearer {_RELAY_TOKEN}"}

    while True:
        try:
            log(f"[Relay/Daemon] Connecting to relay: {relay_url}")
            async with websockets.connect(relay_url, extra_headers=headers) as ws:
                log("[Relay/Daemon] Connected to relay ✓")
                async for raw_msg in ws:
                    try:
                        frame = json.loads(raw_msg)
                        cmd   = frame.get("command", "")
                        if cmd:
                            result = command_callback(cmd)
                            await ws.send(json.dumps({"result": result}))
                    except Exception as exc:
                        log(f"[Relay/Daemon] Frame error: {exc}", level="error")
        except Exception as exc:
            log(f"[Relay/Daemon] Disconnected ({exc}). Reconnecting in 5s…", level="warning")
            await asyncio.sleep(5)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

async def start_relay_server(
    host: str = _DEFAULT_HOST,
    port: int = _DEFAULT_PORT,
) -> None:
    """
    FS-#14: Start the relay WebSocket server.
    Use this from an asyncio event loop.
    """
    _require_websockets()
    import websockets

    log(f"[Relay] Starting on ws://{host}:{port}")
    log(f"[Relay] Token auth: {'enabled' if _RELAY_TOKEN else 'DISABLED (dev mode)'}")

    async with websockets.serve(_router, host, port):
        log("[Relay] Listening — daemon path: /daemon, client path: /client")
        await asyncio.Future()   # Run forever


def run_relay(host: str = _DEFAULT_HOST, port: int = _DEFAULT_PORT) -> None:
    """Synchronous entry point for running the relay server."""
    asyncio.run(start_relay_server(host, port))


def connect_daemon_to_relay(relay_url: str, command_callback=None) -> None:
    """
    FS-#14: Connect this Sherly daemon to a remote relay server.
    Runs the WebSocket client in a background thread.
    """
    _require_websockets()
    import threading

    if command_callback is None:
        from sherly.services.command_router import route_command
        command_callback = route_command

    def _thread():
        asyncio.run(_run_daemon_client(relay_url, command_callback))

    t = threading.Thread(target=_thread, daemon=True, name="RelayClient")
    t.start()
    log(f"[Relay] Daemon client thread started → {relay_url}")


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Sherly Cloud Relay Server")
    parser.add_argument(
        "--mode",
        choices=["server", "daemon"],
        default="server",
        help="'server' = run the relay; 'daemon' = connect local Sherly to a relay",
    )
    parser.add_argument("--url", default=os.environ.get("SHERLY_RELAY_URL", ""))
    parser.add_argument("--host", default=_DEFAULT_HOST)
    parser.add_argument("--port", type=int, default=_DEFAULT_PORT)
    args = parser.parse_args()

    if args.mode == "daemon":
        if not args.url:
            print("❌ --url is required in daemon mode (e.g. wss://relay.example.com/daemon)")
        else:
            connect_daemon_to_relay(args.url)
            import time
            try:
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                pass
    else:
        run_relay(args.host, args.port)
