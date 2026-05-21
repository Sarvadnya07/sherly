"""
Tests for core/session_manager.py — Multi-User Session Support (FS-#15)
"""

from __future__ import annotations

import time

import pytest

from sherly.core.session_manager import (
    SessionContext,
    SessionManager,
    get_session_manager,
    new_session_token,
)


# ---------------------------------------------------------------------------
# SessionContext
# ---------------------------------------------------------------------------

def test_session_context_defaults() -> None:
    ctx = SessionContext()
    assert ctx.mode  == "fast"
    assert ctx.phase == "A"
    assert isinstance(ctx.session_id, str)
    assert len(ctx.session_id) > 0


def test_session_context_touch_updates_timestamp() -> None:
    ctx  = SessionContext()
    old  = ctx.last_active
    time.sleep(0.01)
    ctx.touch()
    assert ctx.last_active > old


def test_session_context_not_expired_immediately() -> None:
    ctx = SessionContext()
    assert not ctx.is_expired()


def test_session_context_to_dict_has_required_keys() -> None:
    ctx  = SessionContext()
    d    = ctx.to_dict()
    for key in ("session_id", "mode", "phase", "pending", "last_active"):
        assert key in d, f"Missing key in to_dict(): {key}"


# ---------------------------------------------------------------------------
# SessionManager
# ---------------------------------------------------------------------------

@pytest.fixture
def mgr() -> SessionManager:
    return SessionManager()


def test_get_or_create_returns_context(mgr: SessionManager) -> None:
    ctx = mgr.get_or_create("token_a")
    assert isinstance(ctx, SessionContext)
    assert ctx.session_id == "token_a"


def test_get_or_create_same_token_returns_same_ctx(mgr: SessionManager) -> None:
    ctx1 = mgr.get_or_create("token_b")
    ctx2 = mgr.get_or_create("token_b")
    assert ctx1 is ctx2


def test_different_tokens_are_isolated(mgr: SessionManager) -> None:
    ctx1 = mgr.get_or_create("user_1")
    ctx2 = mgr.get_or_create("user_2")
    ctx1.mode  = "deep"
    ctx1.phase = "C"
    assert ctx2.mode  == "fast"
    assert ctx2.phase == "A"


def test_get_returns_none_for_unknown(mgr: SessionManager) -> None:
    assert mgr.get("totally_unknown_token") is None


def test_destroy_removes_session(mgr: SessionManager) -> None:
    mgr.get_or_create("to_delete")
    mgr.destroy("to_delete")
    assert mgr.get("to_delete") is None


def test_active_count_increments(mgr: SessionManager) -> None:
    before = mgr.active_count()
    mgr.get_or_create("count_test_1")
    mgr.get_or_create("count_test_2")
    assert mgr.active_count() >= before + 2


def test_list_sessions_returns_list(mgr: SessionManager) -> None:
    mgr.get_or_create("list_test")
    sessions = mgr.list_sessions()
    assert isinstance(sessions, list)
    assert any(s["session_id"] == "list_test" for s in sessions)


# ---------------------------------------------------------------------------
# Module-level singleton
# ---------------------------------------------------------------------------

def test_get_session_manager_returns_singleton() -> None:
    m1 = get_session_manager()
    m2 = get_session_manager()
    assert m1 is m2


def test_new_session_token_is_unique() -> None:
    tokens = {new_session_token() for _ in range(10)}
    assert len(tokens) == 10  # All unique


# ---------------------------------------------------------------------------
# Mutation isolation
# ---------------------------------------------------------------------------

def test_session_mode_mutation_isolated(mgr: SessionManager) -> None:
    ctx_a = mgr.get_or_create("iso_a")
    ctx_b = mgr.get_or_create("iso_b")
    ctx_a.mode = "dev"
    assert ctx_b.mode == "fast"


def test_pending_actions_isolated(mgr: SessionManager) -> None:
    ctx_a = mgr.get_or_create("pend_a")
    ctx_b = mgr.get_or_create("pend_b")
    ctx_a.pending_actions["cmd1"] = {"status": "pending"}
    assert "cmd1" not in ctx_b.pending_actions
