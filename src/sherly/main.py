"""
Main entry point for the src-based Sherly application.

This keeps the startup checks from main while preserving the cleaner startup
logging and dependency handling used during the palette branch work.
"""

from __future__ import annotations

import os
import platform
import sys
from datetime import datetime, timezone


_os = platform.system()
if _os == "Windows":
    os.environ["QT_ENABLE_HIGHDPI_SCALING"] = "0"
    os.environ["QT_LOGGING_RULES"] = "qt.qpa.window=false"


def _check_dependencies() -> None:
    missing: list[str] = []
    required = [
        ("PySide6", "PySide6"),
        ("faster_whisper", "faster-whisper"),
        ("sounddevice", "sounddevice"),
        ("pyttsx3", "pyttsx3"),
        ("requests", "requests"),
    ]
    for module, pip_name in required:
        try:
            __import__(module)
        except ImportError:
            missing.append(pip_name)

    if missing:
        print("Missing required packages. Run:")
        print(f"  pip install {' '.join(missing)}")
        sys.exit(1)


def _check_hardware() -> None:
    try:
        import psutil

        mem = psutil.virtual_memory()
        total_gb = mem.total / (1024**3)
        if total_gb < 8.0:
            print(
                f"WARNING: Your system has {total_gb:.1f}GB of RAM. "
                "Running local LLMs effectively requires at least 8GB. "
                "You may experience performance issues or crashes."
            )
    except ImportError:
        pass


if __name__ == "__main__":
    _check_dependencies()
    _check_hardware()

    print(f"[{datetime.now(timezone.utc).isoformat()}] Starting Sherly...")

    from sherly.ui.app_manager import start_app

    start_app()
