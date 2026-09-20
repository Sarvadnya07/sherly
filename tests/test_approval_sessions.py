"""
SESSION-SCOPED APPROVALS — tests/test_approval_sessions.py
ARCH-001 / SEC-005 regression suite.

Proves the security properties behaviorally:
  - cross-session isolation (no existence oracle)
  - single-use consumption / replay resistance
  - TTL expiry
  - immutability of owner and payload
  - concurrency: exactly one execution
  - integration with safety_guard and the command router
"""

from __future__ import annotations

import threading

import pytest

import approval_service
from approval_service import (
    ApprovalError,
    TicketStatus,
    create_ticket,
    approve_ticket,
    cancel_ticket,
    get_ticket,
    list_pending,
)


@pytest.fixture(autouse=True)
def _clean_tickets():
    approval_service.reset_for_tests()
    yield
    approval_service.reset_for_tests()


def _exec_tracking(results: list, value: str = "ok"):
    def executor(action: str) -> str:
        results.append(action)
        return value
    return executor


# ── Core lifecycle ───────────────────────────────────────────────────────────

def test_confirm_commands_create_ticket():
    ticket = create_ticket("delete the log file", session_id="s1")
    assert ticket.status is TicketStatus.PENDING
    assert [t.ticket_id for t in list_pending("s1")] == [ticket.ticket_id]


def test_safe_commands_do_not_create_approval():
    # Behavioral contract at the safety layer: SAFE commands never raise a ticket.
    from safety_guard import check_command
    assert check_command("open vscode") is None
    assert list_pending("local") == []


def test_dangerous_commands_remain_blocked():
    from safety_guard import check_command
    res = check_command("rm -rf /")
    assert res is not None and "Blocked" in res
    assert list_pending("local") == []


def test_expired_ticket_rejected():
    ticket = create_ticket("delete log", session_id="s1", ttl_seconds=-1)
    with pytest.raises(ApprovalError) as ei:
        approve_ticket(ticket.ticket_id, "s1", lambda a: "ran")
    assert ei.value.code == "EXPIRED"
    # And it cannot be resurrected
    with pytest.raises(ApprovalError):
        get_ticket(ticket.ticket_id, "s1")


def test_cancelled_ticket_rejected():
    ticket = create_ticket("delete log", session_id="s1")
    cancel_ticket(ticket.ticket_id, "s1")
    with pytest.raises(ApprovalError) as ei:
        approve_ticket(ticket.ticket_id, "s1", lambda a: "ran")
    assert ei.value.code == "CANCELLED"


def test_ticket_consumed_once():
    ran: list[str] = []
    ticket = create_ticket("delete log", session_id="s1")
    approve_ticket(ticket.ticket_id, "s1", _exec_tracking(ran))
    assert ran == ["delete log"]
    # Replay must fail
    with pytest.raises(ApprovalError) as ei:
        approve_ticket(ticket.ticket_id, "s1", _exec_tracking(ran))
    assert ei.value.code == "ALREADY_CONSUMED"
    assert ran == ["delete log"]  # no double execution


# ── Session isolation ────────────────────────────────────────────────────────

def test_ticket_is_session_scoped():
    create_ticket("mine", session_id="s1")
    create_ticket("theirs", session_id="s2")
    assert [t.action for t in list_pending("s1")] == ["mine"]
    assert [t.action for t in list_pending("s2")] == ["theirs"]


def test_wrong_session_cannot_approve():
    ran: list[str] = []
    ticket = create_ticket("victim command", session_id="s1")
    with pytest.raises(ApprovalError) as ei:
        approve_ticket(ticket.ticket_id, "attacker", _exec_tracking(ran))
    # Existence oracle: attacker gets the same message as an unknown ID
    assert ei.value.code == "NOT_FOUND"
    assert ran == []
    # The real owner can still approve it
    approve_ticket(ticket.ticket_id, "s1", _exec_tracking(ran))
    assert ran == ["victim command"]


def test_wrong_session_cannot_cancel():
    ticket = create_ticket("victim command", session_id="s1")
    with pytest.raises(ApprovalError):
        cancel_ticket(ticket.ticket_id, "attacker")
    # Still pending for the owner
    assert [t.ticket_id for t in list_pending("s1")] == [ticket.ticket_id]


def test_wrong_session_cannot_view_ticket():
    ticket = create_ticket("victim command", session_id="s1")
    with pytest.raises(ApprovalError):
        get_ticket(ticket.ticket_id, "attacker")


def test_unknown_ticket_is_generic():
    with pytest.raises(ApprovalError) as ei:
        approve_ticket("nonexistent0", "s1", lambda a: "ran")
    assert ei.value.code == "NOT_FOUND"


def test_multiple_sessions_are_isolated():
    t1 = create_ticket("s1 cmd", session_id="s1")
    t2 = create_ticket("s2 cmd", session_id="s2")
    approve_ticket(t1.ticket_id, "s1", lambda a: "ok")
    # s2's ticket is untouched by s1's approval
    assert [t.ticket_id for t in list_pending("s2")] == [t2.ticket_id]
    approve_ticket(t2.ticket_id, "s2", lambda a: "ok")
    assert list_pending("s1") == [] and list_pending("s2") == []


# ── Immutability ─────────────────────────────────────────────────────────────

def test_action_payload_is_immutable():
    ticket = create_ticket("original command", session_id="s1")
    with pytest.raises(Exception):
        ticket.action = "hacked"  # type: ignore[misc]
    consumed = []
    approve_ticket(ticket.ticket_id, "s1", _exec_tracking(consumed))
    assert consumed == ["original command"]


def test_ticket_owner_is_immutable():
    ticket = create_ticket("victim", session_id="s1")
    with pytest.raises(Exception):
        ticket.session_id = "attacker"  # type: ignore[misc]


def test_ticket_ids_are_unguessable():
    ids = {create_ticket(f"cmd {i}", session_id="s").ticket_id for i in range(50)}
    assert len(ids) == 50
    assert all(len(i) >= 8 for i in ids)


# ── Concurrency ──────────────────────────────────────────────────────────────

def test_concurrent_approve_only_executes_once():
    ran: list[str] = []
    ticket = create_ticket("single execution", session_id="s1")
    barrier = threading.Barrier(8)
    outcomes: list[str] = []

    def worker():
        barrier.wait()
        try:
            approve_ticket(ticket.ticket_id, "s1", _exec_tracking(ran))
            outcomes.append("approved")
        except ApprovalError as e:
            outcomes.append(e.code)

    threads = [threading.Thread(target=worker) for _ in range(8)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert ran == ["single execution"]          # exactly one execution
    assert outcomes.count("approved") == 1
    assert outcomes.count("ALREADY_CONSUMED") == 7


def test_concurrent_approve_and_cancel():
    ran: list[str] = []
    ticket = create_ticket("race", session_id="s1")
    barrier = threading.Barrier(2)
    results: list[str] = []

    def do_approve():
        barrier.wait()
        try:
            approve_ticket(ticket.ticket_id, "s1", _exec_tracking(ran))
            results.append("approved")
        except ApprovalError as e:
            results.append(e.code)

    def do_cancel():
        barrier.wait()
        try:
            cancel_ticket(ticket.ticket_id, "s1")
            results.append("cancelled")
        except ApprovalError as e:
            results.append(e.code)

    threads = [threading.Thread(target=do_approve), threading.Thread(target=do_cancel)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    # Exactly one terminal transition wins; the loser reports a stable state.
    assert sorted(results) in (["ALREADY_CONSUMED", "approved"], ["CANCELLED", "cancelled"])
    if "approved" in results:
        assert ran == ["race"]
    else:
        assert ran == []


def test_repeated_approve_and_cancel_requests():
    ticket = create_ticket("once only", session_id="s1")
    approve_ticket(ticket.ticket_id, "s1", lambda a: "ran")
    for _ in range(3):
        with pytest.raises(ApprovalError):
            approve_ticket(ticket.ticket_id, "s1", lambda a: "ran")
    # Cancel after consumption also fails; no state resurrection
    with pytest.raises(ApprovalError):
        cancel_ticket(ticket.ticket_id, "s1")


def test_multiple_pending_tickets_one_session():
    tickets = [create_ticket(f"cmd {i}", session_id="s1") for i in range(5)]
    assert len(list_pending("s1")) == 5
    approve_ticket(tickets[2].ticket_id, "s1", lambda a: "ok")
    remaining = {t.ticket_id for t in list_pending("s1")}
    assert remaining == {t.ticket_id for t in tickets if t is not tickets[2]}


def test_reconnect_does_not_transfer_ticket():
    # A "reconnect" is just the same session id presenting again — ownership
    # follows the session, not a connection object, and a different session
    # id (new connection) cannot inherit tickets.
    ticket = create_ticket("persist across reconnect", session_id="device-A")
    # Old connection drops, new connection claims a different identity:
    with pytest.raises(ApprovalError):
        approve_ticket(ticket.ticket_id, "device-A-2", lambda a: "ran")
    # Same session reconnects: still the owner.
    approve_ticket(ticket.ticket_id, "device-A", lambda a: "ran")


# ── Integration: safety_guard + command router ───────────────────────────────

def test_check_command_creates_scoped_ticket():
    from safety_guard import check_command, handle_confirmation_reply
    prompt = check_command("delete the log file", session_id="sess-A")
    assert prompt is not None and "confirm" in prompt.lower()
    tickets = list_pending("sess-A")
    assert len(tickets) == 1
    tid = tickets[0].ticket_id
    # Another session's confirm reply must not consume it
    msg = handle_confirmation_reply(f"confirm {tid}", session_id="sess-B")
    assert "different session" in msg or "No pending" in msg
    # Owner confirms: router contract returns the tagged action, executed once
    tagged = handle_confirmation_reply(f"confirm {tid}", session_id="sess-A")
    assert tagged.startswith("__CONFIRMED__:")
    assert list_pending("sess-A") == []


def test_bare_confirm_no_longer_confirms_anything():
    from safety_guard import check_command, handle_confirmation_reply
    check_command("delete the log file", session_id="sess-A")
    # The old single-slot "confirm" with no ID must not consume anything.
    assert handle_confirmation_reply("confirm", session_id="sess-B") is None
    assert handle_confirmation_reply("yes", session_id="sess-A") is None
    assert len(list_pending("sess-A")) == 1


def test_router_approval_flow_is_session_scoped():
    from command_router import route_command
    # Route a confirm-level command in session s1
    res = route_command("run command python build_docs.py", session_id="s1")
    assert "Pending approval" in res
    tickets = list_pending("s1")
    assert len(tickets) == 1
    tid = tickets[0].ticket_id
    # Attacker session tries to approve it
    attacker_res = route_command(f"approve {tid}", session_id="attacker")
    assert "Pending" in attacker_res or "No pending" in attacker_res or "expire" in attacker_res.lower()
    assert len(list_pending("s1")) == 1  # untouched
    # Owner approves — safe_exec is the executor, whitelist still applies
    owner_res = route_command(f"approve {tid}", session_id="s1")
    assert "Executed" in owner_res or "Failed" in owner_res  # safe_exec ran or errored cleanly
    assert len(list_pending("s1")) == 0


def test_remote_agent_session_is_distinct():
    from approval_service import REMOTE_SESSION_ID, DEFAULT_SESSION_ID
    assert REMOTE_SESSION_ID != DEFAULT_SESSION_ID
    ticket = create_ticket("remote cmd", session_id=REMOTE_SESSION_ID)
    with pytest.raises(ApprovalError):
        approve_ticket(ticket.ticket_id, DEFAULT_SESSION_ID, lambda a: "ran")
