"""
MAIN ASSISTANT VIEW — sherly_ui/views/assistant_view.py
Modern Cursor / VS Code Copilot style AI assistant view:
  - Clean timeline stream with elegant user cards and rich assistant markdown responses
  - Code block formatting and one-click copy to clipboard
  - Bottom docked composer with file attachment, voice shortcut, and auto-expanding input
"""

from __future__ import annotations

import re
from pathlib import Path
from PySide6.QtCore import Qt, Signal, QTimer, QEvent
from PySide6.QtGui import QFont, QGuiApplication, QKeyEvent
from PySide6.QtWidgets import (
    QFrame, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QTextEdit,
    QScrollArea, QWidget, QFileDialog, QTextBrowser
)

from sherly_ui.theme import (
    C_BG_SURFACE, C_BG_CARD, C_BG_CARD_HOVER, C_BG_INPUT, C_BG_CANVAS,
    C_TEXT_PRIMARY, C_TEXT_SECONDARY, C_TEXT_MUTED, C_TEXT_DIM,
    C_ACCENT_PRIMARY, C_ACCENT_HOVER, C_ACCENT_LIGHT, C_ACCENT_SURFACE, C_ACCENT_GLOW,
    C_BORDER_SUBTLE, C_BORDER_MEDIUM, C_BORDER_ACCENT,
    C_GREEN_SUCCESS, get_ui_font, get_code_font
)


class UserMessageNode(QWidget):
    """Modern user prompt timeline card."""

    def __init__(self, prompt: str, attached_file: str | None = None, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        lay = QHBoxLayout(self)
        lay.setContentsMargins(0, 4, 0, 4)
        lay.setSpacing(12)
        lay.addStretch()

        card = QFrame()
        card.setMaximumWidth(720)
        card.setStyleSheet(f"""
            QFrame {{
                background: #141420;
                border: 1px solid rgba(255, 255, 255, 0.08);
                border-radius: 12px;
                padding: 10px 14px;
            }}
        """)
        c_lay = QVBoxLayout(card)
        c_lay.setContentsMargins(4, 2, 4, 2)
        c_lay.setSpacing(6)

        p_lbl = QLabel(prompt)
        p_lbl.setWordWrap(True)
        p_lbl.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        p_lbl.setFont(get_ui_font(10, QFont.Weight.Medium))
        p_lbl.setStyleSheet(f"color: {C_TEXT_PRIMARY}; line-height: 1.4; border: none; background: transparent;")
        c_lay.addWidget(p_lbl)

        if attached_file:
            att_pill = QLabel(f"📎 Attached: {Path(attached_file).name}")
            att_pill.setFont(get_code_font(8, QFont.Weight.Medium))
            att_pill.setStyleSheet(f"""
                background: {C_ACCENT_SURFACE};
                color: #c4b5fd;
                border: 1px solid {C_BORDER_ACCENT};
                border-radius: 4px;
                padding: 2px 8px;
            """)
            c_lay.addWidget(att_pill, 0, Qt.AlignmentFlag.AlignLeft)

        lay.addWidget(card)

        avatar = QLabel("U")
        avatar.setFixedSize(28, 28)
        avatar.setAlignment(Qt.AlignmentFlag.AlignCenter)
        avatar.setFont(get_ui_font(9, QFont.Weight.Bold))
        avatar.setStyleSheet(f"""
            background: rgba(255, 255, 255, 0.08);
            color: {C_TEXT_PRIMARY};
            border: 1px solid rgba(255, 255, 255, 0.12);
            border-radius: 14px;
        """)
        lay.addWidget(avatar, 0, Qt.AlignmentFlag.AlignTop)


class TaskStatusNode(QWidget):
    """Task status / processing indicator node."""

    def __init__(self, text: str = "Thinking...", parent: QWidget | None = None) -> None:
        super().__init__(parent)
        lay = QHBoxLayout(self)
        lay.setContentsMargins(4, 2, 4, 2)
        lay.setSpacing(10)

        indicator = QLabel("●")
        indicator.setFixedSize(24, 24)
        indicator.setAlignment(Qt.AlignmentFlag.AlignCenter)
        indicator.setFont(get_ui_font(9, QFont.Weight.Bold))
        indicator.setStyleSheet(f"""
            background: {C_ACCENT_SURFACE};
            color: #a78bfa;
            border-radius: 12px;
        """)
        lay.addWidget(indicator)

        self.t_lbl = QLabel(text)
        self.t_lbl.setFont(get_ui_font(9, QFont.Weight.Medium))
        self.t_lbl.setStyleSheet(f"color: {C_TEXT_MUTED};")
        lay.addWidget(self.t_lbl)
        lay.addStretch()

    def set_text(self, text: str) -> None:
        self.t_lbl.setText(text)


class CodeSnippetBlock(QFrame):
    """Modern dark code block with copy action."""

    def __init__(self, code_text: str, language: str = "python", parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._code_text = code_text
        self.setStyleSheet("""
            CodeSnippetBlock {
                background: #09090f;
                border: 1px solid rgba(255, 255, 255, 0.08);
                border-radius: 8px;
            }
        """)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)

        # Header bar with language tag and copy button
        hdr = QFrame()
        hdr.setStyleSheet("background: rgba(255, 255, 255, 0.03); border-bottom: 1px solid rgba(255, 255, 255, 0.06); padding: 4px 10px;")
        h_lay = QHBoxLayout(hdr)
        h_lay.setContentsMargins(6, 4, 6, 4)

        lang_lbl = QLabel(language.upper() if language else "CODE")
        lang_lbl.setFont(get_code_font(8, QFont.Weight.Bold))
        lang_lbl.setStyleSheet("color: #a78bfa; border: none; background: transparent;")
        h_lay.addWidget(lang_lbl)
        h_lay.addStretch()

        self.copy_btn = QPushButton("Copy Code")
        self.copy_btn.setFont(get_ui_font(8, QFont.Weight.Medium))
        self.copy_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.copy_btn.setFixedHeight(20)
        self.copy_btn.setStyleSheet("""
            QPushButton {
                background: rgba(255, 255, 255, 0.06);
                color: #94a3b8;
                border: 1px solid rgba(255, 255, 255, 0.08);
                border-radius: 4px;
                padding: 0px 8px;
            }
            QPushButton:hover {
                background: rgba(255, 255, 255, 0.12);
                color: #ffffff;
            }
        """)
        self.copy_btn.clicked.connect(self._copy_code)
        h_lay.addWidget(self.copy_btn)
        lay.addWidget(hdr)

        # Code content area
        code_lbl = QLabel(code_text)
        code_lbl.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        code_lbl.setFont(get_code_font(9, QFont.Weight.Normal))
        code_lbl.setStyleSheet("color: #f1f5f9; padding: 10px 12px; background: transparent; border: none;")
        lay.addWidget(code_lbl)

    def _copy_code(self) -> None:
        clipboard = QGuiApplication.clipboard()
        if clipboard:
            clipboard.setText(self._code_text)
            self.copy_btn.setText("✓ Copied")
            QTimer.singleShot(1500, lambda: self.copy_btn.setText("Copy Code"))


class AssistantMessageNode(QWidget):
    """Modern Assistant response timeline card."""

    def __init__(self, response_text: str, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._response_text = response_text
        lay = QHBoxLayout(self)
        lay.setContentsMargins(0, 4, 0, 4)
        lay.setSpacing(12)

        # Avatar
        avatar = QLabel("S")
        avatar.setFixedSize(28, 28)
        avatar.setAlignment(Qt.AlignmentFlag.AlignCenter)
        avatar.setFont(get_ui_font(10, QFont.Weight.Bold))
        avatar.setStyleSheet(f"""
            background: {C_ACCENT_PRIMARY};
            color: #ffffff;
            border-radius: 14px;
        """)
        lay.addWidget(avatar, 0, Qt.AlignmentFlag.AlignTop)

        # Content Card
        card = QFrame()
        card.setStyleSheet(f"""
            QFrame {{
                background: {C_BG_CARD};
                border: 1px solid rgba(255, 255, 255, 0.08);
                border-radius: 12px;
                padding: 12px 16px;
            }}
        """)
        c_lay = QVBoxLayout(card)
        c_lay.setContentsMargins(4, 2, 4, 2)
        c_lay.setSpacing(8)

        # Header with Copy button
        hdr = QHBoxLayout()
        hdr_lbl = QLabel("Sherly Assistant")
        hdr_lbl.setFont(get_ui_font(9, QFont.Weight.Bold))
        hdr_lbl.setStyleSheet(f"color: {C_ACCENT_LIGHT}; border: none; background: transparent;")
        hdr.addWidget(hdr_lbl)

        badge = QLabel("Copilot")
        badge.setFont(get_code_font(8, QFont.Weight.Bold))
        badge.setStyleSheet("color: #a78bfa; background: rgba(124, 58, 237, 0.15); border: 1px solid rgba(124, 58, 237, 0.3); border-radius: 4px; padding: 1px 6px;")
        hdr.addWidget(badge)
        hdr.addStretch()

        self.copy_btn = QPushButton("Copy")
        self.copy_btn.setFont(get_ui_font(8, QFont.Weight.Medium))
        self.copy_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.copy_btn.setFixedHeight(22)
        self.copy_btn.setStyleSheet("""
            QPushButton {{
                background: rgba(255, 255, 255, 0.05);
                color: #94a3b8;
                border: 1px solid rgba(255, 255, 255, 0.08);
                border-radius: 4px;
                padding: 0px 8px;
            }}
            QPushButton:hover {{
                background: rgba(255, 255, 255, 0.10);
                color: #ffffff;
            }}
        """)
        self.copy_btn.clicked.connect(self._copy_content)
        hdr.addWidget(self.copy_btn)
        c_lay.addLayout(hdr)

        # Render Text & Code Blocks
        self._render_content(c_lay, response_text)

        lay.addWidget(card, stretch=1)

    def _render_content(self, layout: QVBoxLayout, text: str) -> None:
        """Parse markdown code blocks and render clean widgets."""
        if "```" not in text:
            r_lbl = QLabel(text)
            r_lbl.setWordWrap(True)
            r_lbl.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
            r_lbl.setFont(get_ui_font(10, QFont.Weight.Normal))
            r_lbl.setStyleSheet(f"color: {C_TEXT_PRIMARY}; line-height: 1.5; border: none; background: transparent;")
            layout.addWidget(r_lbl)
            return

        parts = re.split(r"(```[\s\S]*?```)", text)
        for part in parts:
            if part.startswith("```") and part.endswith("```"):
                first_nl = part.find("\n")
                lang = part[3:first_nl].strip() if first_nl != -1 else "python"
                code = part[first_nl+1:-3].strip() if first_nl != -1 else part[3:-3].strip()
                block = CodeSnippetBlock(code, language=lang)
                layout.addWidget(block)
            elif part.strip():
                t_lbl = QLabel(part.strip())
                t_lbl.setWordWrap(True)
                t_lbl.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
                t_lbl.setFont(get_ui_font(10, QFont.Weight.Normal))
                t_lbl.setStyleSheet(f"color: {C_TEXT_PRIMARY}; line-height: 1.5; border: none; background: transparent;")
                layout.addWidget(t_lbl)

    def _copy_content(self) -> None:
        clipboard = QGuiApplication.clipboard()
        if clipboard:
            clipboard.setText(self._response_text)
            self.copy_btn.setText("✓ Copied")
            QTimer.singleShot(1500, lambda: self.copy_btn.setText("Copy"))


class AssistantComposerEdit(QTextEdit):
    """Custom QTextEdit capturing Enter key for submission."""

    return_pressed = Signal()

    def keyPressEvent(self, event: QKeyEvent) -> None:
        if event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            if event.modifiers() & Qt.KeyboardModifier.ShiftModifier:
                super().keyPressEvent(event)
            else:
                event.accept()
                self.return_pressed.emit()
        else:
            super().keyPressEvent(event)


class AssistantView(QFrame):
    """Dynamic Main Assistant View."""

    message_submitted = Signal(str)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._attached_file_path: str | None = None
        self._task_node: TaskStatusNode | None = None
        self.setObjectName("AssistantView")
        self.setStyleSheet(f"""
            #AssistantView {{
                background: {C_BG_SURFACE};
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
        self.stream_lay.setContentsMargins(28, 20, 28, 20)
        self.stream_lay.setSpacing(14)
        self.stream_lay.setAlignment(Qt.AlignmentFlag.AlignTop)

        # Welcome message
        welcome_node = AssistantMessageNode("Hello! I'm Sherly. How can I assist you with your project today?")
        self.stream_lay.addWidget(welcome_node)

        self.scroll.setWidget(self.stream_container)
        lay.addWidget(self.scroll, stretch=1)

        # Bottom Docked Composer Container
        input_container = QWidget()
        ic_lay = QVBoxLayout(input_container)
        ic_lay.setContentsMargins(28, 8, 28, 16)
        ic_lay.setSpacing(6)

        # Attached File Indicator Pill
        self.att_pill = QFrame()
        self.att_pill.hide()
        self.att_pill.setStyleSheet(f"""
            background: {C_ACCENT_SURFACE};
            border: 1px solid {C_BORDER_ACCENT};
            border-radius: 6px;
        """)
        att_lay = QHBoxLayout(self.att_pill)
        att_lay.setContentsMargins(8, 4, 8, 4)
        
        self.att_lbl = QLabel()
        self.att_lbl.setFont(get_code_font(8, QFont.Weight.Medium))
        self.att_lbl.setStyleSheet("color: #c4b5fd;")
        att_lay.addWidget(self.att_lbl)
        
        att_close = QPushButton("✕")
        att_close.setFixedSize(16, 16)
        att_close.setCursor(Qt.CursorShape.PointingHandCursor)
        att_close.setStyleSheet("background: transparent; color: #a78bfa; border: none; font-size: 10px;")
        att_close.clicked.connect(self._clear_attachment)
        att_lay.addWidget(att_close)
        att_lay.addStretch()
        ic_lay.addWidget(self.att_pill, 0, Qt.AlignmentFlag.AlignLeft)

        # Composer bar
        bar = QFrame()
        bar.setStyleSheet(f"""
            QFrame {{
                background: {C_BG_INPUT};
                border: 1px solid rgba(255, 255, 255, 0.12);
                border-radius: 10px;
            }}
            QFrame:focus-within {{
                border: 1px solid {C_ACCENT_PRIMARY};
            }}
        """)
        b_lay = QHBoxLayout(bar)
        b_lay.setContentsMargins(10, 6, 10, 6)
        b_lay.setSpacing(8)

        attach_btn = QPushButton("📎")
        attach_btn.setFont(get_ui_font(11, QFont.Weight.Normal))
        attach_btn.setFixedSize(28, 28)
        attach_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        attach_btn.setToolTip("Attach File")
        attach_btn.setStyleSheet("""
            QPushButton {
                background: rgba(255, 255, 255, 0.05);
                color: #94a3b8;
                border: none;
                border-radius: 6px;
            }
            QPushButton:hover {
                background: rgba(255, 255, 255, 0.10);
                color: #ffffff;
            }
        """)
        attach_btn.clicked.connect(self._browse_file)
        b_lay.addWidget(attach_btn)

        self.input_edit = AssistantComposerEdit()
        self.input_edit.setFont(get_ui_font(10, QFont.Weight.Normal))
        self.input_edit.setPlaceholderText("Ask Sherly anything (Enter to send, Shift+Enter for newline)...")
        self.input_edit.setFixedHeight(36)
        self.input_edit.setFrameShape(QFrame.Shape.NoFrame)
        self.input_edit.setStyleSheet(f"background: transparent; color: {C_TEXT_PRIMARY}; border: none;")
        self.input_edit.return_pressed.connect(self._submit)
        b_lay.addWidget(self.input_edit, stretch=1)

        send_btn = QPushButton("↑")
        send_btn.setFont(get_ui_font(12, QFont.Weight.Bold))
        send_btn.setFixedSize(30, 30)
        send_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        send_btn.setToolTip("Send Prompt")
        send_btn.setStyleSheet(f"""
            QPushButton {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 {C_ACCENT_PRIMARY}, stop:1 #9333ea);
                color: #ffffff;
                border: none;
                border-radius: 8px;
            }}
            QPushButton:hover {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 {C_ACCENT_HOVER}, stop:1 #a855f7);
            }}
        """)
        send_btn.clicked.connect(self._submit)
        b_lay.addWidget(send_btn)

        ic_lay.addWidget(bar)
        lay.addWidget(input_container)

    def _browse_file(self) -> None:
        file_path, _ = QFileDialog.getOpenFileName(self, "Attach File to Assistant", str(Path.cwd()))
        if file_path:
            self._attached_file_path = file_path
            self.att_lbl.setText(f"Attached: {Path(file_path).name}")
            self.att_pill.show()

    def _clear_attachment(self) -> None:
        self._attached_file_path = None
        self.att_pill.hide()

    def _submit(self) -> None:
        text = self.input_edit.toPlainText().strip()
        if not text:
            return

        self.input_edit.clear()
        att = self._attached_file_path
        self._clear_attachment()

        # Add user prompt node
        u_node = UserMessageNode(text, attached_file=att)
        self.stream_lay.addWidget(u_node)

        # Show task status node
        self._task_node = TaskStatusNode("Thinking...")
        self.stream_lay.addWidget(self._task_node)

        self._scroll_to_bottom()
        full_prompt = f"File: {att}\n{text}" if att else text
        self.message_submitted.emit(full_prompt)

    def add_response(self, text: str, response: str) -> None:
        """Called when AI worker completes response."""
        if self._task_node:
            self.stream_lay.removeWidget(self._task_node)
            self._task_node.deleteLater()
            self._task_node = None

        a_node = AssistantMessageNode(response)
        self.stream_lay.addWidget(a_node)
        self._scroll_to_bottom()

    def _scroll_to_bottom(self) -> None:
        sb = self.scroll.verticalScrollBar()
        sb.setValue(sb.maximum())
