"""
SHERLY UI DESIGN SYSTEM & THEME TOKENS — sherly_ui/theme.py
Canonical design system tokens, typography scales, and global Qt stylesheets.
"""

from __future__ import annotations
from PySide6.QtGui import QColor, QFont

# ── 1. Color Palette (Obsidian Dark Theme) ──────────────────────────────────
# Canvas & Surfaces
C_BG_CANVAS      = "#07070b"       # Deepest obsidian canvas
C_BG_DARK        = "#07070b"       # Backward-compat alias for canvas
C_BG_SIDEBAR     = "#0b0b10"       # Left navigation rail
C_BG_SURFACE     = "#0f0f16"       # Main workspace and panels
C_BG_PANEL       = "#0f0f16"       # Backward-compat alias for surface
C_BG_CARD        = "#14141f"       # Embedded cards and message nodes
C_BG_CARD_HOVER  = "#1a1a2a"       # Hovered card state
C_BG_INPUT       = "#11111a"       # Text inputs and textareas
C_BG_HOVER       = "rgba(255, 255, 255, 0.05)"

# Brand Accents & Radiant Glow
C_ACCENT_PRIMARY = "#7c3aed"       # Violet 600
C_ACCENT_HOVER   = "#8b5cf6"       # Violet 500
C_ACCENT_LIGHT   = "#a78bfa"       # Violet 400
C_ACCENT_SURFACE = "rgba(124, 58, 237, 0.14)" # Tinted surface
C_ACCENT_GLOW    = "rgba(124, 58, 237, 0.25)" # Radiant glow
C_PURPLE_MAIN    = "#7c3aed"
C_PURPLE_GLOW    = "rgba(124, 58, 237, 0.25)"
C_PURPLE_DARK    = "#5b21b6"
C_CYAN_ACCENT    = "#38bdf8"       # Sky blue

# Status Semantics
C_GREEN_SUCCESS  = "#10b981"       # Emerald 500
C_GREEN_BG       = "rgba(16, 185, 129, 0.12)"
C_RED_DANGER     = "#f43f5e"       # Rose 500
C_RED_BG         = "rgba(244, 63, 94, 0.12)"
C_AMBER_WARN     = "#f59e0b"       # Amber 500
C_AMBER_BG       = "rgba(245, 158, 11, 0.12)"
C_BLUE_INFO      = "#38bdf8"       # Sky 400
C_BLUE_BG        = "rgba(56, 189, 248, 0.12)"

# Borders & Dividers
C_BORDER_SUBTLE  = "rgba(255, 255, 255, 0.07)"
C_BORDER_MEDIUM  = "rgba(255, 255, 255, 0.14)"
C_BORDER_ACCENT  = "rgba(124, 58, 237, 0.40)"
C_BORDER_PURPLE  = "rgba(124, 58, 237, 0.40)"
C_BORDER_FOCUS   = "#8b5cf6"

# Typography & Text (WCAG 2.2 AAA Contrast on #07070B)
C_TEXT_PRIMARY   = "#f8fafc"       # Pure crisp white
C_TEXT_SECONDARY = "#94a3b8"       # Slate 400
C_TEXT_MUTED     = "#64748b"       # Slate 500
C_TEXT_DIM       = "#475569"       # Slate 600
C_TEXT_DISABLED  = "#475569"

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
        background-color: {C_BG_CARD};
        color: {C_TEXT_PRIMARY};
        border: 1px solid {C_BORDER_MEDIUM};
        border-radius: 6px;
        padding: 5px 9px;
        font-size: 11px;
    }}

    QScrollBar:vertical {{
        border: none;
        background: transparent;
        width: 6px;
        margin: 0;
    }}
    QScrollBar::handle:vertical {{
        background: rgba(255, 255, 255, 0.12);
        border-radius: 3px;
        min-height: 24px;
    }}
    QScrollBar::handle:vertical:hover {{
        background: {C_ACCENT_PRIMARY};
    }}
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
        height: 0;
    }}
    
    QScrollBar:horizontal {{
        border: none;
        background: transparent;
        height: 6px;
        margin: 0;
    }}
    QScrollBar::handle:horizontal {{
        background: rgba(255, 255, 255, 0.12);
        border-radius: 3px;
        min-width: 24px;
    }}
    QScrollBar::handle:horizontal:hover {{
        background: {C_ACCENT_PRIMARY};
    }}
    QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
        width: 0;
    }}
"""

