"""
Pillar 5 – CONTROL LAYER (Safety + Permissions)
================================================
Every command is classified before execution:

    SAFE       → auto-execute, no question asked
    CONFIRM    → ask user for explicit confirmation
    DANGEROUS  → blocked unconditionally

Use `classify_command()` to get the class, then `check_command()` to get an
executable decision string or None.

ARCH-001/SEC-005: confirmation state is no longer a process-global slot.
CONFIRM commands create a session-scoped approval ticket via the canonical
approval_service; only the session that triggered the command can confirm it.
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
    r"&&", r";", r"\|\|", r"\|\s*",              # shell command chaining / piping
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


def check_command(
    text: str,
    session_id: str = "local",
) -> str | None:
    """
    Gate the command through the safety classifier.

    Returns
    -------
    None            → command is SAFE; caller should proceed normally.
    str (message)   → blocked or needs confirmation; return this to the user.
    """
    import approval_service

    level = classify_command(text)

    if level == RiskLevel.DANGEROUS:
        return (
            "⛔ Blocked: This action is too dangerous and cannot be executed. "
            "If you really need this, do it manually in the terminal."
        )

    if level == RiskLevel.CONFIRM:
        ticket = approval_service.create_ticket(
            text, session_id=session_id, risk_level="confirm",
        )
        return (
            f"⚠️  This action requires confirmation: '{text}'\n"
            f"Reply 'confirm {ticket.ticket_id}' to proceed or "
            f"'cancel {ticket.ticket_id}' to abort."
        )

    return None   # SAFE — let it through


# Backwards-compatible default used by tests and legacy callers that never
# specified a session. Reply handling now requires the ticket ID, so the old
# single-slot "any yes confirms whatever is pending" behavior is gone by design.
LEGACY_SESSION_ID = "local"


def handle_confirmation_reply(low: str, session_id: str = LEGACY_SESSION_ID) -> str | None:
    """
    Handle 'confirm <id>' / 'cancel <id>' replies for *session_id*.

    The bare 'confirm'/'cancel' forms from the old single-slot design are no
    longer accepted: a reply must name its ticket ID, so a stray "yes" from
    one surface can never confirm a command raised by another (SEC-006 fix,
    enforced via SEC-005 tickets). Returns a response string or None.
    """
    import approval_service

    stripped = (low or "").strip()
    parts = stripped.split()
    if len(parts) != 2 or parts[0] not in {"confirm", "cancel"}:
        # Not a ticket reply — let it fall through to normal routing.
        return None

    verb, ticket_id = parts
    try:
        if verb == "confirm":
            # The executor here does NOT run the command — it just tags the
            # approved action. The ticket is atomically consumed now (so it is
            # single-use even if the router crashes later); the router then
            # runs the frozen action through safe_exec exactly once.
            result = approval_service.approve_ticket(
                ticket_id, session_id, lambda action: f"__CONFIRMED__:{action}",
            )
            if "__CONFIRMED__:" in result:
                return "__CONFIRMED__:" + result.split("__CONFIRMED__:", 1)[1].split("\n")[0]
            return result
        return approval_service.cancel_ticket(ticket_id, session_id)
    except approval_service.ApprovalError as exc:
        return exc.public_message
