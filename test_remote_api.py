import os
import pytest
from fastapi.testclient import TestClient

os.environ["SHERLY_REMOTE_API_KEY"] = "test_key_xyz"

from remote_api.server import app, API_KEY

client = TestClient(app)

def test_missing_api_key():
    response = client.post("/command", json={"text": "ls"})
    assert response.status_code == 403
    assert response.json() == {"detail": "Unauthorized"}

def test_wrong_api_key():
    response = client.post("/command", json={"text": "ls"}, headers={"x-api-key": "wrong_key"})
    assert response.status_code == 403
    assert response.json() == {"detail": "Unauthorized"}

def test_correct_api_key(mocker):
    # Mock requests.post
    mocker.patch("remote_api.server.requests.post")
    response = client.post("/command", json={"text": "ls"}, headers={"x-api-key": "test_key_xyz"})
    assert response.status_code == 200
