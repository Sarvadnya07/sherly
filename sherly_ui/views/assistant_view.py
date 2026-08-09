"""
MAIN ASSISTANT VIEW — sherly_ui/views/assistant_view.py
Dynamic Main Assistant view:
  - Real file attachments via QFileDialog
  - Connected vertical timeline stream displaying user prompts, thinking states, and AI responses
  - Floating prompt bar with file attachment pill and submit action
"""

from __future__ import annotations

from pathlib import Path
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QFrame, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QTextEdit,
    QScrollArea, QWidget, QFileDialog
)

from sherly_ui.theme import (
    C_BG_PANEL, C_BG_CARD, C_TEXT_PRIMARY, C_TEXT_MUTED, C_TEXT_DIM,
    C_PURPLE_MAIN, C_BORDER_SUBTLE
)


class UserMessageNode(QFrame):
    """User prompt timeline node."""

    def __init__(self, prompt: str, attached_file: str | None = None, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setStyleSheet("background: transparent;")
        lay = QHBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(12)

        dot = QLabel("👤")
        dot.setFixedSize(26, 26)
        dot.setAlignment(Qt.AlignmentFlag.AlignCenter)
        dot.setStyleSheet("background: rgba(255,255,255,0.08); border-radius: 13px; font-size: 11px;")
        lay.addWidget(dot, 0, Qt.AlignmentFlag.AlignTop)

        card = QFrame()
        card.setStyleSheet(f"background: {C_BG_CARD}; border: 1px solid {C_BORDER_SUBTLE}; border-radius: 12px; padding: 10px 14px;")
        c_lay = QVBoxLayout(card)
        c_lay.setContentsMargins(12, 10, 12, 10)
        c_lay.setSpacing(6)

        p_lbl = QLabel(prompt)
        p_lbl.setWordWrap(True)
        p_lbl.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        p_lbl.setStyleSheet(f"color: {C_TEXT_PRIMARY}; font-size: 13px; font-weight: 600;")
        c_lay.addWidget(p_lbl)

        if attached_file:
            att_pill = QLabel(f"📄 {Path(attached_file).name}")
            att_pill.setStyleSheet("""
                background: rgba(255, 255, 255, 0.05);
                color: #aaa;
                border: 1px solid rgba(255, 255, 255, 0.1);
                border-radius: 8px;
                padding: 4px 10px;
                font-size: 11px;
            """)
            c_lay.addWidget(att_pill, 0, Qt.AlignmentFlag.AlignLeft)

        lay.addWidget(card, stretch=1)


class ThinkingNode(QFrame):
    """Thinking / processing indicator node."""

    def __init__(self, text: str = "Thinking...", parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setStyleSheet("background: transparent;")
        lay = QHBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(12)

        dot = QLabel("⚙")
        dot.setFixedSize(26, 26)
        dot.setAlignment(Qt.AlignmentFlag.AlignCenter)
        dot.setStyleSheet("background: rgba(139, 92, 246, 0.15); color: #a78bfa; border-radius: 13px; font-size: 12px;")
        lay.addWidget(dot)

        self.t_lbl = QLabel(text)
        self.t_lbl.setStyleSheet(f"color: {C_TEXT_MUTED}; font-size: 12px; font-weight: 500;")
        lay.addWidget(self.t_lbl)
        lay.addStretch()

    def set_text(self, text: str) -> None:
        self.t_lbl.setText(text)


class AssistantMessageNode(QFrame):
    """Assistant response timeline node."""

    def __init__(self, response_text: str, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setStyleSheet("background: transparent;")
        lay = QHBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(12)

        dot = QLabel("S")
        dot.setFixedSize(26, 26)
        dot.setAlignment(Qt.AlignmentFlag.AlignCenter)
        dot.setStyleSheet("background: #8b5cf6; color: white; border-radius: 13px; font-size: 11px; font-weight: 800;")
        lay.addWidget(dot, 0, Qt.AlignmentFlag.AlignTop)

        card = QFrame()
        card.setStyleSheet(f"background: {C_BG_CARD}; border: 1px solid rgba(139, 92, 246, 0.25); border-radius: 12px; padding: 14px 18px;")
        c_lay = QVBoxLayout(card)
        c_lay.setContentsMargins(14, 12, 14, 12)
        c_lay.setSpacing(8)

        r_lbl = QLabel(response_text)
        r_lbl.setWordWrap(True)
        r_lbl.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        r_lbl.setStyleSheet(f"color: {C_TEXT_PRIMARY}; font-size: 13px; line-height: 1.4;")
        c_lay.addWidget(r_lbl)

        lay.addWidget(card, stretch=1)


class AssistantView(QFrame):
    """Dynamic Main Assistant View."""

    message_submitted = Signal(str)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._attached_file_path: str | None = None
        self._thinking_node: ThinkingNode | None = None
        self.setObjectName("AssistantView")
        self.setStyleSheet(f"""
            #AssistantView {{
                background: {C_BG_PANEL};
            }}
        """)
        self._setup_ui()

    def _setup_ui(self) -> None:
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)

        # Timeline Scroll Area
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setFrameShape(QFrame.Shape.NoFrame)

        self.stream_container = QWidget()
        self.stream_lay = QVBoxLayout(self.stream_container)
        self.stream_lay.setContentsMargins(24, 24, 24, 24)
        self.stream_lay.setSpacing(14)
        self.stream_lay.setAlignment(Qt.AlignmentFlag.AlignTop)

        # Welcome message
        welcome_node = AssistantMessageNode("Hello! I'm Sherly. How can I assist you with your project today?")
        self.stream_lay.addWidget(welcome_node)

        self.scroll.setWidget(self.stream_container)
        lay.addWidget(self.scroll, stretch=1)

        # Bottom Input Bar Container
        input_container = QWidget()
        ic_lay = QVBoxLayout(input_container)
        ic_lay.setContentsMargins(24, 8, 24, 16)
        ic_lay.setSpacing(4)

        # Attached File Indicator Pill
        self.att_indicator = QLabel()
        self.att_indicator.hide()
        self.att_indicator.setStyleSheet("color: #a78bfa; font-size: 11px; font-weight: 600; padding-left: 8px;")
        ic_lay.addWidget(self.att_indicator)

        bar = QFrame()
        bar.setStyleSheet(f"""
            QFrame {{
                background: #11111a;
                border: 1px solid {C_BORDER_SUBTLE};
                border-radius: 18px;
            }}
            QFrame:focus-within {{
                border: 1px solid rgba(139, 92, 246, 0.4);
            }}
        """)
        b_lay = QHBoxLayout(bar)
        b_lay.setContentsMargins(12, 6, 12, 6)
        b_lay.setSpacing(10)

        attach_btn = QPushButton("+")
        attach_btn.setFixedSize(28, 28)
        attach_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        attach_btn.setToolTip("Attach File")
        attach_btn.setStyleSheet("background: transparent; color: #888; border: none; font-size: 18px;")
        attach_btn.clicked.connect(self._browse_file)
        b_lay.addWidget(attach_btn)

        self.input_edit = QTextEdit()
        self.input_edit.setPlaceholderText("Ask Sherly anything...")
        self.input_edit.setFixedHeight(34)
        self.input_edit.setFrameShape(QFrame.Shape.NoFrame)
        self.input_edit.setStyleSheet(f"background: transparent; color: {C_TEXT_PRIMARY}; font-size: 13px;")
        b_lay.addWidget(self.input_edit, stretch=1)

        send_btn = QPushButton("⬆")
        send_btn.setFixedSize(32, 32)
        send_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        send_btn.setStyleSheet("""
            QPushButton {
                background: #8b5cf6; color: white; border: none; border-radius: 10px; font-size: 14px; font-weight: 700;
            }
            QPushButton:hover { background: #9d7aea; }
        """)
        send_btn.clicked.connect(self._submit)
        b_lay.addWidget(send_btn)

        ic_lay.addWidget(bar)
        lay.addWidget(input_container)

    def _browse_file(self) -> None:
        file_path, _ = QFileDialog.getOpenFileName(self, "Attach File to Assistant", str(Path.cwd()))
        if file_path:
            self._attached_file_path = file_path
            self.att_indicator.setText(f"Attached: {Path(file_path).name} ✕")
            self.att_indicator.show()

    def _submit(self) -> None:
        text = self.input_edit.toPlainText().strip()
        if not text:
            return

        self.input_edit.clear()
        att = self._attached_file_path
        self._attached_file_path = None
        self.att_indicator.hide()

        # Add user prompt node
        u_node = UserMessageNode(text, attached_file=att)
        self.stream_lay.addWidget(u_node)

        # Show thinking node
        self._thinking_node = ThinkingNode("Thinking...")
        self.stream_lay.addWidget(self._thinking_node)

        self._scroll_to_bottom()
        full_prompt = f"File: {att}\n{text}" if att else text
        self.message_submitted.emit(full_prompt)

    def add_response(self, text: str, response: str) -> None:
        """Called when AI worker completes response."""
        if self._thinking_node:
            self.stream_lay.removeWidget(self._thinking_node)
            self._thinking_node.deleteLater()
            self._thinking_node = None

        a_node = AssistantMessageNode(response)
        self.stream_lay.addWidget(a_node)
        self._scroll_to_bottom()

    def _scroll_to_bottom(self) -> None:
        sb = self.scroll.verticalScrollBar()
        sb.setValue(sb.maximum())
