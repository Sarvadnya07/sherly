"""
MEMORY BRAIN — memory_brain.py
Fixes: #12 memory file corruption (atomic write via tempfile + replace)
        #17 timezone issues (UTC timestamps on all entries)
"""

from __future__ import annotations

import json
import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path

MEMORY_FILE = Path("memory.json")


# ---------------------------------------------------------------------------
# Fix #12 – atomic save (write to tmp, then rename → never leaves corrupt JSON)
# ---------------------------------------------------------------------------

def load_memory() -> dict:
    if not MEMORY_FILE.exists():
        return {}
    try:
        with MEMORY_FILE.open("r", encoding="utf-8") as f:
            data = json.load(f)
            return data if isinstance(data, dict) else {}
    except (json.JSONDecodeError, OSError):
        # File is corrupt → return empty and let next save recover it
        return {}


def save_memory(mem: dict) -> None:
    """
    Fix #12: atomic write.
    Write to a temp file in the same directory, then os.replace()
    so a crash mid-write never corrupts the live file.
    """
    dir_ = MEMORY_FILE.parent
    try:
        fd, tmp_path = tempfile.mkstemp(dir=dir_, suffix=".json.tmp", text=True)
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(mem, f, indent=2, ensure_ascii=False)
        os.replace(tmp_path, MEMORY_FILE)   # atomic on POSIX; near-atomic on Windows
    except Exception as exc:
        print(f"[MemoryBrain] save error: {exc}")
        # Clean up orphan temp file if it exists
        try:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)
        except Exception:
            pass


def remember(key: str, value: str) -> str:
    mem = load_memory()
    mem[key] = {
        "value": value,
        "updated_at": datetime.now(timezone.utc).isoformat(),  # Fix #17
    }
    save_memory(mem)
    return f"I will remember that {key} is {value}"


def recall(key: str) -> str:
    mem = load_memory()
    entry = mem.get(key)
    if entry is None:
        return "I don't know that yet."
    # Support both legacy plain-string values and new dict entries
    if isinstance(entry, dict):
        return entry.get("value", "I don't know that yet.")
    return str(entry)
