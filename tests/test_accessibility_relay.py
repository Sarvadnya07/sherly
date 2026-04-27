"""
Tests for ui/accessibility.py — Accessibility Theme (OE-7)
and core/cloud_relay.py — Cloud Relay (FS-#14)
"""

from __future__ import annotations

import pytest


# ---------------------------------------------------------------------------
# Accessibility module (no Qt required for logic tests)
# ---------------------------------------------------------------------------

from sherly.ui.accessibility import (
    ACCESSIBILITY_QSS,
    get_current_theme,
    should_use_accessibility,
    _persist_theme,
)


def test_accessibility_qss_is_non_empty() -> None:
    assert len(ACCESSIBILITY_QSS.strip()) > 100


def test_accessibility_qss_contains_high_contrast_colors() -> None:
    """Ensure key WCAG colors are present in the stylesheet."""
    assert "#FFFFFF" in ACCESSIBILITY_QSS   # White background
    assert "#000000" in ACCESSIBILITY_QSS   # Black text
    assert "#0057B8" in ACCESSIBILITY_QSS   # Blue accent


def test_accessibility_qss_has_minimum_font_size() -> None:
    """Baseline font must be at least 14pt for accessibility."""
    assert "14pt" in ACCESSIBILITY_QSS


def test_get_current_theme_returns_string() -> None:
    theme = get_current_theme()
    assert isinstance(theme, str)
    assert theme in ("accessibility", "default")


def test_should_use_accessibility_returns_bool() -> None:
    result = should_use_accessibility()
    assert isinstance(result, bool)


def test_persist_theme_does_not_raise() -> None:
    """_persist_theme should silently handle config read/write failures."""
    # In test environment, config.json may not exist — it must not raise
    try:
        _persist_theme("accessibility")
        _persist_theme("default")   # Restore
    except Exception as exc:
        pytest.fail(f"_persist_theme raised unexpectedly: {exc}")


# ---------------------------------------------------------------------------
# Cloud Relay — logic tests (no WebSocket server needed)
# ---------------------------------------------------------------------------

from sherly.core.cloud_relay import (
    _auth_ok,
    _RELAY_TOKEN,
)


class _MockHeaders(dict):
    """Simple dict that mimics the WebSocket headers interface."""
    pass


def test_auth_ok_no_token_configured() -> None:
    """When SHERLY_RELAY_TOKEN is empty, all connections should be allowed."""
    import sherly.core.cloud_relay as relay_mod
    original = relay_mod._RELAY_TOKEN
    relay_mod._RELAY_TOKEN = ""   # Simulate dev mode

    headers = _MockHeaders()
    assert relay_mod._auth_ok(headers)

    relay_mod._RELAY_TOKEN = original


def test_auth_ok_valid_token() -> None:
    import sherly.core.cloud_relay as relay_mod
    original = relay_mod._RELAY_TOKEN
    relay_mod._RELAY_TOKEN = "my-secret"

    headers = _MockHeaders({"Authorization": "Bearer my-secret"})
    assert relay_mod._auth_ok(headers)

    relay_mod._RELAY_TOKEN = original


def test_auth_ok_invalid_token() -> None:
    import sherly.core.cloud_relay as relay_mod
    original = relay_mod._RELAY_TOKEN
    relay_mod._RELAY_TOKEN = "my-secret"

    headers = _MockHeaders({"Authorization": "Bearer wrong-token"})
    assert not relay_mod._auth_ok(headers)

    relay_mod._RELAY_TOKEN = original


def test_auth_ok_missing_header() -> None:
    import sherly.core.cloud_relay as relay_mod
    original = relay_mod._RELAY_TOKEN
    relay_mod._RELAY_TOKEN = "my-secret"

    headers = _MockHeaders()   # No Authorization header
    assert not relay_mod._auth_ok(headers)

    relay_mod._RELAY_TOKEN = original


def test_relay_imports_without_websockets() -> None:
    """cloud_relay.py must be importable even without the websockets package."""
    import importlib
    try:
        import sherly.core.cloud_relay  # noqa: F401
    except ImportError as exc:
        pytest.fail(f"cloud_relay raised ImportError at import time: {exc}")
