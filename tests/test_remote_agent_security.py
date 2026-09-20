"""SEC-004 regression tests: remote undo is explicitly rejected; the local
agent's loopback bind contract is codified."""

from __future__ import annotations

from fastapi.testclient import TestClient

from remote_agent.agent import HOST, PORT, app

client = TestClient(app)


def test_remote_agent_binds_loopback_only():
    assert HOST == "127.0.0.1"


def test_remote_agent_default_port_is_local():
    assert PORT == 5001


def test_remote_undo_request_is_rejected_explicitly():
    r = client.post("/execute", json={"text": "undo"})
    assert r.status_code == 200
    body = r.json()["response"]
    assert "not available over remote" in body.lower()


def test_remote_undo_variant_is_rejected():
    r = client.post("/execute", json={"text": "undo last action"})
    assert r.status_code == 200
    assert "not available over remote" in r.json()["response"].lower()


def test_non_undo_command_is_not_intercepted(monkeypatch):
    calls = {}

    def fake_route(text, session_id=None):
        calls["text"] = text
        calls["session_id"] = session_id
        return "ok"

    monkeypatch.setattr("remote_agent.agent.route_command", fake_route)
    monkeypatch.setattr("remote_agent.agent.send_notification", lambda *_: None)
    r = client.post("/execute", json={"text": "list files"})
    assert r.status_code == 200
    assert r.json()["response"] == "ok"
    assert calls["text"] == "list files"
    # SEC-005: remote commands run under the distinct remote session identity
    from approval_service import REMOTE_SESSION_ID
    assert calls["session_id"] == REMOTE_SESSION_ID
