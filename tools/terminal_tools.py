"""
Pillar 4 – SYSTEM LAYER (Command Execution)
============================================
Two execution surfaces:

- run_command()  — raw (used only internally by trusted callers)
- safe_exec()    — public; enforces whitelist + safety guard before running
"""

from __future__ import annotations

import subprocess
from safety_guard import check_command

# ---------------------------------------------------------------------------
# Whitelist
# ---------------------------------------------------------------------------

ALLOWED_PREFIXES: tuple[str, ...] = (
    "python",
    "pip",
    "git",
    "uvicorn",
    "npm",
    "node",
    "pytest",
    "mypy",
    "flake8",
    "black",
    "isort",
    "ollama",
    "echo",
    "dir",
    "ls",
    "cat",
    "type",
    "cls",
    "clear",
)

# Maximum execution time (seconds) before the subprocess is killed.
_TIMEOUT_SECONDS = 30


# ---------------------------------------------------------------------------
# Internal runner
# ---------------------------------------------------------------------------

def run_command(command: str) -> str:
    """Run a shell command and return combined output. No safety check here."""
    if not command or not command.strip():
        return "Please specify a command to run."

    try:
        completed = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            check=False,
            timeout=_TIMEOUT_SECONDS,
        )
        output = (completed.stdout or "").strip() or (completed.stderr or "").strip()
        return output if output else "Command executed with no output."
    except subprocess.TimeoutExpired:
        return f"Command timed out after {_TIMEOUT_SECONDS}s."
    except Exception as exc:
        return f"Command error: {exc}"


# ---------------------------------------------------------------------------
# Public safe executor (Pillar 4 + Pillar 5 combined)
# ---------------------------------------------------------------------------

def safe_exec(command: str) -> str:
    """
    Gate the command through:
      1. Whitelist check  — only allowed prefixes may run.
      2. Safety guard     — dangerous patterns are blocked, risky ones need confirm.
    """
    if not command or not command.strip():
        return "Please specify a command."

    command = command.strip()

    # --- 1. Whitelist ---
    low = command.lower()
    if not any(low.startswith(prefix) for prefix in ALLOWED_PREFIXES):
        return (
            f"⛔ Blocked: '{command}' is not in the allowed command list.\n"
            f"Allowed prefixes: {', '.join(ALLOWED_PREFIXES)}"
        )

    # --- 2. Safety guard ---
    guard_result = check_command(command)
    if guard_result is not None:
        return guard_result

    return run_command(command)
