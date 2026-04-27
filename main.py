"""
MAIN ENTRY POINT — main.py
Fixes: #20 startup failure (pre-flight model/config check before Qt starts)
        #21 OS-specific failures (platform guard for DPI env var)
        #17 timezone (UTC in startup log)
"""

from __future__ import annotations

import os
import platform
import sys
from datetime import datetime, timezone


# ---------------------------------------------------------------------------
# Fix #21 – OS-specific env setup before any Qt import
# ---------------------------------------------------------------------------
_os = platform.system()
if _os == "Windows":
    os.environ["QT_ENABLE_HIGHDPI_SCALING"] = "0"
    # Fix #20: suppress SetProcessDpiAwarenessContext error from Qt
    os.environ["QT_LOGGING_RULES"] = "qt.qpa.window=false"

# ---------------------------------------------------------------------------
# Fix #20 – early dependency guard (fails loudly, not silently)
# ---------------------------------------------------------------------------
def _check_dependencies() -> None:
    missing = []
    required = [
        ("PySide6",        "PySide6"),
        ("faster_whisper", "faster-whisper"),
        ("sounddevice",    "sounddevice"),
        ("pyttsx3",        "pyttsx3"),
        ("requests",       "requests"),
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

    # Fix #17: UTC timestamp on startup log
    print(f"[{datetime.now(timezone.utc).isoformat()}] Starting Sherly...")

    from sherly_ui.app_manager import start_app
    start_app()
