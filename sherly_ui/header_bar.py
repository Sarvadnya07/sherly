"""
HEADER BAR COMPONENT — sherly_ui/header_bar.py
Top window title bar with vector logo mark, clean breadcrumb,
model status pill badge, settings action, and window control buttons.
"""

from __future__ import annotations

from PySide6.QtCore import Qt, Signal, QPoint, QRectF
from PySide6.QtGui import QPainter, QColor, QPen, QBrush, QPainterPath, QFont
from PySide6.QtWidgets import (
    QFrame, QHBoxLayout, QLabel, QPushButton, QWidget
)

from sherly_ui.theme import (
    C_BG_CANVAS, C_TEXT_PRIMARY, C_TEXT_SECONDARY, C_TEXT_MUTED,
    C_ACCENT_PRIMARY, C_ACCENT_HOVER, C_ACCENT_SURFACE,
    C_BORDER_SUBTLE, C_BORDER_ACCENT, C_GREEN_SUCCESS,
    FONT_FAMILY_UI, FONT_FAMILY_CODE, get_ui_font, get_code_font
)


class SherlyLogoMark(QWidget):
    """Clean vector geometric prism logo for Sherly."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setFixedSize(20, 20)

    def paintEvent(self, _) -> None:
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Draw outer hexagon / diamond prism
        path = QPainterPath()
        path.moveTo(10, 2)
        path.lineTo(18, 6.5)
        path.lineTo(18, 13.5)
        path.lineTo(10, 18)
        path.lineTo(2, 13.5)
        path.lineTo(2, 6.5)
        path.closeSubpath()

        p.fillPath(path, QBrush(QColor(C_ACCENT_PRIMARY)))
        
        # Inner core
        core = QPainterPath()
        core.moveTo(10, 6)
        core.lineTo(14, 10)
        core.lineTo(10, 14)
        core.lineTo(6, 10)
        core.closeSubpath()
        p.fillPath(core, QBrush(QColor("#ffffff")))


class ModelStatusPill(QFrame):
    """Pill badge showing active model and live status indicator."""
    
    clicked = Signal()

    def __init__(self, text: str = "No Model Selected", parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFixedHeight(26)
        self.setObjectName("ModelPill")
        self.setStyleSheet(f"""
            #ModelPill {{
                background: {C_ACCENT_SURFACE};
                border: 1px solid {C_BORDER_ACCENT};
                border-radius: 13px;
                padding: 0px 10px;
            }}
            #ModelPill:hover {{
                background: rgba(124, 58, 237, 0.22);
            }}
        """)
        
        lay = QHBoxLayout(self)
        lay.setContentsMargins(8, 0, 8, 0)
        lay.setSpacing(6)
        
        # Emerald status indicator dot
        self.dot = QFrame()
        self.dot.setFixedSize(6, 6)
        self.dot.setStyleSheet(f"""
            background: {C_GREEN_SUCCESS};
            border-radius: 3px;
        """)
        lay.addWidget(self.dot)
        
        self.label = QLabel(text)
        self.label.setFont(get_code_font(9, QFont.Weight.DemiBold))
        self.label.setStyleSheet(f"color: #c4b5fd; background: transparent; border: none;")
        lay.addWidget(self.label)

    def set_text(self, text: str) -> None:
        self.label.setText(text)

    def mousePressEvent(self, event) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit()


class HeaderBar(QFrame):
    """Custom frameless window header bar."""

    settings_clicked = Signal()
    minimize_clicked = Signal()
    maximize_clicked = Signal()
    close_clicked    = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setFixedHeight(44)
        self.setObjectName("HeaderBar")
        self.setStyleSheet(f"""
            #HeaderBar {{
                background: {C_BG_CANVAS};
                border-bottom: 1px solid {C_BORDER_SUBTLE};
            }}
        """)
        self._drag_pos: QPoint | None = None
        self._setup_ui()

    def _setup_ui(self) -> None:
        lay = QHBoxLayout(self)
        lay.setContentsMargins(14, 0, 14, 0)
        lay.setSpacing(10)

        # ── App Logo Mark ─────────────────────────────────────────────────────
        self.logo = SherlyLogoMark(self)
        lay.addWidget(self.logo)

        # ── App Breadcrumb / Title ────────────────────────────────────────────
        self.title_lbl = QLabel("Sherly")
        self.title_lbl.setFont(get_ui_font(10, QFont.Weight.Bold))
        self.title_lbl.setStyleSheet(f"color: {C_TEXT_PRIMARY}; letter-spacing: 0.2px;")
        lay.addWidget(self.title_lbl)

        self.sub_sep = QLabel("›")
        self.sub_sep.setFont(get_ui_font(10, QFont.Weight.Normal))
        self.sub_sep.setStyleSheet(f"color: {C_TEXT_MUTED};")
        lay.addWidget(self.sub_sep)

        self.sub_title = QLabel("Developer Workspace")
        self.sub_title.setFont(get_ui_font(9, QFont.Weight.Medium))
        self.sub_title.setStyleSheet(f"color: {C_TEXT_SECONDARY};")
        lay.addWidget(self.sub_title)

        lay.addStretch()

        # ── Model Status Badge ────────────────────────────────────────────────
        self.model_badge = ModelStatusPill("Qwen2.5-Coder 3B • Local", self)
        self.model_badge.clicked.connect(self.settings_clicked.emit)
        lay.addWidget(self.model_badge)

        # ── Settings Action ───────────────────────────────────────────────────
        self.settings_btn = QPushButton("⚙")
        self.settings_btn.setFont(get_ui_font(11, QFont.Weight.Normal))
        self.settings_btn.setToolTip("Settings & Model Configuration")
        self._style_ctrl_btn(self.settings_btn)
        self.settings_btn.clicked.connect(self.settings_clicked.emit)
        lay.addWidget(self.settings_btn)

        # ── Window Controls ───────────────────────────────────────────────────
        min_btn = QPushButton("—")
        min_btn.setFont(get_ui_font(10, QFont.Weight.Normal))
        min_btn.setToolTip("Minimize")
        self._style_ctrl_btn(min_btn)
        min_btn.clicked.connect(self.minimize_clicked.emit)
        lay.addWidget(min_btn)

        max_btn = QPushButton("□")
        max_btn.setFont(get_ui_font(11, QFont.Weight.Normal))
        max_btn.setToolTip("Maximize")
        self._style_ctrl_btn(max_btn)
        max_btn.clicked.connect(self.maximize_clicked.emit)
        lay.addWidget(max_btn)

        close_btn = QPushButton("✕")
        close_btn.setFont(get_ui_font(10, QFont.Weight.Normal))
        close_btn.setToolTip("Close")
        self._style_ctrl_btn(close_btn, is_close=True)
        close_btn.clicked.connect(self.close_clicked.emit)
        lay.addWidget(close_btn)

    def _style_ctrl_btn(self, btn: QPushButton, is_close: bool = False) -> None:
        btn.setFixedSize(28, 28)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        if is_close:
            btn.setStyleSheet(f"""
                QPushButton {{
                    background: transparent;
                    color: {C_TEXT_MUTED};
                    border: none;
                    border-radius: 6px;
                }}
                QPushButton:hover {{
                    background: rgba(244, 63, 94, 0.20);
                    color: #f43f5e;
                }}
            """)
        else:
            btn.setStyleSheet(f"""
                QPushButton {{
                    background: transparent;
                    color: {C_TEXT_MUTED};
                    border: none;
                    border-radius: 6px;
                }}
                QPushButton:hover {{
                    background: rgba(255, 255, 255, 0.08);
                    color: {C_TEXT_PRIMARY};
                }}
            """)

    def set_title(self, title: str) -> None:
        if "—" in title:
            parts = [p.strip() for p in title.split("—", 1)]
            self.title_lbl.setText(parts[0])
            self.sub_title.setText(parts[1])
            self.sub_sep.show()
            self.sub_title.show()
        else:
            self.title_lbl.setText(title)
            self.sub_sep.hide()
            self.sub_title.hide()

    def set_model_name(self, name: str) -> None:
        if name:
            is_cloud = name.startswith(("openai", "gemini", "groq", "anthropic"))
            tag = "Cloud" if is_cloud else "Local"
            self.model_badge.set_text(f"{name} • {tag}")
        else:
            self.model_badge.set_text("No Model Selected")

    # ── Window Dragging ───────────────────────────────────────────────────────
    def mousePressEvent(self, event) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            win = self.window()
            if win:
                self._drag_pos = event.globalPosition().toPoint() - win.frameGeometry().topLeft()

    def mouseMoveEvent(self, event) -> None:
        if event.buttons() & Qt.MouseButton.LeftButton and self._drag_pos:
            win = self.window()
            if win:
                win.move(event.globalPosition().toPoint() - self._drag_pos)

