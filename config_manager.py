"""
CONFIG MANAGER — config_manager.py

Thread-safe, atomic configuration management for Sherly with schema versioning,
incremental migrations, pre-migration backup, and rollback safety.

Model selection uses a three-state system in the ``model_selection`` block:
    - mode: "auto" | "manual"
    - current_model: the model Sherly is actively using (set by resolver or user)
    - pinned_model: user-pinned model (locks mode to "manual")
"""

from __future__ import annotations

import json
import os
import shutil
import tempfile
import threading
from pathlib import Path

CONFIG_FILE = Path("config.json")
CONFIG_BACKUP = Path("config.json.bak")

CURRENT_CONFIG_SCHEMA_VERSION = 2

DEFAULT_CONFIG: dict = {
    "schema_version": CURRENT_CONFIG_SCHEMA_VERSION,
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
# Migration Engine
# ---------------------------------------------------------------------------

def _migrate_config(raw: dict) -> dict:
    """
    Migrates raw configuration to CURRENT_CONFIG_SCHEMA_VERSION incrementally,
    preserving unknown/custom fields and returning a fully compliant config dictionary.
    """
    cfg = raw.copy()
    version = cfg.get("schema_version", 1)

    # v1 -> v2 migration
    if version < 2:
        # Migrate old top-level current_model into model_selection
        if "current_model" in cfg and "model_selection" not in cfg:
            old_model = cfg.pop("current_model", None)
            cfg["model_selection"] = {
                "mode": "auto",
                "current_model": old_model,
                "pinned_model": None,
            }
        cfg["schema_version"] = 2

    return cfg


def _default_config() -> dict:
    return {
        "schema_version":  CURRENT_CONFIG_SCHEMA_VERSION,
        "auto_mode":       DEFAULT_CONFIG["auto_mode"],
        "model_selection": DEFAULT_CONFIG["model_selection"].copy(),
        "api_keys":        DEFAULT_CONFIG["api_keys"].copy(),
        "plugins":         DEFAULT_CONFIG["plugins"].copy(),
    }


def _load_unlocked() -> dict:
    """Read + merge config from disk. Caller must hold _config_lock."""
    if not CONFIG_FILE.exists():
        cfg = _default_config()
        _write_unlocked(cfg)
        return cfg
    try:
        with CONFIG_FILE.open("r", encoding="utf-8") as f:
            raw = json.load(f)
    except (json.JSONDecodeError, OSError):
        return _default_config()

    # Create pre-migration backup if migration is needed
    current_ver = raw.get("schema_version", 1)
    if current_ver < CURRENT_CONFIG_SCHEMA_VERSION:
        try:
            shutil.copy2(CONFIG_FILE, CONFIG_BACKUP)
        except Exception:
            pass

    migrated = _migrate_config(raw)
    config = _default_config()

    # Preserve all user/custom keys
    _SPECIAL = {"api_keys", "plugins", "model_selection", "schema_version"}
    config.update({k: v for k, v in migrated.items() if k not in _SPECIAL})

    config["schema_version"] = CURRENT_CONFIG_SCHEMA_VERSION
    config["api_keys"] = {**DEFAULT_CONFIG["api_keys"], **migrated.get("api_keys", {})}
    config["plugins"]  = {**DEFAULT_CONFIG["plugins"],  **migrated.get("plugins",  {})}
    config["model_selection"] = {
        **DEFAULT_CONFIG["model_selection"],
        **migrated.get("model_selection", {}),
    }

    # Persist migrated config if version was updated
    if current_ver < CURRENT_CONFIG_SCHEMA_VERSION:
        _write_unlocked(config)

    return config


def _write_unlocked(config: dict) -> None:
    """Atomic write via tempfile + replace. Caller must hold _config_lock."""
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
    env_var = f"{model.upper()}_API_KEY"
    env_val = os.getenv(env_var)
    if env_val and env_val.strip() and not env_val.startswith("YOUR_"):
        return env_val.strip()
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
