"""
MEMORY — memory.py
Fixes:
  - Thread-safety: all DB operations protected by a single mutex.
  - WAL mode: enables concurrent reads without blocking writers.
  - Lazy connection: deferred until first use to avoid import-time side effects.
"""
from __future__ import annotations

import sqlite3
import threading

# ---------------------------------------------------------------------------
# Thread-safe connection
# ---------------------------------------------------------------------------
_db_lock: threading.Lock = threading.Lock()
_conn: sqlite3.Connection | None = None


def _get_conn() -> sqlite3.Connection:
    global _conn
    if _conn is None:
        _conn = sqlite3.connect("sherly_memory.db", check_same_thread=False)
        _conn.execute("PRAGMA journal_mode=WAL")   # concurrent reads
        _conn.execute("PRAGMA synchronous=NORMAL")
        _conn.execute(
            "CREATE TABLE IF NOT EXISTS memory "
            "(key TEXT UNIQUE, value TEXT)"
        )
        _conn.execute(
            "CREATE TABLE IF NOT EXISTS chat_history "
            "(id INTEGER PRIMARY KEY, user TEXT, assistant TEXT)"
        )
        _conn.commit()
    return _conn


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def add_memory(user_text: str, assistant_text: str) -> None:
    """Persist each exchange so future prompts can reference recent context."""
    with _db_lock:
        conn = _get_conn()
        conn.execute(
            "INSERT INTO chat_history (user, assistant) VALUES (?, ?)",
            (user_text, assistant_text),
        )
        conn.commit()


def get_context(limit: int = 5) -> str:
    """Return the last few exchanges formatted for prompt injection."""
    with _db_lock:
        conn = _get_conn()
        cursor = conn.execute(
            "SELECT user, assistant FROM chat_history ORDER BY id DESC LIMIT ?",
            (limit,),
        )
        rows = cursor.fetchall()[::-1]

    history = ""
    for user, assistant in rows:
        history += f"User: {user}\nAssistant: {assistant}\n"
    return history.strip()


def save_memory(key: str, value: str) -> None:
    """Store persistent key/value data (settings, etc.)."""
    with _db_lock:
        conn = _get_conn()
        conn.execute(
            "INSERT OR REPLACE INTO memory (key, value) VALUES (?, ?)",
            (key, str(value)),
        )
        conn.commit()


def get_memory(key: str) -> str | None:
    """Retrieve a stored setting by key."""
    with _db_lock:
        conn = _get_conn()
        cursor = conn.execute(
            "SELECT value FROM memory WHERE key=?", (key,)
        )
        result = cursor.fetchone()
    return result[0] if result else None
