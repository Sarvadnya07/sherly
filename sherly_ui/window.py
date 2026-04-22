"""
Sherly Assistant – main window (complete redesign)

Layout
──────
┌────────────────────────────────────────────────────────┐
│  Header: logo · title/status · Listen · Power · Settings · – · ✕  │
├────────────┬───────────────────────────────────────────┤
│  Sidebar   │  Chat area (scrollable bubbles)           │
│ (history / │                                           │
│  memory)   │  ───────────────────────────────────────  │
│            │  [  type a message …  ]  [ ⬆ Send ]      │
└────────────┴───────────────────────────────────────────┘
"""

import sys
import random
from datetime import datetime

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QApplication,
    QGraphicsDropShadowEffect, QScrollArea, QFrame, QSizePolicy,
    QPushButton, QDialog, QFormLayout, QComboBox, QLineEdit,
    QCheckBox, QGroupBox, QTextEdit,
)
from PySide6.QtCore import (
    Qt, QTimer, Signal, QObject, QPropertyAnimation, QEasingCurve,
    QSize,
)
from PySide6.QtGui import (
    QColor, QFont, QLinearGradient, QPainter, QPixmap, QFontDatabase,
    QKeyEvent,
)

from config_manager import (
    get_api_key, get_auto_mode, get_current_model,
    set_api_key, set_auto_mode, set_current_model,
)
from plugin_manager import get_all_plugin_states, set_plugin_enabled


# ─────────────────────────────────────────────────────────────────────────────
# Colours / tokens
# ─────────────────────────────────────────────────────────────────────────────
C_BG          = "#0b0b12"
C_SIDEBAR     = "#0d0d16"
C_PANEL       = "#111120"
C_INPUT_BG    = "#161625"
C_BORDER      = "rgba(255,255,255,0.07)"
C_ACCENT      = "#6C63FF"
C_ACCENT2     = "#00ffcc"
C_TEXT        = "#e8e8f0"
C_MUTED       = "rgba(255,255,255,0.35)"
C_USER_BG     = "rgba(108,99,255,0.18)"
C_AI_BG       = "rgba(0,255,204,0.08)"


# ─────────────────────────────────────────────────────────────────────────────
# Signals object shared across threads
# ─────────────────────────────────────────────────────────────────────────────
class UIUpdater(QObject):
    add_msg_sig       = Signal(str, str)
    status_sig        = Signal(str)
    toggle_power_sig  = Signal(bool)
    listen_once_sig   = Signal()
    set_auto_mode_sig = Signal(bool)
    chat_input_sig    = Signal(str)      # user typed something → route_command
    refresh_actions_sig = Signal()       # refresh pending/history panel


# ─────────────────────────────────────────────────────────────────────────────
# Mini waveform (status indicator only – compact)
# ─────────────────────────────────────────────────────────────────────────────
class WaveformWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(80, 28)
        self._timer = QTimer(self)
        self._timer.timeout.connect(self.update)
        self._timer.start(60)
        self._bars = 14
        self._amp  = [random.uniform(0.1, 0.4) for _ in range(self._bars)]
        self.active = False

    def setActive(self, active: bool):
        self.active = active

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        w, h = self.width(), self.height()
        bw  = (w / self._bars) * 0.55
        gap = (w / self._bars) * 0.45

        grad = QLinearGradient(0, 0, 0, h)
        if self.active:
            grad.setColorAt(0, QColor(0, 255, 204))
            grad.setColorAt(1, QColor(108, 99, 255))
        else:
            grad.setColorAt(0, QColor(60, 60, 80))
            grad.setColorAt(1, QColor(30, 30, 50))

        p.setBrush(grad)
        p.setPen(Qt.PenStyle.NoPen)

        for i in range(self._bars):
            if self.active:
                self._amp[i] += (random.uniform(0.15, 1.0) - self._amp[i]) * 0.25
            else:
                self._amp[i] += (0.08 - self._amp[i]) * 0.1
            bh = max(4, self._amp[i] * h)
            x  = i * (bw + gap)
            y  = (h - bh) / 2
            p.drawRoundedRect(int(x), int(y), int(bw), int(bh), bw / 2, bw / 2)


# ─────────────────────────────────────────────────────────────────────────────
# Chat bubble widget
# ─────────────────────────────────────────────────────────────────────────────
class ChatBubble(QFrame):
    """Single exchange: user message on the right, AI reply below on the left."""

    def __init__(self, user_text: str, ai_text: str, time_str: str, parent=None):
        super().__init__(parent)
        self._user  = user_text
        self._ai    = ai_text
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        self.setStyleSheet("background: transparent;")

        root = QVBoxLayout(self)
        root.setContentsMargins(8, 4, 8, 4)
        root.setSpacing(6)

        # ── User bubble (right-aligned) ──────────────────────────────────
        user_row = QHBoxLayout()
        user_row.addStretch()

        user_box = QFrame()
        user_box.setObjectName("UserBubble")
        user_box.setStyleSheet(f"""
            #UserBubble {{
                background: {C_USER_BG};
                border: 1px solid rgba(108,99,255,0.3);
                border-radius: 18px 18px 4px 18px;
                padding: 2px;
            }}
        """)
        user_box_layout = QVBoxLayout(user_box)
        user_box_layout.setContentsMargins(14, 10, 14, 10)
        user_box_layout.setSpacing(2)

        u_lbl = QLabel(user_text)
        u_lbl.setWordWrap(True)
        u_lbl.setMaximumWidth(340)
        u_lbl.setStyleSheet(f"color: {C_TEXT}; font-size: 13px; font-weight: 500; background: transparent;")
        u_lbl.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        user_box_layout.addWidget(u_lbl)

        t_lbl = QLabel(time_str)
        t_lbl.setStyleSheet("color: rgba(255,255,255,0.25); font-size: 9px; background: transparent;")
        t_lbl.setAlignment(Qt.AlignmentFlag.AlignRight)
        user_box_layout.addWidget(t_lbl)

        user_row.addWidget(user_box)
        root.addLayout(user_row)

        # ── AI bubble (left-aligned) ─────────────────────────────────────
        ai_row = QHBoxLayout()

        # small avatar dot
        dot = QLabel("S")
        dot.setFixedSize(28, 28)
        dot.setAlignment(Qt.AlignmentFlag.AlignCenter)
        dot.setStyleSheet(f"""
            background: qlineargradient(x1:0,y1:0,x2:1,y2:1,
                stop:0 {C_ACCENT}, stop:1 #8F94FB);
            color: white; font-size: 12px; font-weight: 800;
            border-radius: 14px;
        """)
        ai_row.addWidget(dot, 0, Qt.AlignmentFlag.AlignTop)
        ai_row.addSpacing(8)

        ai_box = QFrame()
        ai_box.setObjectName("AIBubble")
        ai_box.setStyleSheet(f"""
            #AIBubble {{
                background: {C_AI_BG};
                border: 1px solid rgba(0,255,204,0.15);
                border-radius: 18px 18px 18px 4px;
                padding: 2px;
            }}
        """)
        ai_box_layout = QVBoxLayout(ai_box)
        ai_box_layout.setContentsMargins(14, 10, 14, 10)

        ai_lbl = QLabel(ai_text)
        ai_lbl.setWordWrap(True)
        ai_lbl.setMaximumWidth(360)
        ai_lbl.setStyleSheet(f"color: {C_TEXT}; font-size: 13px; font-weight: 400; background: transparent;")
        ai_lbl.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        ai_box_layout.addWidget(ai_lbl)

        # copy button row
        copy_row = QHBoxLayout()
        copy_row.addStretch()
        self._copy_btn = QPushButton("Copy")
        self._copy_btn.setFixedHeight(22)
        self._copy_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._copy_btn.setStyleSheet("""
            QPushButton {
                background: transparent; color: rgba(255,255,255,0.3);
                border: none; font-size: 10px; padding: 0 6px;
            }
            QPushButton:hover { color: #00ffcc; }
        """)
        self._copy_btn.clicked.connect(self._copy)
        copy_row.addWidget(self._copy_btn)
        ai_box_layout.addLayout(copy_row)

        ai_row.addWidget(ai_box)
        ai_row.addStretch()
        root.addLayout(ai_row)

    def _copy(self):
        QApplication.clipboard().setText(f"You: {self._user}\nSherly: {self._ai}")
        self._copy_btn.setText("Copied!")
        QTimer.singleShot(1200, lambda: self._copy_btn.setText("Copy"))


# ─────────────────────────────────────────────────────────────────────────────
# Send-on-Enter text input
# ─────────────────────────────────────────────────────────────────────────────
class ChatInput(QTextEdit):
    submitted = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setPlaceholderText("Type a message or command… (Enter to send, Shift+Enter for newline)")
        self.setFixedHeight(52)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.document().contentsChanged.connect(self._auto_resize)

    def _auto_resize(self):
        doc_h = int(self.document().size().height()) + 16
        self.setFixedHeight(max(52, min(doc_h, 120)))

    def keyPressEvent(self, event: QKeyEvent):
        if event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            if event.modifiers() & Qt.KeyboardModifier.ShiftModifier:
                super().keyPressEvent(event)
            else:
                text = self.toPlainText().strip()
                if text:
                    self.submitted.emit(text)
                    self.clear()
                    self.setFixedHeight(52)
        else:
            super().keyPressEvent(event)


# ─────────────────────────────────────────────────────────────────────────────
# Main window
# ─────────────────────────────────────────────────────────────────────────────
class SherlyWindow(QWidget):
    def __init__(self):
        super().__init__()

        self.is_powered_on = True
        self.updater = UIUpdater()
        self.updater.add_msg_sig.connect(self._on_add_message)
        self.updater.status_sig.connect(self._on_status)
        self.updater.toggle_power_sig.connect(self.toggle_power)
        self.updater.refresh_actions_sig.connect(self._refresh_action_panel)

        self.setWindowTitle("Sherly AI Desktop")
        from PySide6.QtGui import QIcon
        self.setWindowIcon(QIcon("sherly_ui/assets/brain.png"))
        
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setWindowOpacity(0.0)
        self._drag_pos = None

        self._setup_ui()

        # Fade-in
        self._anim = QPropertyAnimation(self, b"windowOpacity")
        self._anim.setDuration(450)
        self._anim.setStartValue(0.0)
        self._anim.setEndValue(0.97)
        self._anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        self._anim.start()

    # ──────────────────────────────────────────────────────────────────────
    # UI construction
    # ──────────────────────────────────────────────────────────────────────
    def _setup_ui(self):
        self.setFixedSize(820, 600)

        outer = QFrame(self)
        outer.setGeometry(8, 8, 804, 584)
        outer.setObjectName("Outer")
        outer.setStyleSheet(f"""
            #Outer {{
                background: {C_BG};
                border-radius: 28px;
                border: 1px solid {C_BORDER};
            }}
        """)

        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(60)
        shadow.setColor(QColor(0, 0, 0, 200))
        shadow.setOffset(0, 12)
        outer.setGraphicsEffect(shadow)

        root = QHBoxLayout(outer)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        root.addWidget(self._build_sidebar())
        root.addWidget(self._build_main_panel())

    def _build_sidebar(self) -> QWidget:
        side = QFrame()
        side.setFixedWidth(230)
        side.setObjectName("Sidebar")
        side.setStyleSheet(f"""
            #Sidebar {{
                background: {C_SIDEBAR};
                border-top-left-radius: 28px;
                border-bottom-left-radius: 28px;
                border-right: 1px solid {C_BORDER};
            }}
        """)

        lay = QVBoxLayout(side)
        lay.setContentsMargins(16, 24, 16, 24)
        lay.setSpacing(16)

        # Title
        title = QLabel("HISTORY")
        title.setStyleSheet(f"color: {C_MUTED}; font-size: 9px; font-weight: 900; letter-spacing: 3px;")
        lay.addWidget(title)

        # Scroll area for history
        self._hist_scroll = QScrollArea()
        self._hist_scroll.setWidgetResizable(True)
        self._hist_scroll.setFrameShape(QFrame.Shape.NoFrame)
        self._hist_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self._hist_scroll.setStyleSheet("background: transparent;")
        self._hist_scroll.verticalScrollBar().setStyleSheet("""
            QScrollBar:vertical {
                border: none; background: transparent; width: 3px; margin: 0;
            }
            QScrollBar::handle:vertical {
                background: rgba(255,255,255,0.08); border-radius: 2px; min-height: 20px;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
        """)

        self._hist_container = QWidget()
        self._hist_container.setStyleSheet("background: transparent;")
        self._hist_layout = QVBoxLayout(self._hist_container)
        self._hist_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self._hist_layout.setSpacing(8)
        self._hist_layout.setContentsMargins(0, 0, 4, 0)

        self._hist_scroll.setWidget(self._hist_container)
        lay.addWidget(self._hist_scroll)

        # ── Action Panel (pending approvals + recent history) ─────────────
        action_title = QLabel("ACTIONS")
        action_title.setStyleSheet(
            f"color: {C_MUTED}; font-size: 9px; font-weight: 900; letter-spacing: 3px;"
        )
        lay.addWidget(action_title)

        self._action_scroll = QScrollArea()
        self._action_scroll.setWidgetResizable(True)
        self._action_scroll.setFrameShape(QFrame.Shape.NoFrame)
        self._action_scroll.setFixedHeight(160)
        self._action_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self._action_scroll.setStyleSheet("background: transparent;")

        self._action_container = QWidget()
        self._action_container.setStyleSheet("background: transparent;")
        self._action_layout = QVBoxLayout(self._action_container)
        self._action_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self._action_layout.setSpacing(6)
        self._action_layout.setContentsMargins(0, 0, 4, 0)

        self._action_placeholder = QLabel("No pending actions")
        self._action_placeholder.setStyleSheet(f"color: {C_MUTED}; font-size: 10px;")
        self._action_placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._action_layout.addWidget(self._action_placeholder)

        self._action_scroll.setWidget(self._action_container)
        lay.addWidget(self._action_scroll)

        # Status line at bottom of sidebar
        self._sidebar_status = QLabel("Ready")
        self._sidebar_status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._sidebar_status.setStyleSheet(f"color: {C_MUTED}; font-size: 10px;")
        lay.addWidget(self._sidebar_status)

        return side

    def _build_main_panel(self) -> QWidget:
        panel = QFrame()
        panel.setObjectName("Panel")
        panel.setStyleSheet("background: transparent;")

        lay = QVBoxLayout(panel)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)

        lay.addWidget(self._build_header())

        # Thin divider
        div = QFrame()
        div.setFrameShape(QFrame.Shape.HLine)
        div.setStyleSheet(f"color: {C_BORDER};")
        div.setFixedHeight(1)
        lay.addWidget(div)

        lay.addWidget(self._build_chat_area(), stretch=1)

        lay.addWidget(self._build_input_bar())

        return panel

    def _build_header(self) -> QWidget:
        hdr = QFrame()
        hdr.setObjectName("Header")
        hdr.setFixedHeight(64)
        hdr.setStyleSheet("background: transparent;")

        lay = QHBoxLayout(hdr)
        lay.setContentsMargins(24, 0, 16, 0)
        lay.setSpacing(10)

        # Logo circle
        logo = QLabel("S")
        logo.setFixedSize(38, 38)
        logo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        logo.setStyleSheet(f"""
            background: qlineargradient(x1:0,y1:0,x2:1,y2:1,
                stop:0 {C_ACCENT}, stop:1 #8F94FB);
            color: white; font-size: 18px; font-weight: 800; border-radius: 12px;
        """)
        lay.addWidget(logo)
        lay.addSpacing(8)

        # Title + status
        text_col = QVBoxLayout()
        text_col.setSpacing(1)
        t = QLabel("Sherly")
        t.setStyleSheet(f"color: {C_TEXT}; font-size: 16px; font-weight: 700;")
        self.status_header = QLabel("Active")
        self.status_header.setStyleSheet(f"color: {C_ACCENT2}; font-size: 10px; font-weight: 700; letter-spacing: 1px;")
        text_col.addWidget(t)
        text_col.addWidget(self.status_header)
        lay.addLayout(text_col)

        # Waveform (compact)
        self.waveform = WaveformWidget()
        lay.addWidget(self.waveform)

        lay.addStretch()

        # ── Action buttons ────────────────────
        self.listen_btn = self._icon_btn("🎙 Listen", accent=True)
        self.listen_btn.setToolTip("Start Voice Input")
        self.listen_btn.clicked.connect(self.request_single_listen)
        lay.addWidget(self.listen_btn)

        self.power_btn = self._icon_btn("⏻")
        self.power_btn.setFixedSize(38, 38)
        self.power_btn.setToolTip("Power Off/On")
        self.power_btn.setStyleSheet(self._power_style(True))
        self.power_btn.clicked.connect(self.toggle_power)
        lay.addWidget(self.power_btn)

        self.settings_btn = self._icon_btn("⚙")
        self.settings_btn.setFixedSize(38, 38)
        self.settings_btn.setToolTip("Settings")
        self.settings_btn.clicked.connect(self.open_settings_panel)
        lay.addWidget(self.settings_btn)

        min_btn = self._icon_btn("–")
        min_btn.setFixedSize(38, 38)
        min_btn.setToolTip("Minimize")
        min_btn.clicked.connect(self.showMinimized)
        lay.addWidget(min_btn)

        close_btn = self._icon_btn("✕", danger=True)
        close_btn.setFixedSize(38, 38)
        close_btn.setToolTip("Close")
        close_btn.clicked.connect(self.hide)
        lay.addWidget(close_btn)

        return hdr

    def _build_chat_area(self) -> QWidget:
        """Scrollable chat bubble area."""
        self._chat_scroll = QScrollArea()
        self._chat_scroll.setWidgetResizable(True)
        self._chat_scroll.setFrameShape(QFrame.Shape.NoFrame)
        self._chat_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self._chat_scroll.setStyleSheet(f"background: {C_PANEL}; border: none;")
        self._chat_scroll.verticalScrollBar().setStyleSheet("""
            QScrollBar:vertical {
                border: none; background: transparent; width: 4px; margin: 0;
            }
            QScrollBar::handle:vertical {
                background: rgba(255,255,255,0.1); border-radius: 2px; min-height: 30px;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
        """)

        self._chat_container = QWidget()
        self._chat_container.setStyleSheet("background: transparent;")
        self._chat_layout = QVBoxLayout(self._chat_container)
        self._chat_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self._chat_layout.setSpacing(12)
        self._chat_layout.setContentsMargins(16, 16, 16, 16)

        # Placeholder when no messages
        self._empty_label = QLabel("Start talking or type below…")
        self._empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._empty_label.setStyleSheet(f"color: {C_MUTED}; font-size: 13px;")
        self._chat_layout.addStretch()
        self._chat_layout.addWidget(self._empty_label)
        self._chat_layout.addStretch()

        self._chat_scroll.setWidget(self._chat_container)
        return self._chat_scroll

    def _build_input_bar(self) -> QWidget:
        bar = QFrame()
        bar.setObjectName("InputBar")
        bar.setStyleSheet(f"""
            #InputBar {{
                background: {C_INPUT_BG};
                border-top: 1px solid {C_BORDER};
                border-bottom-right-radius: 28px;
            }}
        """)

        lay = QHBoxLayout(bar)
        lay.setContentsMargins(16, 10, 16, 10)
        lay.setSpacing(10)

        self._chat_input = ChatInput()
        self._chat_input.setStyleSheet(f"""
            QTextEdit {{
                background: rgba(255,255,255,0.05);
                color: {C_TEXT};
                border: 1px solid {C_BORDER};
                border-radius: 14px;
                padding: 10px 14px;
                font-size: 13px;
            }}
            QTextEdit:focus {{
                border: 1px solid rgba(108,99,255,0.5);
            }}
        """)
        self._chat_input.submitted.connect(self._on_user_typed)
        lay.addWidget(self._chat_input)

        send_btn = QPushButton("⬆")
        send_btn.setFixedSize(44, 44)
        send_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        send_btn.setStyleSheet(f"""
            QPushButton {{
                background: {C_ACCENT};
                color: white; border-radius: 14px; font-size: 18px; font-weight: 700;
            }}
            QPushButton:hover {{
                background: #7B74FF;
            }}
            QPushButton:pressed {{
                background: #5a54cc;
            }}
        """)
        send_btn.clicked.connect(self._send_from_btn)
        lay.addWidget(send_btn)

        return bar

    # ──────────────────────────────────────────────────────────────────────
    # Helper: create a styled icon button
    # ──────────────────────────────────────────────────────────────────────
    def _icon_btn(self, label: str, *, accent: bool = False, danger: bool = False) -> QPushButton:
        btn = QPushButton(label)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.setFixedHeight(38)
        btn.setSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed)

        if accent:
            btn.setStyleSheet(f"""
                QPushButton {{
                    background: rgba(108,99,255,0.15); color: {C_ACCENT};
                    border: 1px solid rgba(108,99,255,0.35); border-radius: 12px;
                    font-size: 12px; font-weight: 700; padding: 0 14px;
                }}
                QPushButton:hover {{ background: rgba(108,99,255,0.28); }}
            """)
        elif danger:
            btn.setStyleSheet("""
                QPushButton { background: transparent; color: #555; border-radius: 12px; font-size: 16px; }
                QPushButton:hover { background: rgba(255,50,50,0.15); color: #ff5555; }
            """)
        else:
            btn.setStyleSheet(f"""
                QPushButton {{
                    background: rgba(255,255,255,0.05); color: {C_MUTED};
                    border: 1px solid {C_BORDER}; border-radius: 12px; font-size: 16px;
                }}
                QPushButton:hover {{ background: rgba(255,255,255,0.1); color: {C_TEXT}; }}
            """)
        return btn

    def _power_style(self, on: bool) -> str:
        if on:
            return f"""
                QPushButton {{
                    background: rgba(0,255,204,0.1); color: {C_ACCENT2};
                    border: 1px solid rgba(0,255,204,0.35); border-radius: 12px; font-size: 18px;
                }}
                QPushButton:hover {{ background: rgba(0,255,204,0.22); }}
            """
        return """
            QPushButton {
                background: rgba(255,50,50,0.1); color: #ff5555;
                border: 1px solid rgba(255,50,50,0.35); border-radius: 12px; font-size: 18px;
            }
            QPushButton:hover { background: rgba(255,50,50,0.22); }
        """

    # ──────────────────────────────────────────────────────────────────────
    # Chat logic
    # ──────────────────────────────────────────────────────────────────────
    def _on_user_typed(self, text: str):
        """Called when user presses Enter in the chat input."""
        # Show optimistic user bubble immediately
        self._add_bubble(text, "…thinking…")
        # Emit signal → app_manager routes to worker
        self.updater.chat_input_sig.emit(text)

    def _send_from_btn(self):
        text = self._chat_input.toPlainText().strip()
        if text:
            self._chat_input.clear()
            self._chat_input.setFixedHeight(52)
            self._on_user_typed(text)

    def _add_bubble(self, user_text: str, ai_text: str):
        """Append a new chat bubble. If ai_text is placeholder, mark it pending."""
        # Remove empty state widgets if first message
        if self._empty_label is not None:
            self._empty_label.hide()

        time_str = datetime.now().strftime("%I:%M %p")
        bubble = ChatBubble(user_text, ai_text, time_str)
        self._chat_layout.addWidget(bubble)

        # Scroll to bottom
        QTimer.singleShot(60, self._scroll_to_bottom)
        return bubble

    def _scroll_to_bottom(self):
        sb = self._chat_scroll.verticalScrollBar()
        sb.setValue(sb.maximum())

    # ──────────────────────────────────────────────────────────────────────
    # Public API used by app_manager
    # ──────────────────────────────────────────────────────────────────────
    def add_message(self, text: str, response: str):
        """Called from worker thread via signal."""
        self.updater.add_msg_sig.emit(text, response)

    def _on_add_message(self, text: str, response: str):
        """GUI thread: add to chat area AND sidebar history mini-card."""
        self._add_bubble(text, response)
        self._add_history_card(text, response)
        self._sidebar_status.setText(datetime.now().strftime("%I:%M %p"))
        # Refresh action panel after every response (pending may have changed)
        self._refresh_action_panel()

    def _refresh_action_panel(self):
        """
        Rebuild the sidebar action panel with current pending approvals
        and the last 5 action history entries.  Called on the GUI thread via signal.
        """
        try:
            from action_manager import _pending_actions, _action_history
        except Exception:
            return

        # Clear existing widgets
        while self._action_layout.count():
            item = self._action_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        has_content = False

        # ── Pending approvals ──────────────────────────────────────────────
        import threading as _threading
        pending = {}
        with _threading.Lock():
            pending = dict(_pending_actions)

        try:
            from tools.preview import preview_store
            for aid, p_data in preview_store.items():
                pending[aid] = {"cmd": f"Preview: {p_data['file']}"}
        except Exception:
            pass

        if pending:
            hdr = QLabel("⏳ Awaiting Approval")
            hdr.setStyleSheet(f"color: #ffaa33; font-size: 9px; font-weight: 900; letter-spacing: 2px;")
            self._action_layout.addWidget(hdr)
            has_content = True

            for aid, entry in list(pending.items()):
                card = QFrame()
                card.setObjectName("PendCard")
                card.setStyleSheet(f"""
                    #PendCard {{
                        background: rgba(255,170,51,0.07);
                        border: 1px solid rgba(255,170,51,0.3);
                        border-radius: 8px;
                    }}
                """)
                cl = QVBoxLayout(card)
                cl.setContentsMargins(8, 6, 8, 6)
                cl.setSpacing(4)

                cmd_lbl = QLabel(entry["cmd"][:45] + ("…" if len(entry["cmd"]) > 45 else ""))
                cmd_lbl.setWordWrap(True)
                cmd_lbl.setStyleSheet(f"color: {C_TEXT}; font-size: 10px; font-weight: 600;")
                id_lbl = QLabel(f"ID: {aid}")
                id_lbl.setStyleSheet(f"color: {C_MUTED}; font-size: 9px;")
                cl.addWidget(cmd_lbl)
                cl.addWidget(id_lbl)

                btn_row = QHBoxLayout()
                approve_btn = QPushButton("✓ Approve")
                cancel_btn  = QPushButton("✕ Cancel")
                for b in (approve_btn, cancel_btn):
                    b.setFixedHeight(22)
                    b.setCursor(Qt.CursorShape.PointingHandCursor)

                approve_btn.setStyleSheet("""
                    QPushButton { background: rgba(0,255,100,0.15); color: #00ff88;
                        border: 1px solid rgba(0,255,100,0.3); border-radius: 6px; font-size: 10px; }
                    QPushButton:hover { background: rgba(0,255,100,0.25); }
                """)
                cancel_btn.setStyleSheet("""
                    QPushButton { background: rgba(255,50,50,0.1); color: #ff5555;
                        border: 1px solid rgba(255,50,50,0.3); border-radius: 6px; font-size: 10px; }
                    QPushButton:hover { background: rgba(255,50,50,0.2); }
                """)
                _aid = aid
                approve_btn.clicked.connect(lambda _, a=_aid: self.updater.chat_input_sig.emit(f"approve {a}"))
                cancel_btn.clicked.connect(lambda _, a=_aid: self.updater.chat_input_sig.emit(f"cancel {a}"))
                btn_row.addWidget(approve_btn)
                btn_row.addWidget(cancel_btn)
                cl.addLayout(btn_row)

                self._action_layout.addWidget(card)

        # ── Recent history ─────────────────────────────────────────────────
        history = list(_action_history)[:5]
        if history:
            hdr2 = QLabel("📋 Recent Actions")
            hdr2.setStyleSheet(f"color: {C_MUTED}; font-size: 9px; font-weight: 900; letter-spacing: 2px; margin-top: 4px;")
            self._action_layout.addWidget(hdr2)
            has_content = True

            for entry in history:
                flag = "↩" if entry["undoable"] else "🔒"
                row = QLabel(f"{flag} {entry['action'][:40]}{'…' if len(entry['action']) > 40 else ''}")
                row.setWordWrap(True)
                row.setStyleSheet(f"color: {C_MUTED}; font-size: 10px; padding: 2px 0;")
                self._action_layout.addWidget(row)

        if not has_content:
            ph = QLabel("No pending actions")
            ph.setStyleSheet(f"color: {C_MUTED}; font-size: 10px;")
            ph.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self._action_layout.addWidget(ph)



    def _add_history_card(self, user: str, ai: str):
        card = QFrame()
        card.setObjectName("HCard")
        card.setStyleSheet(f"""
            #HCard {{
                background: rgba(255,255,255,0.03);
                border: 1px solid {C_BORDER};
                border-radius: 10px;
            }}
            #HCard:hover {{
                background: rgba(108,99,255,0.08);
                border: 1px solid rgba(108,99,255,0.3);
            }}
        """)
        cl = QVBoxLayout(card)
        cl.setContentsMargins(10, 8, 10, 8)
        cl.setSpacing(3)

        u = QLabel(user[:40] + ("…" if len(user) > 40 else ""))
        u.setStyleSheet(f"color: rgba(108,99,255,0.9); font-size: 10px; font-weight: 700;")
        u.setWordWrap(True)

        a = QLabel(ai[:60] + ("…" if len(ai) > 60 else ""))
        a.setStyleSheet(f"color: {C_MUTED}; font-size: 10px;")
        a.setWordWrap(True)

        cl.addWidget(u)
        cl.addWidget(a)
        self._hist_layout.insertWidget(0, card)

    def set_status(self, text: str):
        self.updater.status_sig.emit(text)

    def _on_status(self, text: str):
        low = text.lower()
        self._sidebar_status.setText(text)

        if "listening" in low or "recording" in low:
            self.waveform.setActive(True)
            self.status_header.setText("Listening")
            self.status_header.setStyleSheet(f"color: {C_ACCENT2}; font-size: 10px; font-weight: 700;")
        elif "thinking" in low:
            self.waveform.setActive(True)
            self.status_header.setText("Thinking")
            self.status_header.setStyleSheet("color: #ffaa33; font-size: 10px; font-weight: 700;")
        elif "speaking" in low:
            self.waveform.setActive(True)
            self.status_header.setText("Speaking")
            self.status_header.setStyleSheet(f"color: {C_ACCENT}; font-size: 10px; font-weight: 700;")
        else:
            self.waveform.setActive(False)
            if self.is_powered_on:
                self.status_header.setText("Active")
                self.status_header.setStyleSheet(f"color: {C_ACCENT2}; font-size: 10px; font-weight: 700;")

    # ──────────────────────────────────────────────────────────────────────
    # Power toggle
    # ──────────────────────────────────────────────────────────────────────
    def toggle_power(self, state=None):
        if state is not None:
            if self.is_powered_on == state:
                return
            self.is_powered_on = state
        else:
            self.is_powered_on = not self.is_powered_on
            self.updater.toggle_power_sig.emit(self.is_powered_on)

        self.power_btn.setStyleSheet(self._power_style(self.is_powered_on))

        if self.is_powered_on:
            self.status_header.setText("Active")
            self.status_header.setStyleSheet(f"color: {C_ACCENT2}; font-size: 10px; font-weight: 700;")
        else:
            self.status_header.setText("Paused")
            self.status_header.setStyleSheet("color: #ff5555; font-size: 10px; font-weight: 700;")
            self.waveform.setActive(False)

    # ──────────────────────────────────────────────────────────────────────
    # Other actions
    # ──────────────────────────────────────────────────────────────────────
    def open_settings_panel(self):
        SettingsDialog(self).exec()

    def request_single_listen(self):
        self.updater.listen_once_sig.emit()

    # ──────────────────────────────────────────────────────────────────────
    # Drag to move
    # ──────────────────────────────────────────────────────────────────────
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_pos = event.globalPosition().toPoint()

    def mouseMoveEvent(self, event):
        if event.buttons() & Qt.MouseButton.LeftButton and self._drag_pos:
            delta = event.globalPosition().toPoint() - self._drag_pos
            self.move(self.x() + delta.x(), self.y() + delta.y())
            self._drag_pos = event.globalPosition().toPoint()


# ─────────────────────────────────────────────────────────────────────────────
# Settings dialog (styled to match new dark theme)
# ─────────────────────────────────────────────────────────────────────────────
class SettingsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Sherly Settings")
        self.setModal(True)
        self.setFixedSize(440, 540)
        self.setStyleSheet(f"""
            QDialog {{ background: #0d0d18; color: {C_TEXT}; }}
            QLabel {{ color: {C_TEXT}; font-size: 12px; }}
            QComboBox, QLineEdit {{
                background: rgba(255,255,255,0.06);
                color: {C_TEXT}; border: 1px solid {C_BORDER};
                border-radius: 8px; padding: 6px 10px; font-size: 12px;
            }}
            QCheckBox {{ color: {C_TEXT}; spacing: 8px; font-size: 12px; }}
            QGroupBox {{
                color: {C_MUTED}; font-size: 10px; font-weight: 700;
                border: 1px solid {C_BORDER}; border-radius: 10px; margin-top: 10px;
                padding: 12px;
            }}
            QPushButton {{
                background: rgba(108,99,255,0.2); color: {C_ACCENT};
                border: 1px solid rgba(108,99,255,0.4); border-radius: 8px;
                padding: 8px 20px; font-size: 12px; font-weight: 700;
            }}
            QPushButton:hover {{ background: rgba(108,99,255,0.35); }}
        """)

        lay = QVBoxLayout(self)
        lay.setContentsMargins(24, 24, 24, 24)
        lay.setSpacing(16)

        form = QFormLayout()
        form.setSpacing(12)

        self.model_combo = QComboBox()
        for opt in ["phi3", "tinyllama", "openai", "gemini", "groq"]:
            self.model_combo.addItem(opt)
        self.model_combo.setCurrentText(get_current_model())
        form.addRow("Active model", self.model_combo)

        self.api_inputs: dict[str, QLineEdit] = {}
        for prov in ["openai", "gemini", "groq"]:
            f = QLineEdit(get_api_key(prov) or "")
            f.setPlaceholderText(f"{prov.upper()} API Key")
            f.setEchoMode(QLineEdit.EchoMode.Password)
            self.api_inputs[prov] = f
            form.addRow(f"{prov.upper()} API Key", f)

        lay.addLayout(form)

        self.auto_cb = QCheckBox("Enable auto-mode (continuous listening)")
        self.auto_cb.setChecked(get_auto_mode())
        lay.addWidget(self.auto_cb)

        pg = QGroupBox("Plugins")
        pl = QVBoxLayout(pg)
        self.plugin_cbs: dict[str, QCheckBox] = {}
        states = get_all_plugin_states()
        if states:
            for name, en in states.items():
                cb = QCheckBox(name)
                cb.setChecked(en)
                pl.addWidget(cb)
                self.plugin_cbs[name] = cb
        else:
            pl.addWidget(QLabel("No plugins found."))
        lay.addWidget(pg)

        lay.addStretch()

        btns = QHBoxLayout()
        btns.addStretch()
        apply_btn = QPushButton("Apply")
        close_btn = QPushButton("Close")
        close_btn.setStyleSheet("background: rgba(255,255,255,0.05); color: #888; border: 1px solid rgba(255,255,255,0.08);")
        apply_btn.clicked.connect(self._apply)
        close_btn.clicked.connect(self.reject)
        btns.addWidget(close_btn)
        btns.addWidget(apply_btn)
        lay.addLayout(btns)

    def _apply(self):
        set_current_model(self.model_combo.currentText())
        for prov, f in self.api_inputs.items():
            set_api_key(prov, f.text().strip())
        auto = self.auto_cb.isChecked()
        set_auto_mode(auto)
        if (p := self.parent()) and hasattr(p, "updater"):
            p.updater.set_auto_mode_sig.emit(auto)
        for name, cb in self.plugin_cbs.items():
            set_plugin_enabled(name, cb.isChecked())
        self.accept()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    w = SherlyWindow()
    w.show()
    sys.exit(app.exec())
