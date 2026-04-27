"""
Tests for:
  services/async_model.py    — FS-#1 (async httpx layer) + FS-#8 (Ollama health)
  ui/history_panel.py        — OE-3 (Conversation History Panel logic)
  services/conversation_memory.py — get_all_turns() addition
"""

from __future__ import annotations

import asyncio
import time
from unittest.mock import MagicMock, patch

import pytest


# ===========================================================================
# FS-#8 — Ollama health check
# ===========================================================================

from sherly.services.async_model import (
    check_ollama_health,
    _HEALTH_TTL,
)
import sherly.services.async_model as _am


def _reset_health_cache():
    _am._last_health_check = 0.0
    _am._last_health_status = None


def test_health_check_returns_healthy_when_ollama_responds():
    _reset_health_cache()
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    with patch("sherly.services.async_model._get_httpx", return_value=None):
        with patch("requests.get", return_value=mock_resp):
            healthy, msg = check_ollama_health()
    assert healthy is True
    assert "running" in msg.lower()


def test_health_check_returns_unhealthy_when_connection_refused():
    _reset_health_cache()
    with patch("sherly.services.async_model._get_httpx", return_value=None):
        with patch("requests.get", side_effect=ConnectionRefusedError("refused")):
            healthy, msg = check_ollama_health(auto_recover=False)
    assert healthy is False
    assert "ollama" in msg.lower()


def test_health_check_specific_message_references_ollama_serve():
    _reset_health_cache()
    with patch("sherly.services.async_model._get_httpx", return_value=None):
        with patch("requests.get", side_effect=Exception("conn refused")):
            _, msg = check_ollama_health(auto_recover=False)
    assert "ollama serve" in msg


def test_health_check_caches_positive_result():
    _reset_health_cache()
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    with patch("sherly.services.async_model._get_httpx", return_value=None):
        with patch("requests.get", return_value=mock_resp) as mock_get:
            check_ollama_health()   # primes cache
            _am._last_health_check = time.time()  # force within TTL
            _am._last_health_status = True
            healthy, _ = check_ollama_health()
            assert healthy is True
            # Second call hit cache — get() called only once
            assert mock_get.call_count == 1


def test_health_check_auto_recover_does_not_raise():
    _reset_health_cache()
    with patch("sherly.services.async_model._get_httpx", return_value=None):
        with patch("requests.get", side_effect=Exception("down")):
            with patch("sherly.services.async_model._try_auto_recover") as mock_recover:
                healthy, msg = check_ollama_health(auto_recover=True)
                assert not healthy
                mock_recover.assert_called_once()


def test_try_auto_recover_handles_ollama_not_in_path():
    """_try_auto_recover must not raise even if ollama isn't installed."""
    from sherly.services.async_model import _try_auto_recover
    with patch("subprocess.Popen", side_effect=FileNotFoundError("ollama")):
        _try_auto_recover()   # Should not raise


# ===========================================================================
# FS-#1 — Async model functions
# ===========================================================================

@pytest.mark.asyncio
async def test_async_ask_ollama_returns_string_on_connection_error():
    _reset_health_cache()
    with patch("sherly.services.async_model._get_httpx", return_value=None):
        with patch("requests.get", side_effect=Exception("down")):
            with patch("sherly.services.async_model.async_ask_ollama") as mock:
                mock.return_value = "connection failed"
                result = await mock("hello")
    assert isinstance(result, str)


@pytest.mark.asyncio
async def test_async_ask_openai_missing_key_returns_message():
    from sherly.services.async_model import async_ask_openai
    result = await async_ask_openai("test", api_key="YOUR_OPENAI_KEY")
    assert "missing" in result.lower() or "key" in result.lower()


@pytest.mark.asyncio
async def test_async_ask_gemini_missing_key_returns_message():
    from sherly.services.async_model import async_ask_gemini
    result = await async_ask_gemini("test", api_key="YOUR_GEMINI_KEY")
    assert "missing" in result.lower() or "key" in result.lower()


@pytest.mark.asyncio
async def test_async_ask_groq_missing_key_returns_message():
    from sherly.services.async_model import async_ask_groq
    result = await async_ask_groq("test", api_key="YOUR_GROQ_KEY")
    assert "missing" in result.lower() or "key" in result.lower()


@pytest.mark.asyncio
async def test_async_stream_ollama_yields_fallback_when_httpx_unavailable():
    from sherly.services.async_model import async_stream_ollama
    with patch("sherly.services.async_model._get_httpx", return_value=None):
        with patch("sherly.services.async_model.async_ask_ollama", return_value="fallback chunk"):
            chunks = []
            async for chunk in async_stream_ollama("hello"):
                chunks.append(chunk)
    assert len(chunks) >= 1
    assert all(isinstance(c, str) for c in chunks)


def test_ask_model_async_safe_returns_string():
    """Sync wrapper must return a string even when async machinery fails."""
    from sherly.services.async_model import ask_model_async_safe
    with patch("sherly.services.async_model.async_ask_model", side_effect=Exception("fail")):
        with patch("sherly.services.model_manager.ask_model", return_value="sync fallback"):
            result = ask_model_async_safe("hello", timeout=5.0)
    assert isinstance(result, str)


# ===========================================================================
# OE-3 — Conversation history: get_all_turns()
# ===========================================================================

from sherly.services.conversation_memory import (
    add_to_memory, clear_context, get_all_turns,
)


def test_get_all_turns_empty_session():
    clear_context("test_get_all")
    turns = get_all_turns("test_get_all")
    assert turns == []


def test_get_all_turns_returns_list_of_dicts():
    clear_context("test_turns_dicts")
    add_to_memory("hello", "hi there", session_id="test_turns_dicts")
    turns = get_all_turns("test_turns_dicts")
    assert len(turns) == 1
    assert "user" in turns[0]
    assert "assistant" in turns[0]
    assert "timestamp" in turns[0]


def test_get_all_turns_newest_first():
    clear_context("test_order")
    add_to_memory("msg1", "resp1", session_id="test_order")
    add_to_memory("msg2", "resp2", session_id="test_order")
    turns = get_all_turns("test_order")
    # Newest first — msg2 should be index 0
    assert turns[0]["user"] == "msg2"
    assert turns[1]["user"] == "msg1"


def test_get_all_turns_content_matches():
    clear_context("test_content")
    add_to_memory("what is python", "A programming language.", session_id="test_content")
    turns = get_all_turns("test_content")
    assert turns[0]["assistant"] == "A programming language."


def test_get_all_turns_respects_session_isolation():
    clear_context("sess_a")
    clear_context("sess_b")
    add_to_memory("user_a", "resp_a", session_id="sess_a")
    add_to_memory("user_b", "resp_b", session_id="sess_b")
    turns_a = get_all_turns("sess_a")
    turns_b = get_all_turns("sess_b")
    assert len(turns_a) == 1 and turns_a[0]["user"] == "user_a"
    assert len(turns_b) == 1 and turns_b[0]["user"] == "user_b"


# ===========================================================================
# OE-3 — HistoryPanel (headless / no-Qt)
# ===========================================================================

from sherly.ui.history_panel import ConversationHistoryPanel


def test_history_panel_initializes_without_qt():
    """Panel must not raise even when PySide6 is unavailable."""
    with patch("sherly.ui.history_panel._require_qt", return_value=False):
        panel = ConversationHistoryPanel(parent=None)
        assert panel.dock is None


def test_history_panel_add_entry_no_op_without_qt():
    """add_entry() must be silent when Qt is not available."""
    with patch("sherly.ui.history_panel._require_qt", return_value=False):
        panel = ConversationHistoryPanel(parent=None)
        panel.add_entry("hello", "world")   # Should not raise


def test_history_panel_refresh_no_op_without_qt():
    """refresh() must be silent when Qt is not available."""
    with patch("sherly.ui.history_panel._require_qt", return_value=False):
        panel = ConversationHistoryPanel(parent=None)
        panel.refresh()   # Should not raise
