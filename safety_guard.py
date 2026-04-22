"""
Pillar 5 – CONTROL LAYER (Safety + Permissions)
================================================
Every command is classified before execution:

    SAFE       → auto-execute, no question asked
    CONFIRM    → ask user for explicit confirmation
    DANGEROUS  → blocked unconditionally

Use `classify_command()` to get the class, then `check_command()` to get an
executable decision string or None.
"""

from __future__ import annotations

import re
from enum import Enum

# ---------------------------------------------------------------------------
# Classification tables
# ---------------------------------------------------------------------------

class RiskLevel(str, Enum):
    SAFE      = "SAFE"
    CONFIRM   = "CONFIRM"
    DANGEROUS = "DANGEROUS"


# Patterns that are always blocked — no exceptions.
_DANGEROUS_PATTERNS: list[str] = [
    r"\brmdir\b", r"\brm\s+-rf\b",              # directory nukes
    r"\bdel\b.*\/[sS]",                          # del /s (recursive delete)
    r"\bformat\b",                                # disk format
    r"\bshutdown\b", r"\brestart\b",             # system power
    r"\bnetsh\b", r"\bnet\s+user\b",             # account / network tampering
    r"\breg\s+(delete|add)\b",                   # registry writes
    r"\bschtasks\b.*/(create|delete|change)\b",  # scheduled task manipulation
    r"\bpowershell.*-enc\b",                     # encoded PowerShell (obfuscation)
    r"\bcurl\b.*\|\s*(bash|sh|python)\b",        # curl-pipe-execute
    r"\bwget\b.*&&",                             # download + execute chain
    r"\bos\.remove\b", r"\bshutil\.rmtree\b",   # python file deletion
    r"\bdrop\s+table\b", r"\btruncate\b",        # SQL destructive
]

# Patterns that require user confirmation before proceeding.
_CONFIRM_PATTERNS: list[str] = [
    r"\bdelete\b", r"\bremove\b", r"\buninstall\b",
    r"\boverwrite\b", r"\bclear\b.*log",
    r"\bpip\s+uninstall\b",
    r"\bgit\s+reset\b", r"\bgit\s+clean\b", r"\bgit\s+push\b.*--force\b",
    r"\bdrop\b",                                 # partial SQL match
    r"\bkill\b", r"\btaskkill\b",
    r"\bwipe\b", r"\berase\b",
    r"\bwrite to\b.*system",
]

# Everything not matching DANGEROUS or CONFIRM is SAFE.

# ---------------------------------------------------------------------------
# Confirmation state (single pending command)
# ---------------------------------------------------------------------------

_pending_confirmation: dict[str, str] = {}   # {"cmd": <original cmd>}


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def classify_command(text: str) -> RiskLevel:
    """Return the RiskLevel for *text*."""
    low = text.lower()
    for pattern in _DANGEROUS_PATTERNS:
        if re.search(pattern, low):
            return RiskLevel.DANGEROUS
    for pattern in _CONFIRM_PATTERNS:
        if re.search(pattern, low):
            return RiskLevel.CONFIRM
    return RiskLevel.SAFE


def check_command(text: str) -> str | None:
    """
    Gate the command through the safety classifier.

    Returns
    -------
    None            → command is SAFE; caller should proceed normally.
    str (message)   → blocked or needs confirmation; return this to the user.
    """
    level = classify_command(text)

    if level == RiskLevel.DANGEROUS:
        return (
            "⛔ Blocked: This action is too dangerous and cannot be executed. "
            "If you really need this, do it manually in the terminal."
        )

    if level == RiskLevel.CONFIRM:
        _pending_confirmation["cmd"] = text
        return (
            f"⚠️  This action requires confirmation: '{text}'\n"
            "Reply 'confirm' to proceed or 'cancel' to abort."
        )

    return None   # SAFE — let it through


def handle_confirmation_reply(low: str) -> str | None:
    """
    Call this near the top of route_command() to handle pending
    confirmation replies. Returns a response string or None.
    """
    if "cmd" not in _pending_confirmation:
        return None

    if low.strip() in {"confirm", "yes", "y", "proceed", "ok"}:
        cmd = _pending_confirmation.pop("cmd")
        return f"__CONFIRMED__:{cmd}"   # sentinel for the router to re-execute

    if low.strip() in {"cancel", "no", "n", "abort", "stop"}:
        _pending_confirmation.pop("cmd", None)
        return "Action cancelled."

    return None   # not a confirmation reply — ignore pending state
