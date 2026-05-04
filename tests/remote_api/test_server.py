import pytest
from fastapi.testclient import TestClient
import os

from remote_api.server import app
import remote_api.server as server

def test_unauthorized_access(monkeypatch):
    monkeypatch.setenv("SHERLY_REMOTE_API_KEY", "test_key")
    server.API_KEY = "test_key"
    with TestClient(app) as client:
        response = client.post("/command", json={"text": "ls"})
        assert response.status_code == 403

def test_authorized_access(monkeypatch):
    monkeypatch.setenv("SHERLY_REMOTE_API_KEY", "test_key")
    server.API_KEY = "test_key"

    import requests
    def mock_post(*args, **kwargs):
        class MockResponse:
            def json(self): return {"response": "mocked"}
            def raise_for_status(self): pass
        return MockResponse()

    monkeypatch.setattr(requests, "post", mock_post)

    with TestClient(app) as client:
        response = client.post("/command", json={"text": "ls"}, headers={"x-api-key": "test_key"})
        assert response.status_code == 200
        assert response.json() == {"response": "mocked"}
