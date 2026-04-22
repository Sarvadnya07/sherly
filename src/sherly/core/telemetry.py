import json
import os
from datetime import datetime, timezone
from sherly.config.config_manager import load_config

TELEMETRY_FILE = "telemetry.jsonl"

def log_telemetry(event_type: str, data: dict):
    if not load_config().get("telemetry_enabled", False):
        return

    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "event_type": event_type,
        "data": data
    }
    
    try:
        with open(TELEMETRY_FILE, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry) + "\n")
    except Exception:
        pass

def log_self_heal(command: str, success: bool, error: str = None):
    log_telemetry("self_heal", {
        "command": command,
        "success": success,
        "error": error
    })
