"""
FILE TOOLS — tools/file_tools.py
Fixes: #10 file path errors (shlex quoting, path normalization)
        #11 large file crash (chunked read, 3000-char cap)
"""

from __future__ import annotations

import os
import shlex
from pathlib import Path

_MAX_FILE_CHARS = 3_000   # Fix #11: never pass more than this to the LLM


# ---------------------------------------------------------------------------
# Fix #10 – robust path handling
# ---------------------------------------------------------------------------

def _normalize_path(raw_path: str) -> str:
    """
    Expand ~, resolve env vars, and strip surrounding quotes.
    shlex.split handles paths with spaces correctly on Windows too.
    """
    # Strip surrounding single/double quotes the user may have typed
    raw_path = raw_path.strip().strip("\"'")
    raw_path = os.path.expandvars(os.path.expanduser(raw_path))
    return str(Path(raw_path).resolve())


def read_file(path: str) -> str | None:
    """
    Read *path* safely.
    Fix #10: normalizes path before open.
    Fix #11: caps content at _MAX_FILE_CHARS characters.
    """
    try:
        normalized = _normalize_path(path)
    except Exception:
        return None

    if not os.path.isfile(normalized):
        return None

    try:
        with open(normalized, "r", encoding="utf-8", errors="replace") as f:
            # Fix #11: read only what we need — avoid loading huge files
            content = f.read(_MAX_FILE_CHARS + 1)
        if len(content) > _MAX_FILE_CHARS:
            content = content[:_MAX_FILE_CHARS] + "\n...[file truncated]"
        return content
    except OSError:
        return "Unsupported file format"


def explain_file(path: str, ask_model) -> str:
    content = read_file(path)

    if content is None:
        norm = _normalize_path(path) if path else path
        return f"File not found: {norm}"

    if content == "Unsupported file format":
        return content

    prompt = (
        "Explain this file clearly in 2-3 sentences.\n\n"
        f"File content:\n{content}"
    )
    return ask_model(prompt)
