"""
PATCH PREVIEW STORE — tools/preview.py
=======================================
Session-scoped staging of multi-file patch previews (preview-ownership
remediation). Every preview is bound to the session that created it; ALL
operations take the caller's session_id and enforce ownership here, in the
store layer — never in the frontend or the router alone.

Identity reuses the canonical approval_service identities (no second
identity mechanism): DEFAULT_SESSION_ID for the local desktop, REMOTE_SESSION_ID
for the remote agent, or an explicit caller-supplied session id.

Invariants enforced in this file:
  - owner and payload are immutable after creation (stored deep copies)
  - wrong/unknown session cannot get, apply, or discard a preview
    (foreign IDs are indistinguishable from unknown ones — no existence oracle)
  - a preview is single-use: apply atomically consumes it under the lock
    before any filesystem mutation
  - the pre-write hash/conflict check and backups/undo behavior are unchanged
"""

from __future__ import annotations

import copy
import difflib
import os
import secrets
import shutil
import threading

from action_manager import log_action
from approval_service import ApprovalError, DEFAULT_SESSION_ID

_preview_store: dict[str, dict] = {}   # { preview_id: {"session_id": str, "changes": list} }
_store_lock = threading.Lock()
backup_dir = "backups/"

_GENERIC_MISSING = "Invalid preview ID"


def generate_diff(old: str, new: str) -> str:
    diff = difflib.unified_diff(
        old.splitlines(),
        new.splitlines(),
        lineterm=""
    )
    return "\n".join(diff)

def format_preview(change: dict, confidence: int | None = None, reason: str = "") -> str:
    diff = generate_diff(change["old"], change["new"])
    
    # Extract only additions and subtractions for inline preview
    lines = []
    for line in diff.split("\n"):
        if line.startswith("+") and not line.startswith("+++"):
            lines.append(f"➕ {line[1:100]}")
        elif line.startswith("-") and not line.startswith("---"):
            lines.append(f"➖ {line[1:100]}")
            
    clean = "\n".join(lines[:15]) # limit lines
    if len(lines) > 15:
        clean += "\n... (truncated)"
        
    out = f"📄 {change['file']}\n\nChange:\n{clean}"
    if reason:
        out += f"\n\nWhy: {reason}"
    if confidence is not None:
        out += f"\nConfidence: {confidence}%"
    return out

def generate_multi_diff(changes: list, confidence: int | None = None, reason: str = "") -> str:
    output = []
    for change in changes:
        output.append(format_preview(change, confidence, reason))
    return "\n\n────────────────\n\n".join(output)


# ---------------------------------------------------------------------------
# Session-scoped store operations
# ---------------------------------------------------------------------------

def _new_preview_id() -> str:
    # Unguessable ID: a guessed ID must never be the way to reach a foreign
    # preview (defense in depth on top of the ownership check).
    return secrets.token_urlsafe(9)[:12]


def save_preview(
    changes: list,
    session_id: str = DEFAULT_SESSION_ID,
    preview_id: str | None = None,
) -> str:
    """
    Stage *changes* for *session_id*. Returns the preview ID.
    The payload is deep-copied: later mutation of the caller's list cannot
    alter what will be applied.
    """
    pid = preview_id or _new_preview_id()
    with _store_lock:
        # Bound the store (oldest first), preserving the previous cap behavior.
        if len(_preview_store) > 5:
            oldest = next(iter(_preview_store))
            del _preview_store[oldest]
        _preview_store[pid] = {
            "session_id": session_id,
            "changes": copy.deepcopy(changes),
        }
    return pid


def _resolve(preview_id: str, session_id: str) -> dict:
    """Ownership-enforcing lookup. Foreign and unknown IDs are identical."""
    with _store_lock:
        entry = _preview_store.get(preview_id)
        if entry is None or entry["session_id"] != session_id:
            raise ApprovalError("NOT_FOUND", _GENERIC_MISSING)
        return entry


def get_preview(preview_id: str, session_id: str = DEFAULT_SESSION_ID) -> list | None:
    """Deep copy of the staged changes, only for the owning session."""
    try:
        entry = _resolve(preview_id, session_id)
    except ApprovalError:
        return None   # legacy callers treat None as absent; no oracle either way
    return copy.deepcopy(entry["changes"])


def has_preview(preview_id: str, session_id: str = DEFAULT_SESSION_ID) -> bool:
    """Existence check scoped to the calling session."""
    try:
        _resolve(preview_id, session_id)
        return True
    except ApprovalError:
        return False


def discard_preview(preview_id: str, session_id: str = DEFAULT_SESSION_ID) -> bool:
    """Remove the calling session's preview. Foreign/unknown → False."""
    try:
        _resolve(preview_id, session_id)
    except ApprovalError:
        return False
    with _store_lock:
        entry = _preview_store.get(preview_id)
        if entry is not None and entry["session_id"] == session_id:
            del _preview_store[preview_id]
            return True
        return False


def consume_preview(preview_id: str, session_id: str = DEFAULT_SESSION_ID) -> list:
    """
    Atomically remove and return the preview's changes (deep copy) for the
    owning session. Exactly one concurrent caller can ever consume a preview;
    everyone else gets ApprovalError(NOT_FOUND) afterwards.
    """
    with _store_lock:
        entry = _preview_store.get(preview_id)
        if entry is None or entry["session_id"] != session_id:
            raise ApprovalError("NOT_FOUND", _GENERIC_MISSING)
        del _preview_store[preview_id]
    return copy.deepcopy(entry["changes"])


# ---------------------------------------------------------------------------
# Application (canonical filesystem mutation path — unchanged behavior)
# ---------------------------------------------------------------------------

def backup_file(path: str) -> str:
    if not os.path.exists(backup_dir):
        os.makedirs(backup_dir, exist_ok=True)
    safe_name = path.replace("/", "_").replace("\\", "_").replace(":", "_")
    backup_path = os.path.join(backup_dir, safe_name)
    if os.path.exists(path):
        shutil.copy2(path, backup_path)
    return backup_path

def apply_preview(preview_id: str, session_id: str = DEFAULT_SESSION_ID) -> str:
    """
    Apply the owning session's staged patch.
    Single-use: the preview is consumed under the lock BEFORE any filesystem
    mutation, so a concurrent apply can never write twice.
    """
    try:
        changes = consume_preview(preview_id, session_id)
    except ApprovalError:
        return _GENERIC_MISSING

    # Pre-write Conflict Check: Verify base state matches
    for change in changes:
        path = change["file"]
        old_code = change["old"]
        if os.path.exists(path):
            try:
                with open(path, encoding="utf-8", errors="replace") as f:
                    current_content = f.read()
                if old_code and current_content != old_code:
                    return (
                        f"Conflict detected in {path}: file has been modified externally "
                        "since preview was generated. Refusing silent overwrite."
                    )
            except Exception as e:
                from runtime_utils import log
                log(f"[Preview] Error reading base file {path}: {e}", level="error")
                return f"Error reading base file {os.path.basename(path)}: unable to verify file state."

    batch_undo_data = []

    for change in changes:
        path = change["file"]
        old_code = change["old"]
        new_code = change["new"]

        backup_file(path)

        try:
            with open(path, "w", encoding="utf-8") as f:
                f.write(new_code)
        except Exception as e:
            from runtime_utils import log
            log(f"[Preview] Error writing file {path}: {e}", level="error")
            return f"Failed to apply patch to {os.path.basename(path)}."

        batch_undo_data.append(("restore_file", path, old_code))

    files = [os.path.basename(c["file"]) for c in changes]

    log_action(
        action=f"apply patch ({', '.join(files)})",
        action_type="batch_write_file",
        undo_data=batch_undo_data,
        undoable=True,
    )

    return f"Patch applied successfully to: {', '.join(files)}"
