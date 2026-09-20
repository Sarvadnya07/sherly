"""
APPROVAL SERVICE — approval_service.py
=======================================
Canonical, session-scoped approval-ticket system (ARCH-001 / SEC-005 remediation).

Replaces the two former process-global approval stores:
  - safety_guard._pending_confirmation (single-slot, any caller confirmed it)
  - action_manager._pending_actions    (ID-keyed but ownerless)

Security model
--------------
Every approval lives in an immutable ApprovalTicket bound to the session that
created it. ALL operations take the caller's session_id and enforce ownership
inside the service — a caller can never look up, approve, cancel, or consume a
ticket belonging to another session.

Invariants enforced here (server-side):
  1. owner/session is immutable after creation
  2. action payload is immutable after creation
  3. only the owner session can approve / cancel / list
  4. expired tickets cannot be approved or executed
  5. cancelled tickets cannot be approved or executed
  6. a ticket is single-use: approval atomically consumes it
  7. unknown and foreign tickets are indistinguishable (no existence oracle)
  8. ticket IDs use cryptographically secure randomness

Concurrency: a single lock guards the ticket table; approve/cancel/consume
pop the ticket under the lock, so exactly one caller can ever transition a
ticket out of PENDING.
"""

from __future__ import annotations

import secrets
import threading
import time
from dataclasses import dataclass, field
from enum import Enum

from runtime_utils import log

# Default session for the single-user local desktop app. Sessions are opt-in:
# surfaces that can distinguish clients (HTTP headers, remote agent) pass an
# explicit session id; anything that cannot remains this canonical identity.
DEFAULT_SESSION_ID = "local"

# Remote agent process gets its own identity: tickets created via a remote
# path can never collide with — or be consumed by — local desktop tickets.
REMOTE_SESSION_ID = "remote-agent"

DEFAULT_TTL_SECONDS = 120  # preserved from the previous pending-action TTL


class TicketStatus(str, Enum):
    PENDING = "PENDING"
    CANCELLED = "CANCELLED"
    EXPIRED = "EXPIRED"
    CONSUMED = "CONSUMED"


@dataclass(frozen=True)
class ApprovalTicket:
    """Immutable approval ticket. Payload and owner can never change."""
    ticket_id: str
    session_id: str
    action: str
    risk_level: str
    created_at: float
    expires_at: float
    status: TicketStatus = TicketStatus.PENDING
    metadata: dict = field(default_factory=dict)


class ApprovalError(Exception):
    """Deliberate API error for ticket operations.

    `code` distinguishes NOT_FOUND / WRONG_OWNER (both reported externally
    as the same generic message, per the no-existence-oracle invariant),
    EXPIRED, CANCELLED, ALREADY_CONSUMED.
    """

    def __init__(self, code: str, public_message: str) -> None:
        super().__init__(public_message)
        self.code = code
        self.public_message = public_message


_TICKETS: dict[str, ApprovalTicket] = {}
_lock = threading.Lock()

# NOT_FOUND and WRONG_OWNER share one public message: a caller probing IDs
# must not learn whether a ticket exists in another session.
_GENERIC_MISSING = (
    "No pending action found with that ID. It may have expired, "
    "been cancelled, or belong to a different session."
)


def _now() -> float:
    return time.time()


def _new_ticket_id() -> str:
    # 16 url-safe random chars: unguessable, still short enough to type.
    return secrets.token_urlsafe(9)[:12]


def create_ticket(
    action: str,
    session_id: str = DEFAULT_SESSION_ID,
    risk_level: str = "confirm",
    ttl_seconds: int = DEFAULT_TTL_SECONDS,
    metadata: dict | None = None,
) -> ApprovalTicket:
    """Create a PENDING ticket owned by *session_id*. Payload is frozen here."""
    ticket = ApprovalTicket(
        ticket_id=_new_ticket_id(),
        session_id=session_id,
        action=action,
        risk_level=risk_level,
        created_at=_now(),
        expires_at=_now() + ttl_seconds,
        metadata=dict(metadata or {}),
    )
    with _lock:
        # Bound the table: drop oldest expired/consumed entries first.
        if len(_TICKETS) > 256:
            now = _now()
            for tid, t in list(_TICKETS.items()):
                if t.status is not TicketStatus.PENDING or t.expires_at < now:
                    del _TICKETS[tid]
        _TICKETS[ticket.ticket_id] = ticket
    log(f"[ApprovalService] ticket created [{ticket.ticket_id}] session={session_id} risk={risk_level}")
    return ticket


def _resolve(ticket_id: str, session_id: str) -> ApprovalTicket:
    """Look up a ticket enforcing ownership. Raises ApprovalError."""
    with _lock:
        ticket = _TICKETS.get(ticket_id)
        if ticket is None or ticket.session_id != session_id:
            raise ApprovalError("NOT_FOUND", _GENERIC_MISSING)
    return ticket


def _status_error(ticket: ApprovalTicket) -> ApprovalError:
    if ticket.status is TicketStatus.EXPIRED or ticket.expires_at < _now():
        return ApprovalError("EXPIRED", "This action expired. Request it again.")
    if ticket.status is TicketStatus.CANCELLED:
        return ApprovalError("CANCELLED", "This action was already cancelled.")
    return ApprovalError("ALREADY_CONSUMED", "This action was already handled.")


def get_ticket(ticket_id: str, session_id: str) -> ApprovalTicket:
    """Return a ticket only if owned by *session_id* and still actionable."""
    ticket = _resolve(ticket_id, session_id)
    if ticket.status is not TicketStatus.PENDING:
        raise _status_error(ticket)
    if ticket.expires_at < _now():
        return _mark_expired(ticket)
    return ticket


def list_pending(session_id: str) -> list[ApprovalTicket]:
    """All actionable tickets for one session only. Never crosses sessions."""
    now = _now()
    out = []
    with _lock:
        for t in _TICKETS.values():
            if t.session_id != session_id:
                continue
            if t.status is TicketStatus.PENDING and t.expires_at >= now:
                out.append(t)
    return out


def approve_ticket(
    ticket_id: str,
    session_id: str,
    executor,
) -> str:
    """
    Approve and execute a ticket as *session_id*.

    Atomically consumes the ticket under the lock before running the executor,
    so concurrent approvals cannot double-execute. `executor(action)` must run
    the canonical pipeline (safe_exec), never a bypass.
    """
    with _lock:
        ticket = _TICKETS.get(ticket_id)
        if ticket is None or ticket.session_id != session_id:
            raise ApprovalError("NOT_FOUND", _GENERIC_MISSING)
        if ticket.status is not TicketStatus.PENDING:
            raise _status_error(ticket)
        if ticket.expires_at < _now():
            _TICKETS[ticket_id] = _frozen_with(ticket, status=TicketStatus.EXPIRED)
            raise ApprovalError("EXPIRED", "This action expired. Request it again.")
        # Single-use: transition out of PENDING atomically.
        _TICKETS[ticket_id] = _frozen_with(ticket, status=TicketStatus.CONSUMED)

    log(f"[ApprovalService] ticket approved+consumed [{ticket_id}] session={session_id}")
    result = executor(ticket.action)
    return f"✅ Executed: {ticket.action}\n\n{result}"


def cancel_ticket(ticket_id: str, session_id: str) -> str:
    with _lock:
        ticket = _TICKETS.get(ticket_id)
        if ticket is None or ticket.session_id != session_id:
            raise ApprovalError("NOT_FOUND", _GENERIC_MISSING)
        if ticket.status is not TicketStatus.PENDING:
            raise _status_error(ticket)
        _TICKETS[ticket_id] = _frozen_with(ticket, status=TicketStatus.CANCELLED)
    log(f"[ApprovalService] ticket cancelled [{ticket_id}] session={session_id}")
    return f"❌ Cancelled action: {ticket.action}"


def _mark_expired(ticket: ApprovalTicket) -> ApprovalTicket:
    expired = _frozen_with(ticket, status=TicketStatus.EXPIRED)
    with _lock:
        _TICKETS[ticket.ticket_id] = expired
    raise ApprovalError("EXPIRED", "This action expired. Request it again.")


def _frozen_with(ticket: ApprovalTicket, **changes) -> ApprovalTicket:
    data = dict(
        ticket_id=ticket.ticket_id,
        session_id=ticket.session_id,
        action=ticket.action,
        risk_level=ticket.risk_level,
        created_at=ticket.created_at,
        expires_at=ticket.expires_at,
        status=ticket.status,
        metadata=ticket.metadata,
    )
    data.update(changes)
    return ApprovalTicket(**data)


def reset_for_tests() -> None:
    """Test-only: clear all tickets."""
    with _lock:
        _TICKETS.clear()
