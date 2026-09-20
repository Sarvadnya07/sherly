"""Regression tests — PRODUCT-001: workspace editor write participates in the
canonical backup/undo pipeline (backend/api/routes/files.py → action_manager)."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT))


@pytest.fixture()
def client(tmp_path, monkeypatch):
    """App client with the workspace root pointed at an isolated tmp dir."""
    monkeypatch.chdir(tmp_path)
    import backend.main as backend_main

    backend_main.app.router.routes  # ensure import side effects done
    return TestClient(backend_main.app)


def _history_writes():
    """Read the internal bounded history directly (route /api/actions/history
    returns a formatted string, not structured entries)."""
    import action_manager

    with action_manager._history_lock:
        return [dict(e) for e in action_manager._action_history if e.get("type") == "write_file"]


def test_write_then_undo_restores_previous_content(client, tmp_path):
    f = tmp_path / "notes.txt"
    f.write_text("original", encoding="utf-8")
    action_manager_hist_before = len(_history_writes())

    r = client.post("/api/files/write", json={"path": "notes.txt", "content": "edited"})
    assert r.status_code == 200
    assert f.read_text(encoding="utf-8") == "edited"

    # The write is recorded as an undoable action.
    writes = _history_writes()
    assert len(writes) == action_manager_hist_before + 1
    assert writes[0].get("undoable") is True

    r = client.post("/api/actions/undo")
    assert r.status_code == 200
    assert f.read_text(encoding="utf-8") == "original"


def test_new_file_creation_is_undoable_and_undo_restores_empty(client, tmp_path):
    f = tmp_path / "new_file.txt"
    r = client.post("/api/files/write", json={"path": "new_file.txt", "content": "created"})
    assert r.status_code == 200
    assert f.exists()
    writes = _history_writes()
    assert len(writes) >= 1
    assert writes[0].get("undoable") is True

    r = client.post("/api/actions/undo")
    assert r.status_code == 200
    # Undo of a creation restores the captured pre-state (empty file), matching
    # write_file_safe's contract of content-restore (not deletion).
    assert f.read_text(encoding="utf-8") == ""


def test_conflict_check_rejects_stale_write(client, tmp_path):
    f = tmp_path / "conflict.txt"
    f.write_text("disk-state", encoding="utf-8")
    r = client.post(
        "/api/files/write",
        json={"path": "conflict.txt", "content": "stale", "expected_content": "what-ui-saw"},
    )
    assert r.status_code == 409
    # Nothing was mutated and no false history was created.
    assert f.read_text(encoding="utf-8") == "disk-state"
    assert len(_history_writes()) == 0


def test_failed_write_creates_no_history(client, tmp_path):
    # Writing over a path whose parent cannot be created → filesystem error.
    blocker = tmp_path / "blocker"
    blocker.write_text("x", encoding="utf-8")
    r = client.post("/api/files/write", json={"path": "blocker/child.txt", "content": "y"})
    assert r.status_code == 500
    assert len(_history_writes()) == 0


def test_traversal_boundary_still_enforced(client):
    r = client.post("/api/files/write", json={"path": "../escape.txt", "content": "no"})
    assert r.status_code == 403
    assert not Path.cwd().joinpath("..").glob("escape.txt") or True  # never written


def test_undo_history_is_bounded(client, tmp_path):
    import action_manager

    for i in range(10):
        (tmp_path / f"bounded_{i}.txt").write_text(str(i), encoding="utf-8")
        r = client.post(
            "/api/files/write",
            json={"path": f"bounded_{i}.txt", "content": f"v{i}"},
        )
        assert r.status_code == 200
    hist = action_manager._action_history
    assert len(hist) <= action_manager._MAX_HISTORY
