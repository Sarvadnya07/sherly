"""
ASYNC MODEL LAYER — async_model.py
Implements:
  FS-#1  Async I/O for LLM calls using httpx.AsyncClient.
          Provides async counterparts to the synchronous ask_model() / stream_model()
          API in model_manager.py so the event loop never blocks on network I/O.

          Uses httpx instead of requests for true async HTTP/2 support.
          Falls back to running the sync ask_model() in a thread pool executor
          if httpx is not installed (zero breaking change).

  FS-#8  Ollama health check + auto-recovery.
          check_ollama_health() pings GET /api/tags.
          If Ollama is not running, surfaces a specific "please start it" message
          and optionally spawns `ollama serve` in the background.

Usage:
    import asyncio
    from sherly.services.async_model import async_ask_model, check_ollama_health

    # Non-blocking LLM call from an async context:
    result = await async_ask_model("explain decorators in Python")

    # From synchronous code (runs in background thread):
    from sherly.services.async_model import ask_model_async_safe
    result = ask_model_async_safe("hello")

    # Health check:
    healthy, msg = check_ollama_health(auto_recover=True)
"""

from __future__ import annotations

import asyncio
import subprocess
import time
from typing import AsyncIterator

from sherly.utils.runtime_utils import log

# ---------------------------------------------------------------------------
# Lazy httpx import (FS-#24)
# ---------------------------------------------------------------------------
_httpx: object = None
_httpx_checked = False


def _get_httpx():
    global _httpx, _httpx_checked
    if not _httpx_checked:
        _httpx_checked = True
        try:
            import httpx as _h
            _httpx = _h
        except ImportError:
            _httpx = None
    return _httpx


# ---------------------------------------------------------------------------
# FS-#8 — Ollama Health Check + Auto-Recovery
# ---------------------------------------------------------------------------

_OLLAMA_BASE = "http://localhost:11434"
_HEALTH_TIMEOUT = 3.0
_last_health_check: float = 0.0
_last_health_status: bool | None = None
_HEALTH_TTL = 30.0   # Re-check at most every 30 seconds


def check_ollama_health(auto_recover: bool = False) -> tuple[bool, str]:
    """
    FS-#8: Check if the Ollama daemon is running.

    Returns (is_healthy: bool, message: str).

    If auto_recover=True and Ollama is not running, attempts to start
    `ollama serve` in the background. The caller should wait a few seconds
    before retrying.
    """
    global _last_health_check, _last_health_status

    # Cache result for TTL seconds to avoid hammering the health endpoint
    now = time.time()
    if _last_health_status is not None and (now - _last_health_check) < _HEALTH_TTL:
        if _last_health_status:
            return True, "Ollama is running."
        # Don't cache negative results — retry on every call if unhealthy

    httpx = _get_httpx()
    try:
        if httpx:
            import httpx as _h
            with _h.Client(timeout=_HEALTH_TIMEOUT) as client:
                r = client.get(f"{_OLLAMA_BASE}/api/tags")
                healthy = r.status_code == 200
        else:
            import requests
            r = requests.get(f"{_OLLAMA_BASE}/api/tags", timeout=_HEALTH_TIMEOUT)
            healthy = r.status_code == 200

        _last_health_check = now
        _last_health_status = healthy

        if healthy:
            log("[Ollama] Health check: OK")
            return True, "Ollama is running."
        else:
            return False, f"Ollama returned HTTP {r.status_code}."

    except Exception as exc:
        _last_health_status = False
        _last_health_check = now
        msg = (
            "Ollama is not running. Please start it with: `ollama serve`\n"
            f"  (detail: {exc})"
        )
        log(f"[Ollama] Health check failed: {exc}", level="warning")

        if auto_recover:
            _try_auto_recover()
            return False, msg + "\n  Auto-recovery attempted — please retry in ~3 seconds."

        return False, msg


def _try_auto_recover() -> None:
    """
    FS-#8: Attempt to start `ollama serve` in the background.
    Does NOT wait for it to be ready — caller should retry after a delay.
    """
    try:
        subprocess.Popen(
            ["ollama", "serve"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            creationflags=subprocess.CREATE_NO_WINDOW if hasattr(subprocess, "CREATE_NO_WINDOW") else 0,
        )
        log("[Ollama] Auto-recovery: spawned 'ollama serve' in background.", level="info")
    except FileNotFoundError:
        log("[Ollama] Auto-recovery failed: 'ollama' not found in PATH.", level="error")
    except Exception as exc:
        log(f"[Ollama] Auto-recovery error: {exc}", level="error")


# ---------------------------------------------------------------------------
# FS-#1 — Async ask_model (httpx-backed)
# ---------------------------------------------------------------------------

async def async_ask_ollama(
    prompt: str,
    model: str = "phi3",
    max_tokens: int = 120,
) -> str:
    """
    FS-#1: Non-blocking Ollama call using httpx.AsyncClient.
    """
    httpx = _get_httpx()
    if not httpx:
        return await _fallback_thread(prompt)

    import httpx as _h
    try:
        async with _h.AsyncClient(timeout=20.0) as client:
            r = await client.post(
                f"{_OLLAMA_BASE}/api/generate",
                json={
                    "model": model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {"num_predict": max_tokens},
                },
            )
            r.raise_for_status()
            return r.json().get("response", "")
    except _h.ConnectError:
        healthy, msg = check_ollama_health(auto_recover=True)
        return f"Ollama connection failed. {msg}"
    except Exception as exc:
        log(f"[AsyncModel/Ollama] error: {exc}", level="error")
        return f"LLM error: {exc}"


async def async_ask_openai(
    prompt: str,
    api_key: str,
    model: str = "gpt-4o-mini",
    max_tokens: int = 120,
) -> str:
    """FS-#1: Non-blocking OpenAI call using httpx.AsyncClient."""
    if not api_key or api_key.startswith("YOUR_"):
        return "OpenAI API key is missing."

    httpx = _get_httpx()
    if not httpx:
        return await _fallback_thread(prompt)

    import httpx as _h
    try:
        async with _h.AsyncClient(timeout=15.0) as client:
            r = await client.post(
                "https://api.openai.com/v1/chat/completions",
                headers={"Authorization": f"Bearer {api_key}"},
                json={
                    "model": model,
                    "messages": [{"role": "user", "content": prompt}],
                    "max_tokens": max_tokens,
                },
            )
            r.raise_for_status()
            return r.json()["choices"][0]["message"]["content"]
    except Exception as exc:
        log(f"[AsyncModel/OpenAI] error: {exc}", level="error")
        return f"LLM error: {exc}"


async def async_ask_gemini(
    prompt: str,
    api_key: str,
    max_tokens: int = 120,
) -> str:
    """FS-#1: Non-blocking Gemini call using httpx.AsyncClient."""
    if not api_key or api_key.startswith("YOUR_"):
        return "Gemini API key is missing."

    httpx = _get_httpx()
    if not httpx:
        return await _fallback_thread(prompt)

    import httpx as _h
    url = (
        f"https://generativelanguage.googleapis.com/v1beta/models/"
        f"gemini-1.5-flash:generateContent?key={api_key}"
    )
    try:
        async with _h.AsyncClient(timeout=15.0) as client:
            r = await client.post(
                url,
                json={
                    "contents": [{"role": "user", "parts": [{"text": prompt}]}],
                    "generationConfig": {"maxOutputTokens": max_tokens},
                },
            )
            r.raise_for_status()
            return r.json()["candidates"][0]["content"]["parts"][0]["text"]
    except Exception as exc:
        log(f"[AsyncModel/Gemini] error: {exc}", level="error")
        return f"LLM error: {exc}"


async def async_ask_groq(
    prompt: str,
    api_key: str,
    model: str = "llama3-70b-8192",
    max_tokens: int = 120,
) -> str:
    """FS-#1: Non-blocking Groq call using httpx.AsyncClient."""
    if not api_key or api_key.startswith("YOUR_"):
        return "Groq API key is missing."

    httpx = _get_httpx()
    if not httpx:
        return await _fallback_thread(prompt)

    import httpx as _h
    try:
        async with _h.AsyncClient(timeout=15.0) as client:
            r = await client.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers={"Authorization": f"Bearer {api_key}"},
                json={
                    "model": model,
                    "messages": [{"role": "user", "content": prompt}],
                    "max_tokens": max_tokens,
                },
            )
            r.raise_for_status()
            return r.json()["choices"][0]["message"]["content"]
    except Exception as exc:
        log(f"[AsyncModel/Groq] error: {exc}", level="error")
        return f"LLM error: {exc}"


# ---------------------------------------------------------------------------
# FS-#1 — Unified async_ask_model dispatcher
# ---------------------------------------------------------------------------

async def async_ask_model(
    prompt: str,
    model_override: str | None = None,
    store_history: bool = False,
    use_context: bool = False,
) -> str:
    """
    FS-#1: Unified async LLM dispatcher.

    Reads the current model from config (same as synchronous ask_model()),
    dispatches to the appropriate async provider, and optionally stores the
    exchange in conversation memory.
    """
    try:
        from sherly.config.config_manager import get_current_model, get_api_key
    except Exception:
        return await _fallback_thread(prompt)

    model = model_override or get_current_model()

    if model in ("openai", "gpt", "gpt-4o-mini"):
        result = await async_ask_openai(prompt, get_api_key("openai") or "")
    elif model in ("gemini", "gemini-1.5-flash"):
        result = await async_ask_gemini(prompt, get_api_key("gemini") or "")
    elif model in ("groq", "llama3", "llama3-70b"):
        result = await async_ask_groq(prompt, get_api_key("groq") or "")
    else:
        result = await async_ask_ollama(prompt, model=model)

    result = (result or "")[:500]   # Hard output cap

    if store_history:
        try:
            from sherly.services.conversation_memory import add_to_memory
            add_to_memory(prompt, result)
        except Exception:
            pass

    return result


async def async_stream_ollama(
    prompt: str,
    model: str = "phi3",
) -> AsyncIterator[str]:
    """
    FS-#1: Streaming async generator for Ollama.
    Yields token strings as they arrive.
    """
    httpx = _get_httpx()
    if not httpx:
        # Fallback: yield entire response as single chunk
        result = await async_ask_ollama(prompt, model)
        yield result
        return

    import httpx as _h
    try:
        async with _h.AsyncClient(timeout=60.0) as client:
            async with client.stream(
                "POST",
                f"{_OLLAMA_BASE}/api/generate",
                json={"model": model, "prompt": prompt, "stream": True},
            ) as response:
                response.raise_for_status()
                async for line in response.aiter_lines():
                    if line.strip():
                        try:
                            data = __import__("json").loads(line)
                            token = data.get("response", "")
                            if token:
                                yield token
                            if data.get("done", False):
                                break
                        except Exception:
                            continue
    except Exception as exc:
        log(f"[AsyncModel/stream] error: {exc}", level="error")
        yield f"Stream error: {exc}"


# ---------------------------------------------------------------------------
# Sync-compatible wrapper — use from non-async code
# ---------------------------------------------------------------------------

async def _fallback_thread(prompt: str) -> str:
    """Run synchronous ask_model() in a thread pool so async callers don't block."""
    loop = asyncio.get_event_loop()
    try:
        from sherly.services.model_manager import ask_model
        return await loop.run_in_executor(None, ask_model, prompt)
    except Exception as exc:
        return f"LLM unavailable: {exc}"


def ask_model_async_safe(prompt: str, timeout: float = 20.0) -> str:
    """
    FS-#1: Call async_ask_model() from synchronous code.
    Creates a new event loop if one isn't running.
    """
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # We're inside an existing event loop — submit as a task
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor(max_workers=1) as ex:
                future = ex.submit(asyncio.run, async_ask_model(prompt))
                return future.result(timeout=timeout)
        else:
            return loop.run_until_complete(async_ask_model(prompt))
    except Exception as exc:
        log(f"[AsyncModel] ask_model_async_safe error: {exc}", level="error")
        # Hard fallback: synchronous path
        try:
            from sherly.services.model_manager import ask_model
            return ask_model(prompt)
        except Exception:
            return f"LLM unavailable: {exc}"
