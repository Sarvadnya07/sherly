"""
CONFIG MANAGER — config_manager.py
Fixes:
  RC-1  Module-level cache: load_config() now reads disk only once per session.
         Cache is invalidated on save_config() so all getters stay consistent.
  OE-8  ghost_mode_port and llm_rate_limit_per_minute added to DEFAULT_CONFIG.
"""

from __future__ import annotations

import json
import os
import threading
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

CONFIG_FILE = Path(__file__).parent / "config.json"

DEFAULT_CONFIG: dict = {
    "current_model": "phi3",
    "auto_mode": False,
    "api_keys": {
        "openai": "YOUR_OPENAI_KEY",
        "gemini": "YOUR_GEMINI_KEY",
        "groq":   "YOUR_GROQ_KEY",
    },
    "plugins": {},
    "telemetry_enabled": False,
    "ghost_mode_port": 5555,
    "llm_rate_limit_per_minute": 20,
    "plugin_marketplace": False,
    "db_config": {
        "provider": "sqlite",   # "postgresql" for scaling
        "url": "sherly_history.db",
    },
    "chroma_config": {
        "mode": "local",        # "server" for scaling
        "host": "localhost",
        "port": 8000,
    },
}

# ---------------------------------------------------------------------------
# RC-1 — In-memory cache (thread-safe)
# ---------------------------------------------------------------------------
_cache_lock = threading.Lock()
_config_cache: dict | None = None


def _default_config() -> dict:
    import copy
    return copy.deepcopy(DEFAULT_CONFIG)


def load_config() -> dict:
    """
    Return the config dict.  Reads disk only on the first call or after
    save_config() invalidates the cache.
    """
    global _config_cache
    with _cache_lock:
        if _config_cache is not None:
            return _config_cache

        if not CONFIG_FILE.exists():
            save_config(DEFAULT_CONFIG)

        with CONFIG_FILE.open("r", encoding="utf-8") as f:
            raw = json.load(f)

        config = _default_config()
        config.update({k: v for k, v in raw.items() if k not in {"api_keys", "plugins"}})
        config["api_keys"] = {**DEFAULT_CONFIG["api_keys"], **raw.get("api_keys", {})}
        config["plugins"]  = {**DEFAULT_CONFIG["plugins"],  **raw.get("plugins",  {})}

        # Back-fill any keys that might be absent from older config files
        for key, default_val in DEFAULT_CONFIG.items():
            if key not in config:
                config[key] = default_val

        _config_cache = config
        return _config_cache


def save_config(config: dict) -> None:
    """Write config to disk and invalidate the in-memory cache."""
    global _config_cache
    with _cache_lock:
        with CONFIG_FILE.open("w", encoding="utf-8") as f:
            json.dump(config, f, indent=4)
        _config_cache = config   # update cache in place


# ---------------------------------------------------------------------------
# Getters / Setters
# ---------------------------------------------------------------------------

def get_current_model() -> str:
    return load_config().get("current_model", DEFAULT_CONFIG["current_model"])


def set_current_model(model: str) -> str:
    config = load_config()
    config["current_model"] = model
    save_config(config)
    return f"Model switched to {model}"


def get_api_key(model: str) -> str | None:
    env_key_name = f"{model.upper()}_API_KEY"
    env_key = os.environ.get(env_key_name)
    if env_key and env_key != f"YOUR_{model.upper()}_KEY":
        return env_key
    return load_config().get("api_keys", {}).get(model)


def set_api_key(model: str, key: str) -> None:
    config = load_config()
    config.setdefault("api_keys", {})[model] = key
    save_config(config)


def get_auto_mode() -> bool:
    return load_config().get("auto_mode", DEFAULT_CONFIG["auto_mode"])


def set_auto_mode(enabled: bool) -> None:
    config = load_config()
    config["auto_mode"] = bool(enabled)
    save_config(config)


def get_plugin_enabled(name: str, default: bool = True) -> bool:
    return load_config().get("plugins", {}).get(name, default)


def set_plugin_enabled(name: str, enabled: bool) -> None:
    config = load_config()
    config.setdefault("plugins", {})[name] = bool(enabled)
    save_config(config)


def get_ghost_mode_port() -> int:
    return int(load_config().get("ghost_mode_port", DEFAULT_CONFIG["ghost_mode_port"]))


def get_llm_rate_limit() -> int:
    return int(load_config().get("llm_rate_limit_per_minute", DEFAULT_CONFIG["llm_rate_limit_per_minute"]))


def get_plugin_marketplace_enabled() -> bool:
    return bool(load_config().get("plugin_marketplace", False))
