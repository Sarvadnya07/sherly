"""
GHOST MODE — ghost_mode.py
Fixes:
  RC-9   Port now read from config.json (ghost_mode_port, default 5555).
          Specific "port in use" error message instead of silent failure.
  OE-1   GhostModeServer can now be launched directly via main.py --headless.
"""

from __future__ import annotations

import json
import socket
import threading

from sherly.utils.runtime_utils import log


def _get_ghost_port() -> int:
    """RC-9: Read port from config, fall back to 5555."""
    try:
        from sherly.config.config_manager import get_ghost_mode_port
        return get_ghost_mode_port()
    except Exception:
        return 5555


class GhostModeServer:
    """
    IDE 'Ghost' Mode Server.
    Communicates with IDE plugins via a local TCP socket (default port 5555)
    to provide Zero-UI assistance.

    RC-9: Port is now configurable via config.json → ghost_mode_port.
    """

    def __init__(self, port: int | None = None, command_callback=None):
        self.port             = port if port is not None else _get_ghost_port()
        self.running          = False
        self.command_callback = command_callback

    def start(self) -> None:
        if self.running:
            return
        self.running = True
        thread = threading.Thread(
            target=self._run_server,
            daemon=True,
            name="GhostModeServer",
        )
        thread.start()
        log(f"[Ghost] Server started on port {self.port}")

    def _run_server(self) -> None:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                # RC-9: explicit bind error with actionable message
                try:
                    s.bind(("localhost", self.port))
                except OSError as bind_err:
                    log(
                        f"[Ghost] FAILED to bind on port {self.port}: {bind_err}. "
                        f"Set 'ghost_mode_port' in config.json to use a different port.",
                        level="error",
                    )
                    print(
                        f"❌ Ghost Mode failed: port {self.port} is already in use.\n"
                        f"   Fix: set 'ghost_mode_port' in src/sherly/config/config.json."
                    )
                    self.running = False
                    return

                s.listen(5)
                s.settimeout(1.0)
                log(f"[Ghost] Listening on localhost:{self.port}")

                while self.running:
                    try:
                        conn, addr = s.accept()
                        with conn:
                            data = conn.recv(4096)
                            if data:
                                try:
                                    request      = json.loads(data.decode())
                                    cmd          = request.get("command")
                                    log(f"[Ghost] Received from IDE: {cmd}")

                                    response_text = "No callback registered."
                                    if self.command_callback:
                                        response_text = self.command_callback(cmd)

                                    response = {"status": "ok", "message": response_text}
                                    conn.sendall(json.dumps(response).encode())
                                except json.JSONDecodeError:
                                    conn.sendall(
                                        json.dumps({"status": "error", "message": "Invalid JSON"}).encode()
                                    )
                    except socket.timeout:
                        continue

            except Exception as exc:
                log(f"[Ghost] Server error: {exc}", level="error")
                self.running = False

    def stop(self) -> None:
        self.running = False


# ---------------------------------------------------------------------------
# OE-1 — Headless entry point (used by main.py --headless)
# ---------------------------------------------------------------------------

def run_headless(command_callback=None) -> None:
    """
    OE-1: Start Sherly in headless Ghost Mode (no Qt).
    Called by main.py when launched with --headless.
    """
    from sherly.services.command_router import route_command

    callback = command_callback or route_command
    server   = GhostModeServer(command_callback=callback)
    server.start()

    port = server.port
    print(f"✅ Sherly Ghost Mode running on localhost:{port}")
    print("   Send JSON commands: {{\"command\": \"your text here\"}}")
    print("   Press Ctrl+C to exit.")

    try:
        import time
        while server.running:
            time.sleep(0.5)
    except KeyboardInterrupt:
        server.stop()
        print("\nSherly Ghost Mode stopped.")
