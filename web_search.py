"""
WEB SEARCH — web_search.py
Robust DuckDuckGo search integration with clean fallback.
"""

from __future__ import annotations

import warnings
from runtime_utils import log

_SEARCH_TIMEOUT = 5   # seconds before timeout


def search_web(query: str, max_results: int = 5) -> list[dict]:
    """
    Search DuckDuckGo with a hard timeout.
    Returns [] on network failure instead of hanging.
    """
    if not query or not query.strip():
        return []

    cleaned_query = query.strip()
    # Strip common leading command prefixes if present
    for prefix in ("search for", "search", "google", "look up", "find"):
        if cleaned_query.lower().startswith(prefix + " "):
            cleaned_query = cleaned_query[len(prefix) + 1:].strip()

    try:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            try:
                from ddgs import DDGS
            except ImportError:
                from duckduckgo_search import DDGS

            with DDGS(timeout=_SEARCH_TIMEOUT) as ddgs:
                results = list(ddgs.text(cleaned_query, max_results=max_results))
            return results
    except Exception as exc:
        log(f"[WebSearch] failed: {exc}", level="warning")
        return []