"""
MAIN ENTRY POINT — main.py

Startup flow:
    1. Dependency check
    2. Ollama health check
    3. Scan local models
    4. Resolve model (respects auto/manual mode)
    5. Initialize UI
"""

from __future__ import annotations

import logging
import os
import platform
import sys
from datetime import datetime, timezone
from pathlib import Path

for _stream in (sys.stdout, sys.stderr):
    if hasattr(_stream, "reconfigure"):
        _stream.reconfigure(errors="replace")

# Ensure project root is on sys.path so bare module imports resolve correctly.
_PROJECT_ROOT = str(Path(__file__).resolve().parent)
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)


# ---------------------------------------------------------------------------
# OS-specific env setup before any Qt import
# ---------------------------------------------------------------------------
_os = platform.system()
if _os == "Windows":
    os.environ["QT_ENABLE_HIGHDPI_SCALING"] = "0"
    os.environ["QT_LOGGING_RULES"] = "qt.qpa.window=false"


# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(message)s",
)
logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Early dependency guard
# ---------------------------------------------------------------------------
def _check_dependencies() -> None:
    missing = []
    required = [
        ("PySide6",        "PySide6"),
        ("faster_whisper", "faster-whisper"),
        ("sounddevice",    "sounddevice"),
        ("pyttsx3",        "pyttsx3"),
        ("requests",       "requests"),
        ("httpx",          "httpx"),
    ]
    for module, pip_name in required:
        try:
            __import__(module)
        except ImportError:
            missing.append(pip_name)

    if missing:
        print("❌ Missing required packages. Run:")
        print(f"   pip install {' '.join(missing)}")
        sys.exit(1)


if __name__ == "__main__":
    _check_dependencies()

    # UTC timestamp on startup log
    print(f"\n[{datetime.now(timezone.utc).isoformat()}] Sherly starting...\n")

    # ── Ollama health check ──────────────────────────────────────────
    from model_scanner import is_ollama_running

    if is_ollama_running():
        logger.info("[Ollama] Connected")
    else:
        logger.warning("[Ollama] Not running — local models unavailable")

    # ── Model resolution ─────────────────────────────────────────────
    import config_manager
    import model_scanner
    from sherly_core.model_resolver import resolve_model

    model = resolve_model(config_manager, model_scanner)

    if model:
        print(f"\n  ✅ Sherly using model → {model}\n")
    else:
        print("\n  ⚠️  No local Ollama model available.\n")

    # ── Launch UI ────────────────────────────────────────────────────
    from sherly_ui.app_manager import start_app
    start_app()
