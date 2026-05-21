"""
Tests for core/federated.py — Differential Privacy Knowledge Sharing (FS-#12)
"""

from __future__ import annotations

import json

import pytest

from sherly.core.federated import (
    FederatedKnowledge,
    _laplace_noise,
    _scrub_paths,
    _scrub_pii,
    _sign,
    _verify,
)


# ---------------------------------------------------------------------------
# Privacy primitives
# ---------------------------------------------------------------------------

def test_laplace_noise_is_numeric() -> None:
    noise = _laplace_noise()
    assert isinstance(noise, float)


def test_laplace_noise_distribution() -> None:
    """Check that Laplace noise has non-zero variance (not always 0)."""
    samples = [_laplace_noise() for _ in range(50)]
    assert len(set(round(s, 6) for s in samples)) > 1, "Noise must vary"


def test_scrub_windows_path() -> None:
    result = _scrub_paths("Error in C:\\Users\\ASUS\\project\\main.py")
    assert "ASUS" not in result
    assert "$HOME" in result


def test_scrub_unix_path() -> None:
    result = _scrub_paths("File: /home/john/src/app.py")
    assert "john" not in result
    assert "$HOME" in result


def test_scrub_pii_email() -> None:
    result = _scrub_pii("Contact admin@example.com for help.")
    assert "admin@example.com" not in result
    assert "[EMAIL]" in result


def test_scrub_pii_ip() -> None:
    result = _scrub_pii("Request from 192.168.0.1")
    assert "192.168.0.1" not in result
    assert "[IP]" in result


# ---------------------------------------------------------------------------
# HMAC signing
# ---------------------------------------------------------------------------

def test_sign_returns_string() -> None:
    sig = _sign("test payload")
    assert isinstance(sig, str)
    assert len(sig) == 64  # SHA-256 hex digest


def test_verify_valid_signature() -> None:
    payload = '{"error_type": "ImportError"}'
    sig     = _sign(payload)
    assert _verify(payload, sig)


def test_verify_tampered_payload() -> None:
    payload = '{"error_type": "ImportError"}'
    sig     = _sign(payload)
    tampered = payload.replace("Import", "Attribute")
    assert not _verify(tampered, sig)


# ---------------------------------------------------------------------------
# FederatedKnowledge.generate_snippet
# ---------------------------------------------------------------------------

@pytest.fixture
def federated() -> FederatedKnowledge:
    return FederatedKnowledge()


def test_generate_snippet_returns_json(federated: FederatedKnowledge) -> None:
    snippet = federated.generate_snippet(
        error_trace="ImportError: No module named 'requests'",
        solution="pip install requests",
    )
    parsed = json.loads(snippet)
    assert "payload" in parsed
    assert "signature" in parsed


def test_generate_snippet_scrubs_path(federated: FederatedKnowledge) -> None:
    snippet = federated.generate_snippet(
        error_trace="Error in C:\\Users\\ASUS\\project",
        solution="fix applied",
    )
    assert "ASUS" not in snippet


def test_generate_snippet_privacy_score_in_range(federated: FederatedKnowledge) -> None:
    snippet = federated.generate_snippet("ImportError", "fix")
    payload = json.loads(snippet)["payload"]
    assert 0.0 <= payload["privacy_score"] <= 1.0


def test_generate_snippet_detects_error_type(federated: FederatedKnowledge) -> None:
    snippet = federated.generate_snippet("TypeError: unsupported operand", "cast to int")
    payload = json.loads(snippet)["payload"]
    assert payload["error_type"] == "TypeError"


# ---------------------------------------------------------------------------
# FederatedKnowledge.verify_snippet
# ---------------------------------------------------------------------------

def test_verify_snippet_valid(federated: FederatedKnowledge) -> None:
    snippet = federated.generate_snippet("ValueError", "handle it")
    payload = federated.verify_snippet(snippet)
    assert payload is not None
    assert "error_type" in payload


def test_verify_snippet_tampered_returns_none(federated: FederatedKnowledge) -> None:
    snippet  = federated.generate_snippet("KeyError", "add default")
    envelope = json.loads(snippet)
    # Tamper with the payload
    envelope["payload"]["privacy_score"] = 9999
    tampered = json.dumps(envelope)
    assert federated.verify_snippet(tampered) is None


def test_verify_snippet_invalid_json_returns_none(federated: FederatedKnowledge) -> None:
    assert federated.verify_snippet("not json at all") is None
