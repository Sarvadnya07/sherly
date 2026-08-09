"""
CONFIG MANAGER — config_manager.py

Thread-safe, atomic configuration management for Sherly.

Model selection uses a three-state system in the ``model_selection`` block:
    - mode: "auto" | "manual"
    - current_model: the model Sherly is actively using (set by resolver or user)
    - pinned_model: user-pinned model (locks mode to "manual")

This ensures auto-detection never overrides a user's deliberate model choice.
"""

from __future__ import annotations

import json
import os
import tempfile
import threading
from pathlib import Path

CONFIG_FILE = Path("config.json")

DEFAULT_CONFIG: dict = {
    "auto_mode": False,
    "model_selection": {
        "mode": "auto",
        "current_model": None,
        "pinned_model": None,
    },
    "api_keys": {
        "openai": "YOUR_OPENAI_KEY",
        "gemini": "YOUR_GEMINI_KEY",
        "groq":   "YOUR_GROQ_KEY",
    },
    "plugins": {},
}

_config_lock = threading.Lock()


# ---------------------------------------------------------------------------
# Internal helpers  (must be called while _config_lock is held)
# ---------------------------------------------------------------------------

def _default_config() -> dict:
    return {
        "auto_mode":       DEFAULT_CONFIG["auto_mode"],
        "model_selection": DEFAULT_CONFIG["model_selection"].copy(),
        "api_keys":        DEFAULT_CONFIG["api_keys"].copy(),
        "plugins":         DEFAULT_CONFIG["plugins"].copy(),
    }


def _load_unlocked() -> dict:
    """Read + merge config from disk.  Caller must hold _config_lock."""
    if not CONFIG_FILE.exists():
        cfg = _default_config()
        _write_unlocked(cfg)
        return cfg
    try:
        with CONFIG_FILE.open("r", encoding="utf-8") as f:
            raw = json.load(f)
    except (json.JSONDecodeError, OSError):
        return _default_config()

    config = _default_config()

    # Keys handled separately (nested dicts or legacy fields to migrate)
    _SPECIAL = {"api_keys", "plugins", "model_selection",
                "current_model", "auto_detect_model"}
    config.update({k: v for k, v in raw.items() if k not in _SPECIAL})

    config["api_keys"] = {**DEFAULT_CONFIG["api_keys"], **raw.get("api_keys", {})}
    config["plugins"]  = {**DEFAULT_CONFIG["plugins"],  **raw.get("plugins",  {})}
    config["model_selection"] = {
        **DEFAULT_CONFIG["model_selection"],
        **raw.get("model_selection", {}),
    }

    # ── Migration: old-style top-level current_model ──────────────────
    if "current_model" in raw and "model_selection" not in raw:
        old_model = raw["current_model"]
        if old_model:
            config["model_selection"]["current_model"] = old_model

    config.setdefault("auto_mode", DEFAULT_CONFIG["auto_mode"])
    return config


def _write_unlocked(config: dict) -> None:
    """Atomic write via tempfile + replace.  Caller must hold _config_lock."""
    dir_ = CONFIG_FILE.parent
    tmp: str | None = None
    try:
        fd, tmp = tempfile.mkstemp(dir=dir_, suffix=".json.tmp", text=True)
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=4)
        os.replace(tmp, CONFIG_FILE)
    except Exception as exc:
        print(f"[Config] save error: {exc}")
        try:
            if tmp and os.path.exists(tmp):
                os.unlink(tmp)
        except Exception:
            pass


# ---------------------------------------------------------------------------
# Public API — general
# ---------------------------------------------------------------------------

def load_config() -> dict:
    with _config_lock:
        return _load_unlocked()


def save_config(config: dict) -> None:
    with _config_lock:
        _write_unlocked(config)


# ---------------------------------------------------------------------------
# Public API — model selection
# ---------------------------------------------------------------------------

def get_model_mode() -> str:
    """Return 'auto' or 'manual'."""
    with _config_lock:
        cfg = _load_unlocked()
        return cfg.get("model_selection", {}).get("mode", "auto")


def set_model_mode(mode: str) -> None:
    if mode not in {"auto", "manual"}:
        raise ValueError(f"Invalid model mode: {mode!r}. Must be 'auto' or 'manual'.")
    with _config_lock:
        cfg = _load_unlocked()
        cfg.setdefault("model_selection", {})["mode"] = mode
        _write_unlocked(cfg)


def get_current_model() -> str | None:
    """Return the model Sherly is currently using, or None."""
    with _config_lock:
        cfg = _load_unlocked()
        return cfg.get("model_selection", {}).get("current_model")


def set_current_model(model: str) -> str:
    """
    Set the active model.

    When called from the UI or voice command (user deliberate selection),
    this also pins the model and switches to manual mode so auto-detection
    won't override the user's choice.
    """
    with _config_lock:
        cfg = _load_unlocked()
        ms = cfg.setdefault("model_selection", {})
        ms["current_model"] = model
        ms["pinned_model"] = model
        ms["mode"] = "manual"
        _write_unlocked(cfg)
    return f"Model switched to {model}"


def set_resolved_model(model: str) -> None:
    """
    Called by the model resolver during auto-detection.
    Updates current_model WITHOUT changing mode or pinned_model.
    """
    with _config_lock:
        cfg = _load_unlocked()
        ms = cfg.setdefault("model_selection", {})
        ms["current_model"] = model
        _write_unlocked(cfg)


def get_pinned_model() -> str | None:
    """Return the user-pinned model, or None."""
    with _config_lock:
        cfg = _load_unlocked()
        return cfg.get("model_selection", {}).get("pinned_model")


def pin_model(model: str) -> None:
    """Pin a specific model, switching mode to manual."""
    with _config_lock:
        cfg = _load_unlocked()
        ms = cfg.setdefault("model_selection", {})
        ms["mode"] = "manual"
        ms["pinned_model"] = model
        ms["current_model"] = model
        _write_unlocked(cfg)


def enable_auto_detection() -> None:
    """Enable auto-detection mode, clearing any pinned model."""
    with _config_lock:
        cfg = _load_unlocked()
        ms = cfg.setdefault("model_selection", {})
        ms["mode"] = "auto"
        ms["pinned_model"] = None
        _write_unlocked(cfg)


# ---------------------------------------------------------------------------
# Public API — API keys
# ---------------------------------------------------------------------------

def get_api_key(model: str) -> str | None:
    with _config_lock:
        return _load_unlocked().get("api_keys", {}).get(model)


def set_api_key(model: str, key: str) -> None:
    with _config_lock:
        cfg = _load_unlocked()
        cfg.setdefault("api_keys", {})[model] = key
        _write_unlocked(cfg)


# ---------------------------------------------------------------------------
# Public API — auto mode (intent classification, NOT model detection)
# ---------------------------------------------------------------------------

def get_auto_mode() -> bool:
    with _config_lock:
        return _load_unlocked().get("auto_mode", DEFAULT_CONFIG["auto_mode"])


def set_auto_mode(enabled: bool) -> None:
    with _config_lock:
        cfg = _load_unlocked()
        cfg["auto_mode"] = bool(enabled)
        _write_unlocked(cfg)


# ---------------------------------------------------------------------------
# Public API — plugins
# ---------------------------------------------------------------------------

def get_plugin_enabled(name: str, default: bool = True) -> bool:
    with _config_lock:
        return _load_unlocked().get("plugins", {}).get(name, default)


def set_plugin_enabled(name: str, enabled: bool) -> None:
    with _config_lock:
        cfg = _load_unlocked()
        cfg.setdefault("plugins", {})[name] = bool(enabled)
        _write_unlocked(cfg)
