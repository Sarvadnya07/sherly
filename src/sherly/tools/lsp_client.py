"""
LSP CLIENT — lsp_client.py
Implements:
  FS-#13  Language Server Protocol integration via pylsp.
           Sherly's coder_agent can query any LSP-compliant language server
           for real-time diagnostics, hover info, completions, and go-to-definition.

  Supported LSP operations:
    - initialize()     — Handshake with the server process
    - diagnostics()    — Get syntax/type errors for a file
    - hover()          — Get type info for a symbol at (line, col)
    - completions()    — Get autocomplete suggestions
    - definition()     — Get the definition location of a symbol
    - shutdown()       — Clean server teardown

  Supported servers (auto-detected):
    Python → pylsp   (pip install python-lsp-server)
    JS/TS  → typescript-language-server
    Rust   → rust-analyzer
    Go     → gopls
"""

from __future__ import annotations

import json
import os
import subprocess
import threading
import time
from pathlib import Path
from typing import Any

from sherly.utils.runtime_utils import log


# ---------------------------------------------------------------------------
# Server auto-detection
# ---------------------------------------------------------------------------

_LSP_SERVERS: dict[str, list[str]] = {
    ".py":   ["pylsp"],
    ".js":   ["typescript-language-server", "--stdio"],
    ".ts":   ["typescript-language-server", "--stdio"],
    ".tsx":  ["typescript-language-server", "--stdio"],
    ".rs":   ["rust-analyzer"],
    ".go":   ["gopls"],
    ".java": ["jdtls"],
}


def _detect_server(file_ext: str) -> list[str] | None:
    """Return the LSP server command for a given file extension, or None."""
    return _LSP_SERVERS.get(file_ext.lower())


# ---------------------------------------------------------------------------
# JSON-RPC helpers
# ---------------------------------------------------------------------------

def _encode_message(payload: dict) -> bytes:
    body  = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    header = f"Content-Length: {len(body)}\r\n\r\n".encode("ascii")
    return header + body


def _read_message(stream) -> dict | None:
    """Read one JSON-RPC message from *stream* (stdout of the LSP server)."""
    headers: dict[str, str] = {}
    while True:
        line = stream.readline()
        if not line:
            return None
        line = line.decode("utf-8").strip()
        if not line:
            break
        if ":" in line:
            k, _, v = line.partition(":")
            headers[k.strip().lower()] = v.strip()

    length = int(headers.get("content-length", 0))
    if not length:
        return None
    body = stream.read(length)
    return json.loads(body.decode("utf-8"))


# ---------------------------------------------------------------------------
# LSPClient
# ---------------------------------------------------------------------------

class LSPClient:
    """
    FS-#13: Thin JSON-RPC client for Language Server Protocol servers.

    Starts the server as a subprocess, sends/receives JSON-RPC over stdio.
    All operations are synchronous (blocking) for simplicity — suitable for
    on-demand code analysis, not interactive editors.
    """

    def __init__(self, root_path: str) -> None:
        self.root_path   = str(Path(root_path).resolve())
        self._proc:       subprocess.Popen | None = None
        self._msg_id      = 0
        self._lock        = threading.Lock()
        self._initialized = False

    def _next_id(self) -> int:
        with self._lock:
            self._msg_id += 1
            return self._msg_id

    def _send(self, method: str, params: dict) -> int:
        msg_id = self._next_id()
        payload = {
            "jsonrpc": "2.0",
            "id":      msg_id,
            "method":  method,
            "params":  params,
        }
        assert self._proc and self._proc.stdin
        self._proc.stdin.write(_encode_message(payload))
        self._proc.stdin.flush()
        return msg_id

    def _recv(self) -> dict | None:
        assert self._proc
        return _read_message(self._proc.stdout)

    def _request(self, method: str, params: dict) -> dict | None:
        """Send a request and block until the matching response arrives."""
        msg_id = self._send(method, params)
        deadline = time.time() + 10.0
        while time.time() < deadline:
            msg = self._recv()
            if msg is None:
                break
            if msg.get("id") == msg_id:
                return msg
        return None

    def _notify(self, method: str, params: dict) -> None:
        """Send a notification (no response expected)."""
        payload = {"jsonrpc": "2.0", "method": method, "params": params}
        assert self._proc and self._proc.stdin
        self._proc.stdin.write(_encode_message(payload))
        self._proc.stdin.flush()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def start(self, server_cmd: list[str]) -> bool:
        """
        FS-#13: Start the LSP server process and perform the initialize handshake.
        Returns True on success.
        """
        try:
            self._proc = subprocess.Popen(
                server_cmd,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL,
            )
        except FileNotFoundError:
            log(
                f"[LSP] Server not found: {server_cmd[0]}. "
                f"Install with: pip install {server_cmd[0]}",
                level="warning",
            )
            return False

        resp = self._request("initialize", {
            "processId": os.getpid(),
            "rootUri":   f"file://{self.root_path}",
            "capabilities": {
                "textDocument": {
                    "hover":       {"contentFormat": ["plaintext"]},
                    "completion":  {"completionItem": {"snippetSupport": False}},
                    "publishDiagnostics": {},
                },
            },
            "initializationOptions": {},
        })
        if resp and "result" in resp:
            self._notify("initialized", {})
            self._initialized = True
            log("[LSP] Server initialized ✓")
            return True

        log("[LSP] Initialize handshake failed.", level="error")
        return False

    def start_for_file(self, file_path: str) -> bool:
        """Auto-detect the correct LSP server for *file_path* and start it."""
        ext = Path(file_path).suffix
        cmd = _detect_server(ext)
        if not cmd:
            log(f"[LSP] No server registered for extension: {ext}", level="warning")
            return False
        return self.start(cmd)

    def open_file(self, file_path: str) -> None:
        """Notify the server that a file is now open (required before queries)."""
        content = Path(file_path).read_text(encoding="utf-8", errors="ignore")
        self._notify("textDocument/didOpen", {
            "textDocument": {
                "uri":        f"file://{Path(file_path).resolve()}",
                "languageId": _lang_id(file_path),
                "version":    1,
                "text":       content,
            }
        })

    def diagnostics(self, file_path: str) -> list[dict[str, Any]]:
        """
        FS-#13: Collect diagnostics (errors / warnings) for *file_path*.
        Returns a list of LSP Diagnostic objects.
        """
        if not self._initialized:
            return []
        self.open_file(file_path)
        # LSP sends diagnostics as a notification; wait briefly for it
        deadline = time.time() + 5.0
        while time.time() < deadline:
            msg = self._recv()
            if msg and msg.get("method") == "textDocument/publishDiagnostics":
                return msg.get("params", {}).get("diagnostics", [])
        return []

    def hover(self, file_path: str, line: int, col: int) -> str:
        """
        FS-#13: Get hover documentation for the symbol at (line, col).
        Lines and columns are 0-indexed (LSP convention).
        """
        if not self._initialized:
            return ""
        resp = self._request("textDocument/hover", {
            "textDocument": {"uri": f"file://{Path(file_path).resolve()}"},
            "position":     {"line": line, "character": col},
        })
        if resp and "result" in resp and resp["result"]:
            content = resp["result"].get("contents", {})
            if isinstance(content, dict):
                return content.get("value", "")
            if isinstance(content, str):
                return content
        return ""

    def completions(self, file_path: str, line: int, col: int) -> list[str]:
        """
        FS-#13: Get completion candidates at (line, col).
        Returns a list of completion label strings.
        """
        if not self._initialized:
            return []
        resp = self._request("textDocument/completion", {
            "textDocument": {"uri": f"file://{Path(file_path).resolve()}"},
            "position":     {"line": line, "character": col},
        })
        if not resp or "result" not in resp:
            return []
        result = resp["result"]
        items  = result if isinstance(result, list) else result.get("items", [])
        return [item.get("label", "") for item in items[:20]]

    def definition(self, file_path: str, line: int, col: int) -> dict | None:
        """
        FS-#13: Go-to-definition for the symbol at (line, col).
        Returns {"file": path, "line": int, "col": int} or None.
        """
        if not self._initialized:
            return None
        resp = self._request("textDocument/definition", {
            "textDocument": {"uri": f"file://{Path(file_path).resolve()}"},
            "position":     {"line": line, "character": col},
        })
        if not resp or "result" not in resp or not resp["result"]:
            return None
        loc = resp["result"]
        if isinstance(loc, list):
            loc = loc[0]
        uri   = loc.get("uri", "").replace("file://", "")
        start = loc.get("range", {}).get("start", {})
        return {"file": uri, "line": start.get("line", 0), "col": start.get("character", 0)}

    def shutdown(self) -> None:
        """Clean server teardown per LSP spec."""
        if self._initialized:
            try:
                self._request("shutdown", {})
                self._notify("exit", {})
            except Exception:
                pass
        if self._proc:
            try:
                self._proc.terminate()
                self._proc.wait(timeout=3)
            except Exception:
                pass
        self._initialized = False
        log("[LSP] Server shut down.")

    def __enter__(self) -> "LSPClient":
        return self

    def __exit__(self, *_) -> None:
        self.shutdown()


def _lang_id(file_path: str) -> str:
    """Map file extension to LSP languageId string."""
    return {
        ".py":  "python",
        ".js":  "javascript",
        ".ts":  "typescript",
        ".tsx": "typescriptreact",
        ".rs":  "rust",
        ".go":  "go",
    }.get(Path(file_path).suffix.lower(), "plaintext")


# ---------------------------------------------------------------------------
# Convenience wrapper — used by coder_agent
# ---------------------------------------------------------------------------

def analyze_file_with_lsp(file_path: str, root_path: str | None = None) -> str:
    """
    FS-#13: One-shot diagnostic report for *file_path*.
    Returns a human-readable string of errors and warnings,
    or "No issues found." if the LSP server reports no diagnostics.
    """
    root = root_path or str(Path(file_path).parent)
    client = LSPClient(root)

    if not client.start_for_file(file_path):
        return (
            f"[LSP] Could not start a language server for {file_path}. "
            "Install pylsp: pip install python-lsp-server"
        )

    try:
        client.open_file(file_path)
        diags = client.diagnostics(file_path)
        if not diags:
            return "No issues found."
        lines = [f"[LSP] {len(diags)} diagnostic(s) in {Path(file_path).name}:"]
        for d in diags:
            severity = {1: "ERROR", 2: "WARNING", 3: "INFO", 4: "HINT"}.get(
                d.get("severity", 3), "INFO"
            )
            start = d.get("range", {}).get("start", {})
            lines.append(
                f"  [{severity}] L{start.get('line', 0)+1}:{start.get('character', 0)+1} "
                f"— {d.get('message', '')}"
            )
        return "\n".join(lines)
    finally:
        client.shutdown()
