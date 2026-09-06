"""
HEADER BAR COMPONENT — sherly_ui/header_bar.py
Top window title bar with vector logo mark, clean breadcrumb,
model status pill badge, settings action, and window control buttons.
"""

from __future__ import annotations

from PySide6.QtCore import QPoint, Qt, Signal
from PySide6.QtGui import QBrush, QColor, QFont, QPainter, QPainterPath
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QPushButton, QWidget

from sherly_ui.theme import (
    C_ACCENT_PRIMARY,
    C_BG_CANVAS,
    C_BORDER_SUBTLE,
    C_GREEN_SUCCESS,
    C_TEXT_MUTED,
    C_TEXT_PRIMARY,
    C_TEXT_SECONDARY,
    get_code_font,
    get_ui_font,
)


class SherlyLogoMark(QWidget):
    """Clean vector geometric prism logo for Sherly."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setFixedSize(18, 18)

    def paintEvent(self, _) -> None:
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        path = QPainterPath()
        path.moveTo(9, 2)
        path.lineTo(16, 6)
        path.lineTo(16, 12)
        path.lineTo(9, 16)
        path.lineTo(2, 12)
        path.lineTo(2, 6)
        path.closeSubpath()

        p.fillPath(path, QBrush(QColor(C_ACCENT_PRIMARY)))
        
        core = QPainterPath()
        core.moveTo(9, 5)
        core.lineTo(13, 9)
        core.lineTo(9, 13)
        core.lineTo(5, 9)
        core.closeSubpath()
        p.fillPath(core, QBrush(QColor("#ffffff")))


class ModelStatusPill(QFrame):
    """Pill badge showing active model and live status indicator."""
    
    clicked = Signal()

    def __init__(self, text: str = "No Model Selected", parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFixedHeight(24)
        self.setObjectName("ModelPill")
        self.setStyleSheet("""
            #ModelPill {
                background: #18181b;
                border: 1px solid rgba(255, 255, 255, 0.08);
                border-radius: 6px;
                padding: 0px 8px;
            }
            #ModelPill:hover {
                background: #27272a;
                border: 1px solid rgba(255, 255, 255, 0.14);
            }
        """)
        
        lay = QHBoxLayout(self)
        lay.setContentsMargins(6, 0, 6, 0)
        lay.setSpacing(6)
        
        self.dot = QFrame()
        self.dot.setFixedSize(6, 6)
        self.dot.setStyleSheet(f"""
            background: {C_GREEN_SUCCESS};
            border-radius: 3px;
        """)
        lay.addWidget(self.dot)
        
        self.label = QLabel(text)
        self.label.setFont(get_code_font(8, QFont.Weight.Medium))
        self.label.setStyleSheet("color: #d4d4d8; background: transparent; border: none;")
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
        self.setFixedHeight(38)
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
        lay.setContentsMargins(12, 0, 12, 0)
        lay.setSpacing(8)

        # ── App Logo Mark ─────────────────────────────────────────────────────
        self.logo = SherlyLogoMark(self)
        lay.addWidget(self.logo)

        # ── App Breadcrumb / Title ────────────────────────────────────────────
        self.title_lbl = QLabel("Sherly")
        self.title_lbl.setFont(get_ui_font(9, QFont.Weight.Bold))
        self.title_lbl.setStyleSheet(f"color: {C_TEXT_PRIMARY};")
        lay.addWidget(self.title_lbl)

        self.sub_sep = QLabel("/")
        self.sub_sep.setFont(get_ui_font(9, QFont.Weight.Normal))
        self.sub_sep.setStyleSheet(f"color: {C_TEXT_MUTED};")
        lay.addWidget(self.sub_sep)

        self.sub_title = QLabel("Workspace")
        self.sub_title.setFont(get_ui_font(9, QFont.Weight.Normal))
        self.sub_title.setStyleSheet(f"color: {C_TEXT_SECONDARY};")
        lay.addWidget(self.sub_title)

        lay.addStretch()

        # ── Model Status Badge ────────────────────────────────────────────────
        self.model_badge = ModelStatusPill("qwen2.5-coder:3b • Local", self)
        self.model_badge.clicked.connect(self.settings_clicked.emit)
        lay.addWidget(self.model_badge)

        # ── Settings Action ───────────────────────────────────────────────────
        self.settings_btn = QPushButton("⚙")
        self.settings_btn.setFont(get_ui_font(10, QFont.Weight.Normal))
        self.settings_btn.setToolTip("Settings & Model Configuration")
        self._style_ctrl_btn(self.settings_btn)
        self.settings_btn.clicked.connect(self.settings_clicked.emit)
        lay.addWidget(self.settings_btn)

        # ── Window Controls ───────────────────────────────────────────────────
        min_btn = QPushButton("—")
        min_btn.setFont(get_ui_font(9, QFont.Weight.Normal))
        min_btn.setToolTip("Minimize")
        self._style_ctrl_btn(min_btn)
        min_btn.clicked.connect(self.minimize_clicked.emit)
        lay.addWidget(min_btn)

        max_btn = QPushButton("□")
        max_btn.setFont(get_ui_font(10, QFont.Weight.Normal))
        max_btn.setToolTip("Maximize")
        self._style_ctrl_btn(max_btn)
        max_btn.clicked.connect(self.maximize_clicked.emit)
        lay.addWidget(max_btn)

        close_btn = QPushButton("✕")
        close_btn.setFont(get_ui_font(9, QFont.Weight.Normal))
        close_btn.setToolTip("Close")
        self._style_ctrl_btn(close_btn, is_close=True)
        close_btn.clicked.connect(self.close_clicked.emit)
        lay.addWidget(close_btn)

    def _style_ctrl_btn(self, btn: QPushButton, is_close: bool = False) -> None:
        btn.setFixedSize(24, 24)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        if is_close:
            btn.setStyleSheet("""
                QPushButton {
                    background: transparent;
                    color: #71717a;
                    border: none;
                    border-radius: 4px;
                }
                QPushButton:hover {
                    background: rgba(239, 68, 68, 0.20);
                    color: #ef4444;
                }
            """)
        else:
            btn.setStyleSheet("""
                QPushButton {
                    background: transparent;
                    color: #71717a;
                    border: none;
                    border-radius: 4px;
                }
                QPushButton:hover {
                    background: rgba(255, 255, 255, 0.08);
                    color: #f4f4f5;
                }
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
