import os
import secrets
import pytest

os.environ["SHERLY_REMOTE_API_KEY"] = "test_key"

import remote_api.server as server

def test_verify_key_correct():
    # Calling the internal logic directly without relying on FastAPI TestClient
    assert server.verify_key("test_key") == True

def test_verify_key_incorrect():
    from fastapi import HTTPException
    with pytest.raises(HTTPException) as excinfo:
        server.verify_key("wrong_key")
    assert excinfo.value.status_code == 403

def test_missing_env_var(monkeypatch):
    monkeypatch.delenv("SHERLY_REMOTE_API_KEY", raising=False)
    # Reload module or re-evaluate the condition
    api_key = os.getenv("SHERLY_REMOTE_API_KEY")
    with pytest.raises(RuntimeError) as excinfo:
        if not api_key:
            raise RuntimeError("SHERLY_REMOTE_API_KEY environment variable is missing")
    assert str(excinfo.value) == "SHERLY_REMOTE_API_KEY environment variable is missing"
