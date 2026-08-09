"""
HEADER BAR COMPONENT — sherly_ui/header_bar.py
Top window title bar with dot pattern grid, dynamic window title,
model selection pill badge, settings gear, and window control buttons.
"""

from __future__ import annotations

from PySide6.QtCore import Qt, Signal, QPoint
from PySide6.QtGui import QPainter, QColor, QPen
from PySide6.QtWidgets import (
    QFrame, QHBoxLayout, QLabel, QPushButton, QWidget, QSizePolicy
)

from sherly_ui.theme import (
    C_BG_DARK, C_TEXT_PRIMARY, C_TEXT_MUTED, C_PURPLE_MAIN,
    C_BORDER_SUBTLE, C_RED_DANGER
)


class HeaderBar(QFrame):
    """Custom frameless window header bar."""

    settings_clicked = Signal()
    minimize_clicked = Signal()
    maximize_clicked = Signal()
    close_clicked    = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setFixedHeight(48)
        self.setObjectName("HeaderBar")
        self.setStyleSheet(f"""
            #HeaderBar {{
                background: {C_BG_DARK};
                border-bottom: 1px solid {C_BORDER_SUBTLE};
            }}
        """)
        self._drag_pos: QPoint | None = None
        self._setup_ui()

    def _setup_ui(self) -> None:
        lay = QHBoxLayout(self)
        lay.setContentsMargins(16, 0, 16, 0)
        lay.setSpacing(12)

        # ── App Logo + Dot Pattern Title ──────────────────────────────────────
        logo_lbl = QLabel("🌁")
        logo_lbl.setStyleSheet("font-size: 16px;")
        lay.addWidget(logo_lbl)

        self.title_lbl = QLabel("Sherly — Main Assistant")
        self.title_lbl.setStyleSheet(f"""
            color: {C_TEXT_PRIMARY};
            font-size: 14px;
            font-weight: 700;
            letter-spacing: 0.5px;
        """)
        lay.addWidget(self.title_lbl)

        # Dot-grid pattern spacer
        dots_lbl = QLabel("•  •  •  •  •  •  •  •  •  •  •  •")
        dots_lbl.setStyleSheet("color: rgba(255,255,255,0.12); font-size: 12px; letter-spacing: 4px;")
        lay.addWidget(dots_lbl)

        lay.addStretch()

        # ── Model Pill Badge ──────────────────────────────────────────────────
        self.model_badge = QLabel("Qwen2.5-Coder 3B • Local")
        self.model_badge.setCursor(Qt.CursorShape.PointingHandCursor)
        self.model_badge.setStyleSheet(f"""
            QLabel {{
                background: rgba(139, 92, 246, 0.12);
                color: #a78bfa;
                border: 1px solid rgba(139, 92, 246, 0.3);
                border-radius: 12px;
                padding: 4px 12px;
                font-size: 11px;
                font-weight: 600;
            }}
            QLabel:hover {{
                background: rgba(139, 92, 246, 0.22);
                color: #c4b5fd;
            }}
        """)
        lay.addWidget(self.model_badge)

        # ── Settings Gear Button ──────────────────────────────────────────────
        self.settings_btn = QPushButton("⚙")
        self._style_ctrl_btn(self.settings_btn)
        self.settings_btn.clicked.connect(self.settings_clicked.emit)
        lay.addWidget(self.settings_btn)

        # ── Window Controls ───────────────────────────────────────────────────
        min_btn = QPushButton("–")
        self._style_ctrl_btn(min_btn)
        min_btn.clicked.connect(self.minimize_clicked.emit)
        lay.addWidget(min_btn)

        max_btn = QPushButton("🗖")
        self._style_ctrl_btn(max_btn)
        max_btn.clicked.connect(self.maximize_clicked.emit)
        lay.addWidget(max_btn)

        close_btn = QPushButton("✕")
        self._style_ctrl_btn(close_btn, is_close=True)
        close_btn.clicked.connect(self.close_clicked.emit)
        lay.addWidget(close_btn)

    def _style_ctrl_btn(self, btn: QPushButton, is_close: bool = False) -> None:
        btn.setFixedSize(28, 28)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        if is_close:
            btn.setStyleSheet("""
                QPushButton {
                    background: transparent; color: #888; border: none; font-size: 13px; border-radius: 6px;
                }
                QPushButton:hover {
                    background: rgba(239, 68, 68, 0.2); color: #ef4444;
                }
            """)
        else:
            btn.setStyleSheet("""
                QPushButton {
                    background: transparent; color: #888; border: none; font-size: 13px; border-radius: 6px;
                }
                QPushButton:hover {
                    background: rgba(255, 255, 255, 0.08); color: #f3f4f6;
                }
            """)

    def set_title(self, title: str) -> None:
        self.title_lbl.setText(title)

    def set_model_name(self, name: str) -> None:
        if name:
            self.model_badge.setText(f"{name} • Local" if not name.startswith(("openai", "gemini", "groq")) else f"{name} • Cloud")
        else:
            self.model_badge.setText("No Model Selected")

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
