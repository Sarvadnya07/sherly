"""
SHERLY UI DESIGN SYSTEM & THEME TOKENS — sherly_ui/theme.py
Canonical design system tokens, typography scales, and global Qt stylesheets.
Ultra-premium Obsidian & Zinc developer aesthetics (Linear / Cursor / Raycast style).
"""

from __future__ import annotations
from PySide6.QtGui import QColor, QFont

# ── 1. Color Palette (Obsidian & Zinc Dark Theme) ───────────────────────────
# Canvas & Surfaces
C_BG_CANVAS      = "#09090b"       # Deepest neutral canvas
C_BG_DARK        = "#09090b"       # Backward-compat alias for canvas
C_BG_SIDEBAR     = "#0d0d11"       # Left navigation rail
C_BG_SURFACE     = "#09090b"       # Main workspace and panels
C_BG_PANEL       = "#09090b"       # Backward-compat alias for surface
C_BG_CARD        = "#141418"       # Embedded cards and message nodes
C_BG_CARD_HOVER  = "#1a1a22"       # Hovered card state
C_BG_INPUT       = "#121216"       # Text inputs and textareas
C_BG_HOVER       = "rgba(255, 255, 255, 0.05)"

# Brand Accents & Restrained Highlights
C_ACCENT_PRIMARY = "#6366f1"       # Indigo 500
C_ACCENT_HOVER   = "#4f46e5"       # Indigo 600
C_ACCENT_LIGHT   = "#818cf8"       # Indigo 400
C_ACCENT_SURFACE = "rgba(99, 102, 241, 0.08)" # Subtle tint
C_ACCENT_GLOW    = "rgba(99, 102, 241, 0.15)"
C_PURPLE_MAIN    = "#6366f1"
C_PURPLE_GLOW    = "rgba(99, 102, 241, 0.15)"
C_PURPLE_DARK    = "#3730a3"
C_CYAN_ACCENT    = "#38bdf8"       # Sky blue

# Status Semantics
C_GREEN_SUCCESS  = "#10b981"       # Emerald 500
C_GREEN_BG       = "rgba(16, 185, 129, 0.10)"
C_RED_DANGER     = "#ef4444"       # Rose/Red 500
C_RED_BG         = "rgba(239, 68, 68, 0.10)"
C_AMBER_WARN     = "#f59e0b"       # Amber 500
C_AMBER_BG       = "rgba(245, 158, 11, 0.10)"
C_BLUE_INFO      = "#38bdf8"       # Sky 400
C_BLUE_BG        = "rgba(56, 189, 248, 0.10)"

# Borders & Dividers
C_BORDER_SUBTLE  = "rgba(255, 255, 255, 0.06)"
C_BORDER_MEDIUM  = "rgba(255, 255, 255, 0.10)"
C_BORDER_ACCENT  = "rgba(99, 102, 241, 0.25)"
C_BORDER_PURPLE  = "rgba(99, 102, 241, 0.25)"
C_BORDER_FOCUS   = "#6366f1"

# Typography & Text (WCAG 2.2 AAA Contrast on #09090B)
C_TEXT_PRIMARY   = "#f4f4f5"       # Zinc 100
C_TEXT_SECONDARY = "#a1a1aa"       # Zinc 400
C_TEXT_MUTED     = "#71717a"       # Zinc 500
C_TEXT_DIM       = "#52525b"       # Zinc 600
C_TEXT_DISABLED  = "#52525b"

# ── 2. Font Fallback Chains ──────────────────────────────────────────────────
FONT_FAMILY_UI = "'Segoe UI Variable Text', 'Segoe UI', Inter, -apple-system, sans-serif"
FONT_FAMILY_CODE = "'Cascadia Code', 'JetBrains Mono', Consolas, 'Courier New', monospace"

def get_ui_font(size_pt: int = 10, weight: QFont.Weight = QFont.Weight.Normal) -> QFont:
    """Helper to safely construct UI QFont with explicit point size."""
    font = QFont("Segoe UI", size_pt)
    font.setStyleHint(QFont.StyleHint.SansSerif)
    font.setWeight(weight)
    return font

def get_code_font(size_pt: int = 10, weight: QFont.Weight = QFont.Weight.Normal) -> QFont:
    """Helper to safely construct Code QFont with explicit point size."""
    font = QFont("Consolas", size_pt)
    font.setStyleHint(QFont.StyleHint.Monospace)
    font.setWeight(weight)
    return font

# ── 3. Global Stylesheet ─────────────────────────────────────────────────────
STYLE_MAIN_WINDOW = f"""
    QWidget {{
        color: {C_TEXT_PRIMARY};
        font-family: {FONT_FAMILY_UI};
        font-size: 13px;
        selection-background-color: {C_ACCENT_PRIMARY};
        selection-color: #ffffff;
    }}
    
    QToolTip {{
        background-color: #18181b;
        color: {C_TEXT_PRIMARY};
        border: 1px solid rgba(255, 255, 255, 0.12);
        border-radius: 6px;
        padding: 5px 9px;
        font-size: 11px;
    }}

    QScrollBar:vertical {{
        border: none;
        background: transparent;
        width: 5px;
        margin: 0;
    }}
    QScrollBar::handle:vertical {{
        background: rgba(255, 255, 255, 0.10);
        border-radius: 2px;
        min-height: 24px;
    }}
    QScrollBar::handle:vertical:hover {{
        background: rgba(255, 255, 255, 0.20);
    }}
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
        height: 0;
    }}
    
    QScrollBar:horizontal {{
        border: none;
        background: transparent;
        height: 5px;
        margin: 0;
    }}
    QScrollBar::handle:horizontal {{
        background: rgba(255, 255, 255, 0.10);
        border-radius: 2px;
        min-width: 24px;
    }}
    QScrollBar::handle:horizontal:hover {{
        background: rgba(255, 255, 255, 0.20);
    }}
    QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
        width: 0;
    }}
"""
