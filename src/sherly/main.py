"""
Compatibility entry point for the legacy ``src/sherly`` layout.

The active branch uses top-level modules such as ``sherly_ui.app_manager``.
Keep this launcher so IDE run configs pointing at ``src/sherly/main.py`` still
start the app correctly.
"""

from __future__ import annotations

import os
import platform
import sys
from datetime import datetime, timezone
from pathlib import Path


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


def _add_repo_root_to_path() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    repo_root_str = str(repo_root)
    if repo_root_str not in sys.path:
        sys.path.insert(0, repo_root_str)


if __name__ == "__main__":
    _check_dependencies()
    _add_repo_root_to_path()

    print(f"[{datetime.now(timezone.utc).isoformat()}] Starting Sherly...")

    from sherly_ui.app_manager import start_app

    start_app()
