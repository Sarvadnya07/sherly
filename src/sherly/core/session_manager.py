"""
SESSION MANAGER — session_manager.py
Implements:
  FS-#15  Multi-User Session Support.
           Each session token carries isolated state:
             - mode (fast | deep | dev)
             - phase (A | B | C)
             - pending actions dict
             - conversation context
           A TTL-based cleanup loop evicts stale sessions.
           SessionContext is a drop-in extension of the global router state.
"""

from __future__ import annotations

import threading
import time
import uuid
from dataclasses import dataclass, field
from typing import Any

from sherly.utils.runtime_utils import log


# ---------------------------------------------------------------------------
# Session lifetime
# ---------------------------------------------------------------------------
SESSION_TTL_SECONDS = 3600   # 1 hour of inactivity expires a session
_CLEANUP_INTERVAL   = 300    # Run GC every 5 minutes


@dataclass
class SessionContext:
    """
    FS-#15: Per-session isolated state.

    Every user (or API client) gets their own SessionContext so that
    mode changes, phase flags, pending approvals, and conversation history
    are never shared across sessions.
    """
    session_id:      str             = field(default_factory=lambda: str(uuid.uuid4()))
    mode:            str             = "fast"   # fast | deep | dev
    phase:           str             = "A"      # A | B | C
    pending_actions: dict[str, Any]  = field(default_factory=dict)
    last_active:     float           = field(default_factory=time.time)
    metadata:        dict[str, Any]  = field(default_factory=dict)

    def touch(self) -> None:
        """Update last-active timestamp on every interaction."""
        self.last_active = time.time()

    def is_expired(self) -> bool:
        return (time.time() - self.last_active) > SESSION_TTL_SECONDS

    def to_dict(self) -> dict[str, Any]:
        return {
            "session_id":   self.session_id,
            "mode":         self.mode,
            "phase":        self.phase,
            "pending":      len(self.pending_actions),
            "last_active":  self.last_active,
        }


# ---------------------------------------------------------------------------
# Session Manager (singleton)
# ---------------------------------------------------------------------------

class SessionManager:
    """
    FS-#15: Central registry for all active sessions.

    Usage:
        mgr = get_session_manager()

        # Create or retrieve
        ctx = mgr.get_or_create("user_token_abc")

        # Route with session context
        ctx.touch()
        result = route_command(user_input, session=ctx)

        # Destroy
        mgr.destroy("user_token_abc")
    """

    def __init__(self) -> None:
        self._sessions: dict[str, SessionContext] = {}
        self._lock     = threading.Lock()
        self._start_gc()

    def get_or_create(self, token: str) -> SessionContext:
        """
        Return the existing session for *token*, or create a new one.
        Touches the session on every call.
        """
        with self._lock:
            if token not in self._sessions:
                ctx = SessionContext(session_id=token)
                self._sessions[token] = ctx
                log(f"[Session] Created: {token[:16]}…")
            else:
                ctx = self._sessions[token]
            ctx.touch()
            return ctx

    def get(self, token: str) -> SessionContext | None:
        """Return an existing session, or None if not found / expired."""
        with self._lock:
            ctx = self._sessions.get(token)
            if ctx and ctx.is_expired():
                del self._sessions[token]
                log(f"[Session] Expired on access: {token[:16]}…")
                return None
            if ctx:
                ctx.touch()
            return ctx

    def destroy(self, token: str) -> None:
        """Explicitly terminate a session."""
        with self._lock:
            if token in self._sessions:
                del self._sessions[token]
                log(f"[Session] Destroyed: {token[:16]}…")

    def active_count(self) -> int:
        with self._lock:
            return len(self._sessions)

    def list_sessions(self) -> list[dict[str, Any]]:
        with self._lock:
            return [ctx.to_dict() for ctx in self._sessions.values()]

    # ------------------------------------------------------------------
    # Background GC
    # ------------------------------------------------------------------

    def _gc(self) -> None:
        """Remove expired sessions periodically."""
        while True:
            time.sleep(_CLEANUP_INTERVAL)
            with self._lock:
                expired = [t for t, ctx in self._sessions.items() if ctx.is_expired()]
                for t in expired:
                    del self._sessions[t]
                if expired:
                    log(f"[Session] GC evicted {len(expired)} expired session(s).")

    def _start_gc(self) -> None:
        gc_thread = threading.Thread(
            target=self._gc, daemon=True, name="SessionGC"
        )
        gc_thread.start()


# ---------------------------------------------------------------------------
# Module-level singleton
# ---------------------------------------------------------------------------

_manager: SessionManager | None = None
_manager_lock = threading.Lock()


def get_session_manager() -> SessionManager:
    """Return the module-level SessionManager singleton."""
    global _manager
    with _manager_lock:
        if _manager is None:
            _manager = SessionManager()
    return _manager


def new_session_token() -> str:
    """Generate a fresh, unique session token."""
    return str(uuid.uuid4())
