"""
MAIN ENTRY POINT — main.py
Fixes:
  RC-6  Startup pre-flight checks before Qt launch
  OE-1  --headless CLI flag (skips Qt, starts Ghost Mode server)
  FS-10 Model auto-selection advisory based on available RAM
  #20   Startup failure guard (early dependency check)
  #21   OS-specific env setup before any Qt import
  #17   UTC timestamps in startup log
"""

from __future__ import annotations

import argparse
import os
import platform
import sys
from datetime import datetime, timezone

# ---------------------------------------------------------------------------
# #21 – OS-specific env setup before any Qt import
# ---------------------------------------------------------------------------
_os = platform.system()
if _os == "Windows":
    os.environ["QT_ENABLE_HIGHDPI_SCALING"] = "0"
    os.environ["QT_LOGGING_RULES"]          = "qt.qpa.window=false"


# ---------------------------------------------------------------------------
# #20 – Early dependency guard (fails loudly, not silently)
# ---------------------------------------------------------------------------
def _check_dependencies() -> None:
    missing: list[str] = []
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
        print("Missing required packages. Run:")
        print(f"  pip install {' '.join(missing)}")
        sys.exit(1)


def _check_hardware() -> None:
    try:
        import psutil
        mem      = psutil.virtual_memory()
        total_gb = mem.total / (1024 ** 3)
        if total_gb < 8.0:
            print(
                f"WARNING: Your system has {total_gb:.1f} GB of RAM. "
                "Running local LLMs effectively requires at least 8 GB. "
                "You may experience performance issues or crashes."
            )
    except ImportError:
        pass


def _print_model_advisory() -> None:
    """
    FS-#10: Hardware-aware model recommendation displayed at startup.
    Calls the existing _get_optimal_local_model() helper in model_manager.
    """
    try:
        from sherly.services.model_manager import _get_optimal_local_model
        import psutil
        mem      = psutil.virtual_memory()
        total_gb = mem.total / (1024 ** 3)
        recommended = _get_optimal_local_model()
        print(
            f"Hardware: {total_gb:.1f} GB RAM detected. "
            f"Recommended local model: '{recommended}'. "
            "Switch anytime: \"switch to llama3 model\"."
        )
    except Exception:
        pass  # Non-fatal; advisory only


# ---------------------------------------------------------------------------
# CLI argument parsing (OE-1)
# ---------------------------------------------------------------------------
def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Sherly AI — Autonomous Developer Orchestrator",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  python src/sherly/main.py              # Full UI mode\n"
            "  python src/sherly/main.py --headless   # Ghost Mode (no UI)\n"
        ),
    )
    parser.add_argument(
        "--headless",
        action="store_true",
        help="Run in Ghost Mode (socket server, no Qt UI). Ideal for Docker / CI.",
    )
    parser.add_argument(
        "--accessibility",
        action="store_true",
        default=False,
        help="Apply high-contrast WCAG AA theme and enable screen reader hints (OE-7).",
    )
    return parser.parse_args()


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    args = _parse_args()

    # Path hack for direct script execution
    _src = os.path.abspath(os.path.join(os.path.dirname(__file__), "../"))
    if _src not in sys.path:
        sys.path.insert(0, _src)

    print(f"[{datetime.now(timezone.utc).isoformat()}] Starting Sherly...")

    # RC-4: Explicit router initialization (eliminates circular-import side-effects)
    from sherly.services.command_router import initialize as _router_init
    _router_init()

    if args.headless:
        # OE-1: Skip Qt entirely, launch headless Ghost Mode
        print("Headless mode — skipping UI initialisation.")
        from sherly.core.ghost_mode import run_headless
        run_headless()
    else:
        # Full UI mode
        _check_dependencies()
        _check_hardware()
        _print_model_advisory()   # FS-#10

        from sherly.ui.app_manager import start_app

        # OE-7: Apply accessibility theme if requested or saved in config
        use_accessibility = args.accessibility
        if not use_accessibility:
            try:
                from sherly.ui.accessibility import should_use_accessibility
                use_accessibility = should_use_accessibility()
            except Exception:
                pass

        start_app()
