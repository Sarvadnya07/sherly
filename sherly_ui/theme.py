"""
SHERLY UI DESIGN SYSTEM & THEME TOKENS
Matches the high-end dark theme aesthetic from the screenshots.
"""

from PySide6.QtGui import QColor, QFont

# ── Color Palette ─────────────────────────────────────────────────────────────
C_BG_DARK        = "#09090d"       # Deepest background
C_BG_PANEL       = "#0e0e15"       # Main panel background
C_BG_CARD        = "#13131e"       # Card / container background
C_BG_SIDEBAR     = "#0b0b11"       # Sidebar background
C_BG_INPUT       = "#161624"       # Input field background
C_BG_HOVER       = "rgba(255, 255, 255, 0.05)"

# Accents
C_PURPLE_MAIN    = "#8b5cf6"       # Vibrant primary purple
C_PURPLE_GLOW    = "rgba(139, 92, 246, 0.25)"
C_PURPLE_DARK    = "#6d28d9"
C_CYAN_ACCENT    = "#00f0ff"       # Neon cyan
C_GREEN_SUCCESS  = "#10b981"       # Emerald green for Accept/Success
C_GREEN_BG       = "rgba(16, 185, 129, 0.12)"
C_RED_DANGER     = "#ef4444"       # Red for Reject/Delete
C_RED_BG         = "rgba(239, 68, 68, 0.12)"
C_AMBER_WARN     = "#f59e0b"       # Warning amber

# Borders & Text
C_BORDER_SUBTLE  = "rgba(255, 255, 255, 0.07)"
C_BORDER_PURPLE  = "rgba(139, 92, 246, 0.35)"
C_TEXT_PRIMARY   = "#f3f4f6"       # Pure crisp white-gray
C_TEXT_MUTED     = "rgba(255, 255, 255, 0.45)"
C_TEXT_DIM       = "rgba(255, 255, 255, 0.25)"

# ── Common Stylesheets ────────────────────────────────────────────────────────
STYLE_MAIN_WINDOW = f"""
    QWidget {{
        color: {C_TEXT_PRIMARY};
        font-family: 'Segoe UI', 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    }}
    QScrollBar:vertical {{
        border: none; background: transparent; width: 5px; margin: 0;
    }}
    QScrollBar::handle:vertical {{
        background: rgba(255, 255, 255, 0.12); border-radius: 2px; min-height: 20px;
    }}
    QScrollBar::handle:vertical:hover {{
        background: {C_PURPLE_MAIN};
    }}
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}
"""
