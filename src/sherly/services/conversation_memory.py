"""
CONVERSATION MEMORY — conversation_memory.py
Fixes: #7  context drift (strict 5-turn cap, topic-change reset)
        #19 multi-user collision hook (session_id parameter)
"""

from __future__ import annotations

import threading

_MAX_TURNS = 5   # Fix #7: never send more than 5 turns to LLM

# Fix #5: lock for thread-safe appends
_lock = threading.Lock()

# Fix #19: per-session storage (default session = "default")
_sessions: dict[str, list[dict]] = {}


def _get_session(session_id: str) -> list[dict]:
    if session_id not in _sessions:
        _sessions[session_id] = []
    return _sessions[session_id]


def add_to_memory(user: str, assistant: str, session_id: str = "default") -> None:
    with _lock:
        session = _get_session(session_id)
        session.append({"user": user, "assistant": assistant})
        # Fix #7: keep only last _MAX_TURNS turns in memory
        if len(session) > _MAX_TURNS:
            _sessions[session_id] = session[-_MAX_TURNS:]


def clear_context(session_id: str = "default") -> None:
    """Fix #7: reset context on new topic (call this when topic changes)."""
    with _lock:
        _sessions[session_id] = []


def build_prompt(user_input: str, session_id: str = "default") -> str:
    with _lock:
        session = list(_get_session(session_id))   # snapshot under lock

    history = ""
    for entry in session[-_MAX_TURNS:]:
        history += f"User: {entry['user']}\nAssistant: {entry['assistant']}\n"
    return history + f"User: {user_input}"
