"""
MODEL SCANNER — model_scanner.py

Queries the local Ollama server for installed models, normalizes metadata,
and ranks them by suitability for Sherly's tasks.

Key design decisions:
  - AUTO-DETECT = YES, AUTO-DOWNLOAD = NO (never pulls models automatically)
  - Numeric scoring for deterministic ranking
  - Family normalization handles Ollama naming conventions
    (e.g. "qwen2.5-coder:3b" → family="qwen2.5-coder", tag="3b")
"""

from __future__ import annotations

import logging
from typing import Any

import httpx

logger = logging.getLogger(__name__)

OLLAMA_URL = "http://127.0.0.1:11434"

# ── Scoring tables ──────────────────────────────────────────────────────
# Higher score = higher priority.
# Coding models rank highest since Sherly is a developer assistant.

CODING_MODELS: dict[str, int] = {
    "qwen2.5-coder":     100,
    "qwen3-coder":       100,
    "deepseek-coder-v2":  95,
    "deepseek-coder":     95,
    "codellama":          90,
    "starcoder2":         88,
    "starcoder":          85,
    "codegemma":          85,
}

GENERAL_MODELS: dict[str, int] = {
    "llama3.2":    85,
    "llama3.1":    85,
    "llama3":      80,
    "qwen2.5":     85,
    "qwen2":       80,
    "mistral":     75,
    "mixtral":     78,
    "gemma2":      75,
    "gemma":       70,
    "phi3":        70,
    "phi":         65,
    "command-r":   72,
    "neural-chat": 60,
    "zephyr":      60,
    "orca":        55,
    "vicuna":      55,
}


# ── Model normalization ─────────────────────────────────────────────────

def normalize_model(raw: dict[str, Any]) -> dict[str, Any]:
    """
    Normalize an Ollama model dict into a structured metadata record.

    Input  (from /api/tags):
        {"name": "qwen2.5-coder:3b", "size": 1900000000, ...}

    Output:
        {
            "name":   "qwen2.5-coder:3b",
            "family": "qwen2.5-coder",
            "tag":    "3b",
            "size":   1900000000,
            "coding": True,
            "local":  True,
        }
    """
    name = raw.get("name", "")

    if ":" in name:
        family, tag = name.rsplit(":", 1)
    else:
        family = name
        tag = "latest"

    family_lower = family.lower()
    is_coding = any(family_lower.startswith(k) for k in CODING_MODELS)

    return {
        "name":   name,
        "family": family_lower,
        "tag":    tag,
        "size":   raw.get("size", 0),
        "coding": is_coding,
        "local":  True,
        "_raw":   raw,
    }


# ── Scoring ──────────────────────────────────────────────────────────────

def _score_model(model: dict[str, Any]) -> int:
    """
    Score a normalized model.  Higher = better fit for Sherly.
    """
    family = model.get("family", "")

    # Check coding models first (longest prefix match wins)
    for prefix, score in CODING_MODELS.items():
        if family == prefix or family.startswith(prefix):
            return score

    # Then general models
    for prefix, score in GENERAL_MODELS.items():
        if family == prefix or family.startswith(prefix):
            return score

    # Unknown model — give a small score (better than nothing)
    size = model.get("size", 0)
    return 10 if size else 1


# ── Scanner ──────────────────────────────────────────────────────────────

def is_ollama_running() -> bool:
    """Return True if the local Ollama server is reachable."""
    try:
        r = httpx.get(f"{OLLAMA_URL}/api/tags", timeout=3.0)
        return r.status_code == 200
    except Exception:
        return False


def scan_ollama_models() -> list[dict[str, Any]]:
    """
    Query Ollama /api/tags and return normalized model metadata.

    Returns a list of dicts with keys:
        name, family, tag, size, coding, local

    Returns an empty list if Ollama is unreachable.
    """
    try:
        response = httpx.get(
            f"{OLLAMA_URL}/api/tags",
            timeout=3.0,
        )
        response.raise_for_status()

        data = response.json()
        raw_models = data.get("models", [])
        models = [normalize_model(m) for m in raw_models]

        logger.info("Ollama scan completed: %d model(s)", len(models))
        return models

    except Exception as exc:
        logger.warning("Ollama unavailable: %s", exc)
        return []


def pick_best_model(
    models: list[dict[str, Any]],
) -> dict[str, Any] | None:
    """
    Given a list of normalized model dicts, return the best one.
    Returns None if the list is empty.
    """
    if not models:
        return None

    ranked = sorted(models, key=_score_model, reverse=True)
    return ranked[0]