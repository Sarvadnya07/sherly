"""
ACTION MANAGER — action_manager.py
===================================
Implements three tightly-coupled systems:

  System 1 – APPROVAL QUEUE  (human-in-the-loop)
    classify_action()     → safe / confirm / dangerous
    request_approval()    → adds to pending store, returns prompt
    approve_action()      → executes approved pending command
    cancel_action()       → removes pending command
    list_pending()        → returns formatted pending list for UI

  System 2 – ACTION HISTORY + UNDO
    log_action()          → push to bounded history stack
    undo_last()           → revert last undoable action
    get_history()         → returns formatted list for UI

  System 3 – IRREVERSIBILITY GUARD
    Non-undoable action types are marked NON_UNDOABLE and excluded from undo.

Fixes:
  RC-3  Added _db_write_lock around all SQLite write paths to prevent
         'database is locked' errors under concurrent load.
"""

from __future__ import annotations

import os
import shutil
import threading
import uuid
from collections import deque
from datetime import datetime, timezone
from typing import Any, Callable

from sherly.utils.runtime_utils import log
from sherly.services.memory import conn
import json

# RC-3 — Dedicated write lock for all SQLite writes in this module
_db_write_lock = threading.Lock()

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
    words = set(cmd.lower().replace('.', '').replace(',', '').split())
    if any(k in words for k in _DANGEROUS_KEYWORDS):
        return "dangerous"
    if any(k in words for k in _CONFIRM_KEYWORDS):
        return "confirm"
    if any(k in words for k in _SAFE_KEYWORDS):
        return "safe"
    return "confirm"   # default to confirm for unknown commands


# ---------------------------------------------------------------------------
# 2 ─ PENDING ACTION STORE  (approval queue)
# ---------------------------------------------------------------------------

_pending_lock = threading.Lock()
_pending_actions: dict[str, dict] = {}   # { action_id: {cmd, ts, level} }

_PENDING_TTL_SECONDS = 120   # pending actions expire after 2 minutes


def _prune_expired() -> None:
    """Remove pending actions older than TTL."""
    now = datetime.now(timezone.utc).timestamp()
    expired = [
        k for k, v in _pending_actions.items()
        if now - v["ts"] > _PENDING_TTL_SECONDS
    ]
    for k in expired:
        del _pending_actions[k]


def request_approval(cmd: str) -> str:
    """
    Add *cmd* to the pending queue and return the confirmation prompt.
    Returns a short action ID the user can reference to approve/cancel.
    """
    with _pending_lock:
        _prune_expired()
        action_id = str(uuid.uuid4())[:8]   # short 8-char ID, easy to say/type
        _pending_actions[action_id] = {
            "cmd": cmd,
            "ts":  datetime.now(timezone.utc).timestamp(),
            "level": "confirm",
        }
    log(f"[ActionManager] pending approval [{action_id}]: {cmd}")
    return (
        f"🔔 Pending approval\n"
        f"Command: {cmd}\n"
        f"ID: {action_id}\n\n"
        f"Say 'approve {action_id}' to confirm or 'cancel {action_id}' to abort."
    )


def approve_action(action_id: str, executor: Callable[[str], str]) -> str:
    """
    Execute the pending command identified by *action_id*.
    *executor* is called with the raw command string — use safe_exec().
    """
    with _pending_lock:
        _prune_expired()
        entry = _pending_actions.pop(action_id, None)

    if entry is None:
        return f"⚠️ No pending action found with ID '{action_id}'. It may have expired or been cancelled."

    cmd = entry["cmd"]
    log(f"[ActionManager] approved [{action_id}]: {cmd}")
    result = executor(cmd)

    # Log to action history so the user can undo
    log_action(
        action=cmd,
        action_type="approved_command",
        undo_data=None,    # terminal commands are not undoable
        undoable=False,
    )
    return f"✅ Executed: {cmd}\n\n{result}"


def cancel_action(action_id: str) -> str:
    with _pending_lock:
        entry = _pending_actions.pop(action_id, None)
    if entry is None:
        return f"No pending action with ID '{action_id}'."
    log(f"[ActionManager] cancelled [{action_id}]: {entry['cmd']}")
    return f"❌ Cancelled action: {entry['cmd']}"


def list_pending() -> str:
    """Return a human-readable list of pending actions."""
    with _pending_lock:
        _prune_expired()
        if not _pending_actions:
            return "No pending actions."
        lines = ["⏳ Pending actions:"]
        for aid, entry in _pending_actions.items():
            lines.append(f"  [{aid}] {entry['cmd']}")
        return "\n".join(lines)


# ---------------------------------------------------------------------------
# 3 ─ ACTION HISTORY + UNDO ENGINE
# ---------------------------------------------------------------------------

def _load_history():
    pass  # No longer needed, DB is live


def _save_history(entry: dict) -> None:
    """RC-3: All writes serialized through _db_write_lock."""
    with _db_write_lock:
        try:
            conn.execute(
                "INSERT INTO action_history "
                "(action, action_type, undo_data, undoable, timestamp) "
                "VALUES (?, ?, ?, ?, ?)",
                (
                    entry["action"],
                    entry["type"],
                    json.dumps(entry["undo"]),
                    1 if entry["undoable"] else 0,
                    entry["ts"],
                ),
            )
            conn.commit()
        except Exception as exc:
            log(f"[ActionManager] Failed to save history: {exc}", level="error")


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
    _save_history(entry)
    log(f"[ActionManager] logged: {action}")


def get_history() -> str:
    """Return a formatted recent action list for UI display."""
    cursor = conn.execute("SELECT action, undoable FROM action_history ORDER BY id DESC LIMIT 5")
    rows = cursor.fetchall()
    if not rows:
        return "No recent actions."
    lines = ["[HISTORY] Recent actions (newest first):"]
    for i, (action, undoable) in enumerate(rows, 1):
        flag = "[UNDO]" if undoable else "[LOCK]"
        lines.append(f"  {i}. {flag} {action}")
    return "\n".join(lines)


def undo_last() -> str:
    """
    Revert the most recent undoable action from history.
    RC-3: DELETE is also serialized through _db_write_lock.
    """
    cursor = conn.execute(
        "SELECT id, action, action_type, undo_data FROM action_history "
        "WHERE undoable=1 ORDER BY id DESC LIMIT 1"
    )
    row = cursor.fetchone()
    if not row:
        return "Nothing to undo — recent actions are irreversible."

    hid, action, action_type, undo_json = row
    undo_data = json.loads(undo_json)

    # RC-3: serialize the DELETE write
    with _db_write_lock:
        conn.execute("DELETE FROM action_history WHERE id=?", (hid,))
        conn.commit()

    log(f"[ActionManager] undoing: {action}")

    if action_type == "write_file":
        return _undo_write_file(undo_data)
    elif action_type == "delete_file":
        return _undo_delete_file(undo_data)
    elif action_type == "conversation":
        return _undo_conversation(undo_data)
    elif action_type == "shell_command":
        return _undo_shell_command(undo_data)   # FS-#6
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
        return f"[UNDO] Restored file: {path}"
    except Exception as exc:
        return f"Undo failed for file write: {exc}"


def _undo_delete_file(undo_data: tuple) -> str:
    """Move backup file back to its original path."""
    try:
        _, path, backup_path = undo_data
        if not os.path.exists(backup_path):
            return f"Backup not found: {backup_path}. Cannot undo."
        shutil.move(backup_path, path)
        log(f"[Undo] restored deleted file: {path}")
        return f"[UNDO] Restored deleted file: {path}"
    except Exception as exc:
        return f"Undo failed for file deletion: {exc}"


def _undo_conversation(undo_data: tuple) -> str:
    """Pop the last entry from conversation memory."""
    try:
        from sherly.services.conversation_memory import clear_context
        clear_context()
        return "[UNDO] Conversation context cleared."
    except Exception as exc:
        return f"Undo failed for conversation: {exc}"


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
        except Exception:
            pass

    try:
        from sherly.utils.atomic_writer import atomic_write
        atomic_write(path, content)
    except Exception as exc:
        return f"Write failed: {exc}"

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
        return f"Delete failed: {exc}"

    log_action(
        action=f"delete {path}",
        action_type="delete_file",
        undo_data=("restore_deleted", path, backup),
        undoable=True,
    )
    return f"Deleted: {path} (backup at {backup})"


# ---------------------------------------------------------------------------
# FS-#6 — Shell Command Undo (whitelisted reversible commands)
# ---------------------------------------------------------------------------

#: Maps a command prefix to the function that builds its inverse.
#: Key = canonical first token; value = (inverse_builder_fn, is_undoable)
_REVERSIBLE_COMMANDS: dict[str, str] = {
    "mkdir": "rmdir",   # mkdir foo → rmdir foo
    "rmdir": "mkdir",   # rmdir foo → mkdir foo
    "cp":    "rm",      # cp src dst → rm dst
    "copy":  "del",     # Windows copy src dst → del dst
    "mv":    None,      # mv src dst → mv dst src  (special case)
    "move":  None,      # Windows move src dst → move dst src
}


def _compute_inverse(cmd: str) -> str | None:
    """
    FS-#6: Compute the inverse of a whitelisted shell command.
    Returns the inverse command string, or None if not invertible.
    """
    import shlex
    try:
        parts = shlex.split(cmd)
    except ValueError:
        return None
    if not parts:
        return None

    verb = parts[0].lower()

    if verb in ("mkdir", "rmdir") and len(parts) >= 2:
        opposite = "rmdir" if verb == "mkdir" else "mkdir"
        return f"{opposite} {parts[1]}"

    if verb in ("cp", "copy") and len(parts) >= 3:
        dst = parts[-1]
        return f"rm {dst}"

    if verb in ("mv", "move") and len(parts) >= 3:
        src, dst = parts[1], parts[2]
        return f"{verb} {dst} {src}"

    return None


def shell_command_safe(cmd: str) -> str:
    """
    FS-#6: Execute a whitelisted, reversible shell command with undo support.

    Supported: mkdir, rmdir, cp/copy, mv/move.
    Unsupported commands are executed but logged as non-undoable.
    Returns a status string.
    """
    import subprocess, shlex

    inverse = _compute_inverse(cmd)
    undoable = inverse is not None

    try:
        result = subprocess.run(
            shlex.split(cmd),
            capture_output=True,
            text=True,
            timeout=15,
            shell=False,
        )
        output = result.stdout.strip() or result.stderr.strip()
    except Exception as exc:
        return f"Shell command failed: {exc}"

    log_action(
        action=cmd,
        action_type="shell_command",
        undo_data=("run_inverse", inverse) if undoable else None,
        undoable=undoable,
    )

    suffix = " ([UNDO] undoable)" if undoable else " ([LOCK] not undoable)"
    return f"Executed: {cmd}{suffix}\n{output}" if output else f"Executed: {cmd}{suffix}"


def _undo_shell_command(undo_data: tuple) -> str:
    """
    FS-#6: Replay the pre-computed inverse command.
    undo_data = ("run_inverse", inverse_cmd_string)
    """
    import subprocess, shlex

    if not undo_data or len(undo_data) < 2:
        return "No inverse command available for this action."

    _, inverse_cmd = undo_data[0], undo_data[1]
    if not inverse_cmd:
        return "This shell command has no automatic inverse."

    try:
        result = subprocess.run(
            shlex.split(inverse_cmd),
            capture_output=True,
            text=True,
            timeout=15,
            shell=False,
        )
        output = result.stdout.strip() or result.stderr.strip()
        log(f"[Undo] ran inverse command: {inverse_cmd}")
        return f"[UNDO] Reversed with: {inverse_cmd}\n{output}" if output else f"[UNDO] Reversed with: {inverse_cmd}"
    except Exception as exc:
        return f"Undo (shell command) failed: {exc}"
