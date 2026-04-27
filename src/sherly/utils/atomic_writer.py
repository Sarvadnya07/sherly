"""
ATOMIC WRITER — atomic_writer.py
Implements:
  PRODUCTION_AUDIT.md §5.B — Atomic file writes via tmp → os.replace().

  Every write goes through:
    1. Write to  <target>.tmp  in the same directory
    2. os.replace() atomically renames .tmp → target
       (on the same filesystem, this is an atomic kernel operation)
    3. On any failure the .tmp is cleaned up; the original is never corrupted.

  This prevents zero-byte files on power loss / process kill mid-write.
"""

from __future__ import annotations

import os
import tempfile
from pathlib import Path


def atomic_write(path: str | Path, content: str, encoding: str = "utf-8") -> None:
    """
    Atomically write *content* to *path*.

    Guarantees that either the full new content is present at *path*,
    or the original file is untouched — no partial writes, no zero-byte files.

    Raises:
        OSError: if the write or rename fails.
    """
    path    = Path(path)
    dir_    = path.parent
    dir_.mkdir(parents=True, exist_ok=True)

    # Write to a temp file in the same directory so os.replace() is atomic
    fd, tmp_path = tempfile.mkstemp(dir=str(dir_), suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding=encoding) as f:
            f.write(content)
            f.flush()
            os.fsync(f.fileno())   # Flush OS kernel buffers to disk

        os.replace(tmp_path, str(path))   # Atomic rename
    except Exception:
        # Clean up the temp file on failure; original is untouched
        try:
            os.unlink(tmp_path)
        except OSError:
            pass
        raise


def atomic_write_bytes(path: str | Path, data: bytes) -> None:
    """
    Atomically write raw *data* bytes to *path*.
    """
    path  = Path(path)
    dir_  = path.parent
    dir_.mkdir(parents=True, exist_ok=True)

    fd, tmp_path = tempfile.mkstemp(dir=str(dir_), suffix=".tmp")
    try:
        with os.fdopen(fd, "wb") as f:
            f.write(data)
            f.flush()
            os.fsync(f.fileno())

        os.replace(tmp_path, str(path))
    except Exception:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass
        raise
