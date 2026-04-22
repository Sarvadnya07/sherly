import json
from sherly.utils.runtime_utils import safe_execute
from sherly.core.diagnostics import run_diagnostics
from sherly.config.config_manager import set_current_model
from sherly.services.memory_brain import remember

def handle_system_command(low: str, raw: str) -> str | None:
    # --- System diagnostics ---
    if "run diagnostics" in low or "system health" in low:
        results = safe_execute(lambda: run_diagnostics(), "Failed to run diagnostics.")
        return f"Diagnostics:\n{json.dumps(results, indent=2)}"

    # --- Model switching ---
    for keyword, model_name in [
        ("use openai", "openai"), ("switch to openai", "openai"),
        ("use gemini", "gemini"), ("switch to gemini", "gemini"),
        ("use groq", "groq"), ("switch to groq", "groq"),
        ("use local", "local"), ("switch to local", "local"),
    ]:
        if keyword in low:
            return set_current_model(model_name)

    return None
