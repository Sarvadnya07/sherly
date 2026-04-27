"""
ACCESSIBILITY THEME — accessibility.py
Implements:
  OE-7  High-contrast QSS theme + screen reader hints.
         Applied via --accessibility CLI flag or config.json → theme: "accessibility".

  Spec:
    - White background (#FFFFFF), black text (#000000) — ≥4.5:1 contrast ratio (WCAG AA)
    - Blue accent (#0057B8) for interactive elements
    - Large font baseline (14pt minimum)
    - All interactive elements get setAccessibleName() hints for screen readers
    - Preference persisted in config.json under "theme"
"""

from __future__ import annotations

from sherly.utils.runtime_utils import log


# ---------------------------------------------------------------------------
# QSS Stylesheet
# ---------------------------------------------------------------------------

ACCESSIBILITY_QSS = """
/* OE-7: High-Contrast Accessibility Theme — WCAG AA compliant */

QWidget {
    background-color: #FFFFFF;
    color: #000000;
    font-family: "Segoe UI", Arial, sans-serif;
    font-size: 14pt;
}

QTextEdit, QPlainTextEdit, QLineEdit {
    background-color: #FFFFFF;
    color: #000000;
    border: 2px solid #000000;
    border-radius: 4px;
    padding: 6px;
    font-size: 14pt;
    selection-background-color: #0057B8;
    selection-color: #FFFFFF;
}

QPushButton {
    background-color: #0057B8;
    color: #FFFFFF;
    border: 2px solid #003F88;
    border-radius: 4px;
    padding: 8px 16px;
    font-size: 14pt;
    font-weight: bold;
}

QPushButton:hover {
    background-color: #003F88;
}

QPushButton:pressed {
    background-color: #002060;
}

QPushButton:focus {
    outline: 3px solid #FFD600;
    outline-offset: 2px;
}

QLabel {
    color: #000000;
    font-size: 14pt;
}

QScrollBar:vertical {
    background: #E0E0E0;
    width: 18px;
}

QScrollBar::handle:vertical {
    background: #555555;
    min-height: 30px;
    border-radius: 4px;
}

QDockWidget {
    background-color: #F5F5F5;
    color: #000000;
    border: 2px solid #000000;
    font-size: 14pt;
    font-weight: bold;
}

QMenuBar, QMenu {
    background-color: #FFFFFF;
    color: #000000;
    border: 1px solid #000000;
    font-size: 14pt;
}

QMenu::item:selected {
    background-color: #0057B8;
    color: #FFFFFF;
}

QListWidget {
    background-color: #FFFFFF;
    color: #000000;
    border: 2px solid #000000;
    font-size: 13pt;
}

QListWidget::item:selected {
    background-color: #0057B8;
    color: #FFFFFF;
}

QStatusBar {
    background-color: #000000;
    color: #FFFFFF;
    font-size: 12pt;
}
"""


# ---------------------------------------------------------------------------
# Dark theme (default)
# ---------------------------------------------------------------------------

DEFAULT_QSS = ""  # Use the existing glassmorphism stylesheet from the UI


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def apply_accessibility_theme(app) -> None:
    """
    OE-7: Apply the high-contrast QSS stylesheet to a QApplication.
    Also sets Qt accessibility attributes for screen readers.

    Call before showing any window.
    """
    try:
        from PySide6.QtGui import QAccessible
        app.setStyleSheet(ACCESSIBILITY_QSS)
        QAccessible.setActive(True)
        log("[Accessibility] High-contrast theme applied ✓")
        _persist_theme("accessibility")
    except ImportError:
        log("[Accessibility] PySide6 not available — skipping Qt theme.", level="warning")
    except Exception as exc:
        log(f"[Accessibility] Theme application failed: {exc}", level="error")


def apply_default_theme(app) -> None:
    """Reset to the default dark/glassmorphism theme."""
    try:
        app.setStyleSheet(DEFAULT_QSS)
        log("[Accessibility] Default theme applied.")
        _persist_theme("default")
    except Exception as exc:
        log(f"[Accessibility] Theme reset failed: {exc}", level="error")


def get_current_theme() -> str:
    """Return the saved theme preference ('accessibility' or 'default')."""
    try:
        from sherly.config.config_manager import load_config
        return load_config().get("theme", "default")
    except Exception:
        return "default"


def should_use_accessibility() -> bool:
    """Return True if the accessibility theme should be applied at startup."""
    return get_current_theme() == "accessibility"


def _persist_theme(theme_name: str) -> None:
    """Save theme preference to config.json."""
    try:
        from sherly.config.config_manager import load_config, save_config
        cfg          = load_config()
        cfg["theme"] = theme_name
        save_config(cfg)
    except Exception:
        pass  # Non-fatal — preference just won't persist


def add_accessible_names(widget_map: dict[str, object]) -> None:
    """
    OE-7: Set Qt accessibility names on all widgets in *widget_map*.
    widget_map: {"Human-readable label": widget_instance, ...}
    """
    try:
        for name, widget in widget_map.items():
            if hasattr(widget, "setAccessibleName"):
                widget.setAccessibleName(name)
            if hasattr(widget, "setAccessibleDescription"):
                widget.setAccessibleDescription(name)
    except Exception as exc:
        log(f"[Accessibility] setAccessibleName failed: {exc}", level="warning")
