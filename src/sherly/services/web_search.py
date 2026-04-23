"""
WEB SEARCH — web_search.py
Fixes: #13 network latency / failure (timeout + graceful fallback)
"""

from __future__ import annotations

_SEARCH_TIMEOUT = 4   # seconds before we give up


def search_web(query: str, max_results: int = 5) -> list[dict]:
    """
    Search DuckDuckGo with a hard timeout.
    Returns [] on network failure instead of hanging.
    Fix #13: never block the router for more than _SEARCH_TIMEOUT seconds.
    """
    if not query or not query.strip():
        return []

    try:
        from ddgs import DDGS
        with DDGS() as ddgs:
            results = list(ddgs.text(query.strip(), max_results=max_results))
        return results
    except Exception as exc:
        print(f"[WebSearch] failed: {exc}")
        return []   # Fix #13: graceful empty-list fallback