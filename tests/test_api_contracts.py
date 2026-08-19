"""
CONTRACT TESTS — tests/test_api_contracts.py
Verifies FastAPI REST contracts, Pydantic validation boundaries,
and WebSocket event envelopes.
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from backend.main import app
from backend.api.schemas.contracts import (
    ChatRequest,
    ChatResponse,
    ModelSelectRequest,
    ModelModeRequest,
    ApiKeyRequest,
    PendingApproval,
    TerminalRunRequest,
    FileWriteRequest,
    SherlyEvent,
)


@pytest.fixture
def client():
    return TestClient(app)


# ── REST Schema Validation Tests ──────────────────────────────────────────────

def test_chat_request_validation():
    req = ChatRequest(prompt="Write a python function to sort a list")
    assert req.prompt == "Write a python function to sort a list"
    assert req.file_attachment is None

    # Empty prompt fails validation
    with pytest.raises(Exception):
        ChatRequest(prompt="")


def test_model_mode_request_validation():
    req = ModelModeRequest(mode="auto")
    assert req.mode == "auto"

    req_man = ModelModeRequest(mode="manual")
    assert req_man.mode == "manual"

    with pytest.raises(Exception):
        ModelModeRequest(mode="invalid_mode")


def test_api_key_request_validation():
    req = ApiKeyRequest(provider="openai", api_key="sk-testkey123")
    assert req.provider == "openai"
    assert req.api_key == "sk-testkey123"

    with pytest.raises(Exception):
        ApiKeyRequest(provider="unknown_provider", api_key="key")


def test_terminal_run_request_validation():
    req = TerminalRunRequest(command="python --version")
    assert req.command == "python --version"

    with pytest.raises(Exception):
        TerminalRunRequest(command="")


# ── WebSocket Envelope Serialization Tests ───────────────────────────────────

def test_websocket_envelope_serialization():
    event = SherlyEvent(
        event_type="status",
        payload={"status": "thinking", "prompt": "test prompt"},
        request_id="req_12345",
    )
    assert event.event_type == "status"
    assert event.payload["status"] == "thinking"
    assert event.request_id == "req_12345"
    assert event.timestamp > 0


# ── FastAPI Endpoint Contract Smoke Tests ────────────────────────────────────

def test_health_endpoint_contract(client):
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "version" in data


def test_models_endpoint_contract(client):
    response = client.get("/api/models")
    assert response.status_code == 200
    data = response.json()
    assert "mode" in data
    assert "is_ollama_running" in data
    assert "models" in data
    assert isinstance(data["models"], list)


def test_settings_endpoint_contract(client):
    response = client.get("/api/settings")
    assert response.status_code == 200
    data = response.json()
    assert "auto_mode" in data
    assert "model_mode" in data
    assert "api_keys_configured" in data


def test_voice_status_contract(client):
    response = client.get("/api/voice/status")
    assert response.status_code == 200
    data = response.json()
    assert "is_listening" in data
    assert "is_speaking" in data


def test_files_tree_contract(client):
    response = client.get("/api/files/tree")
    assert response.status_code == 200
    data = response.json()
    assert "name" in data
    assert "is_dir" in data


def test_actions_approvals_contract(client):
    response = client.get("/api/actions/approvals")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
