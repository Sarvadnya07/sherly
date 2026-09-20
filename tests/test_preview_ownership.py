"""
PREVIEW SESSION OWNERSHIP — tests/test_preview_ownership.py
Regression suite for session-scoped patch previews.

Proves behaviorally: cross-session isolation (no existence oracle),
immutable owner/payload, single-use application, concurrency safety,
hash-conflict protection, backups, undo, and approval↔preview identity
agreement.
"""

from __future__ import annotations

import threading

import pytest

import approval_service
from approval_service import ApprovalError
from tools.preview import (
    apply_preview,
    consume_preview,
    discard_preview,
    get_preview,
    has_preview,
    save_preview,
)


@pytest.fixture(autouse=True)
def _clean(tmp_path, monkeypatch):
    approval_service.reset_for_tests()
    import tools.preview as pv
    monkeypatch.setattr(pv, "_preview_store", {})
    monkeypatch.setattr(pv, "backup_dir", str(tmp_path / "backups"))
    yield
    approval_service.reset_for_tests()


def _changes(path, old="a\n", new="b\n"):
    return [{"file": str(path), "old": old, "new": new}]


def _mkfile(tmp_path, name="t.txt", content="a\n"):
    p = tmp_path / name
    p.write_text(content)
    return p


def pv_backup_dir() -> str:
    import tools.preview as pv
    return pv.backup_dir


# ── Session scoping ──────────────────────────────────────────────────────────

def test_preview_is_session_scoped(tmp_path):
    pid = save_preview(_changes(_mkfile(tmp_path)), session_id="s1")
    assert has_preview(pid, session_id="s1") is True
    assert has_preview(pid, session_id="s2") is False


def test_wrong_session_cannot_get_preview(tmp_path):
    pid = save_preview(_changes(_mkfile(tmp_path)), session_id="s1")
    assert get_preview(pid, session_id="attacker") is None


def test_wrong_session_cannot_apply_preview(tmp_path):
    p = _mkfile(tmp_path)
    pid = save_preview(_changes(p), session_id="s1")
    res = apply_preview(pid, session_id="attacker")
    assert res == "Invalid preview ID"
    assert p.read_text() == "a\n"          # nothing written
    # Owner can still apply
    assert "applied successfully" in apply_preview(pid, session_id="s1")
    assert p.read_text() == "b\n"


def test_wrong_session_cannot_cancel_preview(tmp_path):
    pid = save_preview(_changes(_mkfile(tmp_path)), session_id="s1")
    assert discard_preview(pid, session_id="attacker") is False
    assert has_preview(pid, session_id="s1") is True
    assert discard_preview(pid, session_id="s1") is True


def test_wrong_session_cannot_list_preview(tmp_path):
    pid = save_preview(_changes(_mkfile(tmp_path)), session_id="s1")
    assert has_preview(pid, session_id="s2") is False
    assert get_preview(pid, session_id="s2") is None


def test_unknown_preview_no_existence_oracle():
    # Unknown ID and foreign ID produce the identical error/message.
    def _try(pid, sid):
        try:
            consume_preview(pid, session_id=sid)
            return None
        except ApprovalError as e:
            return (e.code, e.public_message)
    unknown = _try("doesnotexist1", "s1")
    foreign = save_preview([], session_id="sX")
    foreign_res = _try(foreign, "s1")
    assert unknown is not None and foreign_res is not None
    assert unknown == foreign_res
    assert unknown[0] == "NOT_FOUND"


# ── Immutability & single-use ────────────────────────────────────────────────

def test_preview_payload_is_immutable(tmp_path):
    p = _mkfile(tmp_path)
    changes = _changes(p)
    pid = save_preview(changes, session_id="s1")
    changes[0]["new"] = "HACKED\n"                    # mutate caller's copy
    staged = get_preview(pid, session_id="s1")
    assert staged[0]["new"] == "b\n"
    apply_preview(pid, session_id="s1")
    assert p.read_text() == "b\n"                     # original payload applied


def test_preview_owner_is_immutable():
    pid = save_preview([], session_id="s1")
    with pytest.raises(ApprovalError):
        consume_preview(pid, session_id="s2")         # cannot re-bind by use
    # No API exists to change session_id; verify stored entry directly.
    import tools.preview as pv
    assert pv._preview_store[pid]["session_id"] == "s1"


def test_preview_single_use(tmp_path):
    p = _mkfile(tmp_path)
    pid = save_preview(_changes(p), session_id="s1")
    assert "applied successfully" in apply_preview(pid, session_id="s1")
    assert apply_preview(pid, session_id="s1") == "Invalid preview ID"
    assert apply_preview(pid, session_id="s1") == "Invalid preview ID"
    assert p.read_text() == "b\n"                     # written exactly once


# ── Concurrency ──────────────────────────────────────────────────────────────

def test_concurrent_apply_only_executes_once(tmp_path):
    p = _mkfile(tmp_path)
    pid = save_preview(_changes(p), session_id="s1")
    barrier = threading.Barrier(6)
    results: list[str] = []

    def worker(sid):
        barrier.wait()
        results.append(apply_preview(pid, session_id=sid))

    threads = [threading.Thread(target=worker, args=("s1",)) for _ in range(6)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert sum("applied successfully" in r for r in results) == 1
    assert results.count("Invalid preview ID") == 5


def test_two_sessions_two_previews_isolated(tmp_path):
    p1, p2 = _mkfile(tmp_path, "a.txt", "x\n"), _mkfile(tmp_path, "b.txt", "1\n")
    id1 = save_preview(_changes(p1, "x\n", "y\n"), session_id="s1")
    id2 = save_preview(_changes(p2, "1\n", "2\n"), session_id="s2")
    assert "applied successfully" in apply_preview(id1, session_id="s1")
    # s2's preview untouched
    assert has_preview(id2, session_id="s2") is True
    assert p2.read_text() == "1\n"
    assert "applied successfully" in apply_preview(id2, session_id="s2")


def test_apply_after_removal_rejected(tmp_path):
    pid = save_preview(_changes(_mkfile(tmp_path)), session_id="s1")
    discard_preview(pid, session_id="s1")
    assert apply_preview(pid, session_id="s1") == "Invalid preview ID"


def test_reconnect_preserves_ownership(tmp_path):
    pid = save_preview(_changes(_mkfile(tmp_path)), session_id="device-A")
    assert apply_preview(pid, session_id="device-A-2") == "Invalid preview ID"
    assert "applied successfully" in apply_preview(pid, session_id="device-A")


# ── Preserved guarantees: conflict, backup, undo ─────────────────────────────

def test_hash_conflict_still_blocks_apply(tmp_path):
    p = _mkfile(tmp_path, content="a\n")
    pid = save_preview(_changes(p, "a\n", "b\n"), session_id="s1")
    p.write_text("externally modified\n")             # base changed after staging
    res = apply_preview(pid, session_id="s1")
    assert "Conflict detected" in res
    assert p.read_text() == "externally modified\n"   # NOT overwritten


def test_backup_created_before_apply(tmp_path):
    p = _mkfile(tmp_path)
    pid = save_preview(_changes(p), session_id="s1")
    apply_preview(pid, session_id="s1")
    from pathlib import Path as _Path
    # backup_file() flattens the full path into a safe filename
    safe_name = str(p).replace("/", "_").replace("\\", "_").replace(":", "_")
    backup = _Path(pv_backup_dir()) / safe_name
    assert backup.exists()
    assert backup.read_text(encoding="utf-8") == "a\n"


def test_undo_remains_available_after_apply(tmp_path):
    p = _mkfile(tmp_path, content="original\n")
    pid = save_preview(_changes(p, "original\n", "patched\n"), session_id="s1")
    apply_preview(pid, session_id="s1")
    assert p.read_text() == "patched\n"
    from action_manager import undo_last
    msg = undo_last()
    assert "Restored" in msg
    assert p.read_text() == "original\n"


# ── Approval ↔ preview identity agreement ────────────────────────────────────

def test_approval_and_preview_sessions_match(tmp_path, monkeypatch):
    """The approve-command path applies the preview only for the owner session."""
    p = _mkfile(tmp_path)
    pid = save_preview(_changes(p), session_id="s1")
    from command_router import route_command
    res = route_command(f"approve {pid}", session_id="attacker")
    assert "Invalid preview" in res or "No pending" in res or "expire" in res.lower()
    assert p.read_text() == "a\n"                     # foreign apply rejected
    res = route_command(f"approve {pid}", session_id="s1")
    assert "applied successfully" in res
    assert p.read_text() == "b\n"


def test_fix_project_creates_preview_for_caller_session(monkeypatch, tmp_path):
    """apply_last_fix binds the created preview to the routing session."""
    import tools.fix_project as fp
    from approval_service import DEFAULT_SESSION_ID
    captured = {}

    def fake_save(changes, session_id=DEFAULT_SESSION_ID, preview_id=None):
        captured["session_id"] = session_id
        return "pid123"

    monkeypatch.setattr(fp, "save_preview", fake_save)
    monkeypatch.setattr(fp, "generate_multi_diff", lambda *a, **k: "diff")
    fp.LAST_FIX_CONTEXT.update({
        "command": "pytest", "error": "boom",
        "target_files": [str(_mkfile(tmp_path))],
    })

    def fake_fix_data(error, ctx, ask_model):
        return {"confidence": 90, "reason": "r",
                "changes": [{"file": fp.LAST_FIX_CONTEXT["target_files"][0], "new": "z"}]}

    monkeypatch.setattr(fp, "generate_multi_fix", fake_fix_data)
    fp.apply_last_fix(lambda *a, **k: "", session_id="remote-agent")
    assert captured["session_id"] == "remote-agent"
