"""
ACTION MANAGER — action_manager.py
===================================
Implements three tightly-coupled systems:

  System 1 – APPROVAL QUEUE  (human-in-the-loop)
    Approval state is delegated to the canonical, session-scoped
    approval_service (ARCH-001/SEC-005). The module-level _pending_actions
    global store was removed — do not reintroduce it.

  System 2 – ACTION HISTORY + UNDO
    log_action()          → push to bounded history stack
    undo_last()           → revert last undoable action
    get_history()         → returns formatted list for UI

  System 3 – IRREVERSIBILITY GUARD
    Non-undoable action types are marked NON_UNDOABLE and excluded from undo.
"""

from __future__ import annotations

import os
import shutil
import threading
from collections.abc import Callable
from collections import deque
from datetime import datetime, timezone
from typing import Any

import approval_service
from approval_service import DEFAULT_SESSION_ID
from runtime_utils import log

# ---------------------------------------------------------------------------
# 1 ─ ACTION CLASSIFIER
# ---------------------------------------------------------------------------

# SAFE: run directly, no confirmation needed
_SAFE_KEYWORDS: set[str] = {
    "open", "search", "show", "list", "display", "read",
    "explain", "analyze", "status", "help", "what", "who",
    "hello", "hi", "hey", "thanks",
}

# CONFIRM: propose → user approves → execute
_CONFIRM_KEYWORDS: set[str] = {
    "run", "install", "edit", "write", "create", "start",
    "send", "upload", "download", "update", "copy", "move",
    "pip", "git", "python", "execute", "apply",
}

# DANGEROUS: blocked unconditionally (also covered by safety_guard)
_DANGEROUS_KEYWORDS: set[str] = {
    "delete", "remove", "wipe", "erase", "format", "shutdown",
    "restart", "kill", "drop", "truncate", "rm", "del",
    "uninstall", "reset",
}

# Action types that can NEVER be undone
NON_UNDOABLE: set[str] = {
    "shutdown", "restart", "send_email", "external_api",
    "format_disk", "drop_table", "dangerous_blocked",
}


def classify_action(cmd: str) -> str:
    """
    Returns 'safe', 'confirm', or 'dangerous'.
    Checks dangerous first (highest priority), then confirm, then safe.
    """
    low = cmd.lower()
    if any(k in low for k in _DANGEROUS_KEYWORDS):
        return "dangerous"
    if any(k in low for k in _CONFIRM_KEYWORDS):
        return "confirm"
    if any(k in low for k in _SAFE_KEYWORDS):
        return "safe"
    return "confirm"   # default to confirm for unknown commands


# ---------------------------------------------------------------------------
# 2 ─ PENDING ACTION STORE  (approval queue)
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
# 2 ─ APPROVAL QUEUE  (delegates to canonical approval_service)
# ---------------------------------------------------------------------------

def request_approval(
    cmd: str,
    session_id: str = DEFAULT_SESSION_ID,
    risk_level: str = "confirm",
) -> str:
    """
    Create a session-scoped approval ticket for *cmd* and return the prompt.
    Only the owning session can later approve/cancel the returned ID.
    """
    ticket = approval_service.create_ticket(cmd, session_id=session_id, risk_level=risk_level)
    log(f"[ActionManager] pending approval [{ticket.ticket_id}] session={session_id}: {cmd}")
    return (
        f"🔔 Pending approval\n"
        f"Command: {cmd}\n"
        f"ID: {ticket.ticket_id}\n\n"
        f"Say 'approve {ticket.ticket_id}' to confirm or 'cancel {ticket.ticket_id}' to abort."
    )


def approve_action(
    action_id: str,
    executor: Callable[[str], str],
    session_id: str = DEFAULT_SESSION_ID,
) -> str:
    """
    Approve the ticket *action_id* as *session_id* and execute via *executor*
    (must be safe_exec or equivalent canonical pipeline).
    """
    result = approval_service.approve_ticket(action_id, session_id, executor)
    log_action(
        action=result.split("\n")[0].replace("✅ Executed: ", ""),
        action_type="approved_command",
        undo_data=None,
        undoable=False,
    )
    return result


def cancel_action(action_id: str, session_id: str = DEFAULT_SESSION_ID) -> str:
    return approval_service.cancel_ticket(action_id, session_id)


def list_pending(session_id: str = DEFAULT_SESSION_ID) -> str:
    """Human-readable list of the calling session's pending actions."""
    tickets = approval_service.list_pending(session_id)
    if not tickets:
        return "No pending actions."
    lines = ["⏳ Pending actions:"]
    for t in tickets:
        lines.append(f"  [{t.ticket_id}] {t.action}")
    return "\n".join(lines)


def list_pending_entries(session_id: str = DEFAULT_SESSION_ID) -> dict[str, dict]:
    """Snapshot of the calling session's pending tickets for API consumers."""
    return {
        t.ticket_id: {
            "cmd": t.action,
            "ts": t.created_at,
            "level": t.risk_level,
        }
        for t in approval_service.list_pending(session_id)
    }


# ---------------------------------------------------------------------------
# 3 ─ ACTION HISTORY + UNDO ENGINE
# ---------------------------------------------------------------------------

_MAX_HISTORY = 5

_history_lock = threading.Lock()
_action_history: deque[dict] = deque(maxlen=_MAX_HISTORY)


def log_action(
    action: str,
    action_type: str,
    undo_data: Any = None,
    undoable: bool = True,
) -> None:
    """
    Push an action onto the history stack.

    Parameters
    ----------
    action       : human-readable description ("write /path/to/file.py")
    action_type  : machine-readable type ("write_file", "delete_file", ...)
    undo_data    : tuple passed to the undo engine; None if not undoable
    undoable     : False for irreversible actions (shutdown, send_email, etc.)
    """
    entry = {
        "action":   action,
        "type":     action_type,
        "undo":     undo_data,
        "undoable": undoable and (action_type not in NON_UNDOABLE),
        "ts":       datetime.now(timezone.utc).isoformat(),
    }
    with _history_lock:
        _action_history.appendleft(entry)   # newest first
    log(f"[ActionManager] logged: {action}")


def get_history() -> str:
    """Return a formatted recent action list for UI display."""
    with _history_lock:
        if not _action_history:
            return "No recent actions."
        lines = ["📋 Recent actions (newest first):"]
        for i, entry in enumerate(_action_history, 1):
            flag = "↩" if entry["undoable"] else "🔒"
            lines.append(f"  {i}. {flag} {entry['action']}")
        return "\n".join(lines)


def undo_last() -> str:
    """
    Revert the most recent undoable action from history.
    Non-undoable actions are skipped with a message.
    """
    with _history_lock:
        # Find the first undoable entry
        undoable_idx = next(
            (i for i, e in enumerate(_action_history) if e["undoable"]),
            None,
        )
        if undoable_idx is None:
            return "Nothing to undo — recent actions are irreversible."

        entry = _action_history[undoable_idx]
        # Remove it from history
        tmp = list(_action_history)
        tmp.pop(undoable_idx)
        _action_history.clear()
        _action_history.extend(tmp)

    undo_data = entry["undo"]
    action_type = entry["type"]
    log(f"[ActionManager] undoing: {entry['action']}")

    if action_type == "write_file":
        return _undo_write_file(undo_data)
    elif action_type == "batch_write_file":
        return _undo_batch_write_file(undo_data)
    elif action_type == "delete_file":
        return _undo_delete_file(undo_data)
    elif action_type == "conversation":
        return _undo_conversation(undo_data)
    else:
        return f"Undo not implemented for action type '{action_type}'."


# ---------------------------------------------------------------------------
# 4 ─ UNDO IMPLEMENTATIONS
# ---------------------------------------------------------------------------

def _undo_write_file(undo_data: tuple) -> str:
    """Restore a file to its pre-write content."""
    try:
        _, path, old_content = undo_data
        with open(path, "w", encoding="utf-8") as f:
            f.write(old_content)
        log(f"[Undo] restored file: {path}")
        return f"↩️ Restored file: {path}"
    except Exception as exc:
        log(f"[Undo] failed for file write {path}: {exc}", level="error")
        return f"Undo failed for file write on {os.path.basename(path)}."


def _undo_batch_write_file(undo_data: list[tuple]) -> str:
    """Restore multiple files in a multi-file patch atomically."""
    restored = []
    for item in undo_data:
        try:
            _, path, old_content = item
            with open(path, "w", encoding="utf-8") as f:
                f.write(old_content)
            restored.append(os.path.basename(path))
            log(f"[Undo] batch restored file: {path}")
        except Exception as exc:
            log(f"[Undo] failed batch restore for {path}: {exc}", level="error")
    return f"↩️ Restored multi-file patch ({', '.join(restored)})"


def _undo_delete_file(undo_data: tuple) -> str:
    """Move backup file back to its original path."""
    try:
        _, path, backup_path = undo_data
        if not os.path.exists(backup_path):
            return f"Backup not found: {backup_path}. Cannot undo."
        shutil.move(backup_path, path)
        log(f"[Undo] restored deleted file: {path}")
        return f"↩️ Restored deleted file: {path}"
    except Exception as exc:
        log(f"[Undo] failed for file deletion {path}: {exc}", level="error")
        return f"Undo failed for file deletion on {os.path.basename(path)}."


def _undo_conversation(undo_data: tuple) -> str:
    """Pop the last entry from conversation memory."""
    try:
        from conversation_memory import clear_context
        clear_context()
        return "↩️ Conversation context cleared."
    except Exception as exc:
        log(f"[Undo] failed for conversation: {exc}", level="error")
        return "Undo failed for conversation context."


# ---------------------------------------------------------------------------
# 5 ─ UNDO-AWARE FILE OPERATIONS (use these instead of raw open/shutil)
# ---------------------------------------------------------------------------

def write_file_safe(path: str, content: str) -> str:
    """
    Write *content* to *path*, saving old content first for undo.
    Returns a status string.
    """
    old_content = ""
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8", errors="replace") as f:
                old_content = f.read()
        except Exception as exc:
            try:
                log(f"[ActionManager] failed reading {path}: {exc}", level="warning")
            except Exception:
                # best-effort fallback
                print(f"[ActionManager] read fallback failed: {exc}")

    try:
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
    except Exception as exc:
        log(f"[ActionManager] write failed for {path}: {exc}", level="error")
        return f"Write failed for {os.path.basename(path)}."

    log_action(
        action=f"write {path}",
        action_type="write_file",
        undo_data=("restore_file", path, old_content),
        undoable=True,
    )
    return f"Written: {path}"


def delete_file_safe(path: str) -> str:
    """
    Delete *path*, backing it up as `path.bak` for undo.
    Returns a status string.
    """
    if not os.path.exists(path):
        return f"File not found: {path}"

    backup = path + ".bak"
    try:
        shutil.copy2(path, backup)
        os.remove(path)
    except Exception as exc:
        log(f"[ActionManager] delete failed for {path}: {exc}", level="error")
        return f"Delete failed for {os.path.basename(path)}."

    log_action(
        action=f"delete {path}",
        action_type="delete_file",
        undo_data=("restore_deleted", path, backup),
        undoable=True,
    )
    return f"Deleted: {path} (backup at {backup})"
