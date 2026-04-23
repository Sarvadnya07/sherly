import json
from pathlib import Path

CONFIG_FILE = Path(__file__).parent / "config.json"
DEFAULT_CONFIG = {
    "current_model": "phi3",
    "auto_mode": False,
    "api_keys": {
        "openai": "YOUR_OPENAI_KEY",
        "gemini": "YOUR_GEMINI_KEY",
        "groq": "YOUR_GROQ_KEY",
    },
    "plugins": {},
    "telemetry_enabled": False,
    "db_config": {
        "provider": "sqlite", # Or "postgresql" for scaling
        "url": "sherly_history.db"
    },
    "chroma_config": {
        "mode": "local", # Or "server" for scaling
        "host": "localhost",
        "port": 8000
    }
}


def _default_config():
    return {
        "current_model": DEFAULT_CONFIG["current_model"],
        "auto_mode": DEFAULT_CONFIG["auto_mode"],
        "api_keys": DEFAULT_CONFIG["api_keys"].copy(),
        "plugins": DEFAULT_CONFIG["plugins"].copy(),
    }


def load_config():
    if not CONFIG_FILE.exists():
        save_config(DEFAULT_CONFIG)

    with CONFIG_FILE.open("r", encoding="utf-8") as f:
        raw = json.load(f)

    config = _default_config()
    config.update({k: v for k, v in raw.items() if k not in {"api_keys", "plugins"}})
    config["api_keys"] = {**DEFAULT_CONFIG["api_keys"], **raw.get("api_keys", {})}
    config["plugins"] = {**DEFAULT_CONFIG["plugins"], **raw.get("plugins", {})}

    if "auto_mode" not in config:
        config["auto_mode"] = DEFAULT_CONFIG["auto_mode"]

    return config


def save_config(config):
    with CONFIG_FILE.open("w", encoding="utf-8") as f:
        json.dump(config, f, indent=4)


def get_current_model():
    return load_config().get("current_model", DEFAULT_CONFIG["current_model"])


def set_current_model(model):
    config = load_config()
    config["current_model"] = model
    save_config(config)
    return f"Model switched to {model}"


import os
from dotenv import load_dotenv

load_dotenv()

def get_api_key(model):
    env_key_name = f"{model.upper()}_API_KEY"
    env_key = os.environ.get(env_key_name)
    if env_key and env_key != f"YOUR_{model.upper()}_KEY":
        return env_key
    return load_config().get("api_keys", {}).get(model)


def set_api_key(model, key):
    config = load_config()
    config.setdefault("api_keys", {})[model] = key
    save_config(config)


def get_auto_mode():
    return load_config().get("auto_mode", DEFAULT_CONFIG["auto_mode"])


def set_auto_mode(enabled):
    config = load_config()
    config["auto_mode"] = bool(enabled)
    save_config(config)


def get_plugin_enabled(name, default=True):
    return load_config().get("plugins", {}).get(name, default)


def set_plugin_enabled(name, enabled):
    config = load_config()
    config.setdefault("plugins", {})[name] = bool(enabled)
    save_config(config)
