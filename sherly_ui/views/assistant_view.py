"""
MAIN ASSISTANT VIEW — sherly_ui/views/assistant_view.py
Ultra-sleek ChatGPT / Cursor style AI assistant view:
  - Clean natural timeline stream with compact user bubbles and elegant assistant responses
  - High-contrast code block formatting and copy to clipboard
  - Floating island composer with file attachment, mic trigger, and circular send button
"""

from __future__ import annotations

import re
from pathlib import Path
from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtGui import QFont, QGuiApplication, QKeyEvent
from PySide6.QtWidgets import (
    QFrame, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QTextEdit,
    QScrollArea, QWidget, QFileDialog
)

from sherly_ui.theme import (
    C_BG_SURFACE, C_BG_CARD, C_BG_INPUT, C_BG_CANVAS,
    C_TEXT_PRIMARY, C_TEXT_SECONDARY, C_TEXT_MUTED, C_TEXT_DIM,
    C_ACCENT_PRIMARY, C_ACCENT_HOVER, C_ACCENT_LIGHT,
    C_BORDER_SUBTLE, C_BORDER_MEDIUM, C_BORDER_ACCENT,
    C_GREEN_SUCCESS, get_ui_font, get_code_font
)


class UserMessageNode(QWidget):
    """Sleek user prompt bubble aligned to the right."""

    def __init__(self, prompt: str, attached_file: str | None = None, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        lay = QHBoxLayout(self)
        lay.setContentsMargins(0, 4, 0, 4)
        lay.setSpacing(10)
        lay.addStretch()

        card = QFrame()
        card.setMaximumWidth(680)
        card.setStyleSheet("""
            QFrame {
                background: #27272a;
                border: 1px solid rgba(255, 255, 255, 0.06);
                border-radius: 14px;
                padding: 8px 14px;
            }
        """)
        c_lay = QVBoxLayout(card)
        c_lay.setContentsMargins(2, 2, 2, 2)
        c_lay.setSpacing(4)

        p_lbl = QLabel(prompt)
        p_lbl.setWordWrap(True)
        p_lbl.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        p_lbl.setFont(get_ui_font(9, QFont.Weight.Normal))
        p_lbl.setStyleSheet(f"color: {C_TEXT_PRIMARY}; line-height: 1.4; border: none; background: transparent;")
        c_lay.addWidget(p_lbl)

        if attached_file:
            att_pill = QLabel(f"📎 {Path(attached_file).name}")
            att_pill.setFont(get_code_font(8, QFont.Weight.Medium))
            att_pill.setStyleSheet("""
                background: #18181b;
                color: #d4d4d8;
                border: 1px solid rgba(255, 255, 255, 0.08);
                border-radius: 4px;
                padding: 2px 6px;
            """)
            c_lay.addWidget(att_pill, 0, Qt.AlignmentFlag.AlignLeft)

        lay.addWidget(card)


class TaskStatusNode(QWidget):
    """Clean thinking indicator node."""

    def __init__(self, text: str = "Thinking...", parent: QWidget | None = None) -> None:
        super().__init__(parent)
        lay = QHBoxLayout(self)
        lay.setContentsMargins(0, 4, 0, 4)
        lay.setSpacing(8)

        indicator = QLabel("S")
        indicator.setFixedSize(22, 22)
        indicator.setAlignment(Qt.AlignmentFlag.AlignCenter)
        indicator.setFont(get_ui_font(8, QFont.Weight.Bold))
        indicator.setStyleSheet(f"""
            background: {C_ACCENT_PRIMARY};
            color: #ffffff;
            border-radius: 4px;
        """)
        lay.addWidget(indicator)

        self.t_lbl = QLabel(text)
        self.t_lbl.setFont(get_ui_font(9, QFont.Weight.Medium))
        self.t_lbl.setStyleSheet("color: #a1a1aa;")
        lay.addWidget(self.t_lbl)
        lay.addStretch()

    def set_text(self, text: str) -> None:
        self.t_lbl.setText(text)


class CodeSnippetBlock(QFrame):
    """Sleek dark code block with copy action."""

    def __init__(self, code_text: str, language: str = "python", parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._code_text = code_text
        self.setStyleSheet("""
            CodeSnippetBlock {
                background: #09090b;
                border: 1px solid rgba(255, 255, 255, 0.08);
                border-radius: 8px;
            }
        """)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)

        # Header bar with language tag and copy button
        hdr = QFrame()
        hdr.setStyleSheet("background: #141418; border-bottom: 1px solid rgba(255, 255, 255, 0.06); padding: 4px 8px;")
        h_lay = QHBoxLayout(hdr)
        h_lay.setContentsMargins(6, 3, 6, 3)

        lang_lbl = QLabel(language.upper() if language else "CODE")
        lang_lbl.setFont(get_code_font(8, QFont.Weight.Bold))
        lang_lbl.setStyleSheet("color: #a1a1aa; border: none; background: transparent;")
        h_lay.addWidget(lang_lbl)
        h_lay.addStretch()

        self.copy_btn = QPushButton("Copy")
        self.copy_btn.setFont(get_ui_font(8, QFont.Weight.Medium))
        self.copy_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.copy_btn.setFixedHeight(20)
        self.copy_btn.setStyleSheet("""
            QPushButton {
                background: #27272a;
                color: #d4d4d8;
                border: 1px solid rgba(255, 255, 255, 0.06);
                border-radius: 4px;
                padding: 0px 8px;
            }
            QPushButton:hover {
                background: #3f3f46;
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
        code_lbl.setStyleSheet("color: #f4f4f5; padding: 10px 12px; background: transparent; border: none;")
        lay.addWidget(code_lbl)

    def _copy_code(self) -> None:
        clipboard = QGuiApplication.clipboard()
        if clipboard:
            clipboard.setText(self._code_text)
            self.copy_btn.setText("✓ Copied")
            QTimer.singleShot(1500, lambda: self.copy_btn.setText("Copy"))


class AssistantMessageNode(QWidget):
    """Natural flow Assistant response node."""

    def __init__(self, response_text: str, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._response_text = response_text
        lay = QHBoxLayout(self)
        lay.setContentsMargins(0, 4, 0, 4)
        lay.setSpacing(10)

        # Avatar
        avatar = QLabel("S")
        avatar.setFixedSize(22, 22)
        avatar.setAlignment(Qt.AlignmentFlag.AlignCenter)
        avatar.setFont(get_ui_font(8, QFont.Weight.Bold))
        avatar.setStyleSheet(f"""
            background: {C_ACCENT_PRIMARY};
            color: #ffffff;
            border-radius: 4px;
        """)
        lay.addWidget(avatar, 0, Qt.AlignmentFlag.AlignTop)

        # Content Stream
        content_container = QWidget()
        c_lay = QVBoxLayout(content_container)
        c_lay.setContentsMargins(0, 0, 0, 0)
        c_lay.setSpacing(6)

        # Render Text & Code Blocks
        self._render_content(c_lay, response_text)

        # Bottom subtle action row
        act_row = QHBoxLayout()
        act_row.setSpacing(6)
        
        self.copy_btn = QPushButton("Copy")
        self.copy_btn.setFont(get_ui_font(8, QFont.Weight.Normal))
        self.copy_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.copy_btn.setFixedHeight(18)
        self.copy_btn.setStyleSheet("""
            QPushButton {
                background: transparent;
                color: #71717a;
                border: none;
                padding: 0px 4px;
            }
            QPushButton:hover {
                color: #d4d4d8;
            }
        """)
        self.copy_btn.clicked.connect(self._copy_content)
        act_row.addWidget(self.copy_btn)
        act_row.addStretch()
        c_lay.addLayout(act_row)

        lay.addWidget(content_container, stretch=1)

    def _render_content(self, layout: QVBoxLayout, text: str) -> None:
        """Parse markdown code blocks and render clean widgets."""
        if "```" not in text:
            r_lbl = QLabel(text)
            r_lbl.setWordWrap(True)
            r_lbl.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
            r_lbl.setFont(get_ui_font(9, QFont.Weight.Normal))
            r_lbl.setStyleSheet("color: #e4e4e7; line-height: 1.5; border: none; background: transparent;")
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
                t_lbl.setFont(get_ui_font(9, QFont.Weight.Normal))
                t_lbl.setStyleSheet("color: #e4e4e7; line-height: 1.5; border: none; background: transparent;")
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
                background: {C_BG_CANVAS};
            }}
        """)
        self._setup_ui()

    def _setup_ui(self) -> None:
        main_lay = QVBoxLayout(self)
        main_lay.setContentsMargins(0, 0, 0, 0)
        main_lay.setSpacing(0)

        # ── Scrollable Chat Timeline Stream ───────────────────────────────────
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setFrameShape(QFrame.Shape.NoFrame)
        self.scroll.setStyleSheet("background: transparent; border: none;")

        self.timeline_widget = QWidget()
        self.timeline_widget.setStyleSheet("background: transparent;")
        self.timeline_lay = QVBoxLayout(self.timeline_widget)
        self.timeline_lay.setContentsMargins(20, 16, 20, 16)
        self.timeline_lay.setSpacing(14)
        self.timeline_lay.addStretch()

        self.scroll.setWidget(self.timeline_widget)
        main_lay.addWidget(self.scroll, stretch=1)

        # ── Docked Floating Island Composer ──────────────────────────────────
        composer_container = QWidget()
        composer_container.setStyleSheet("background: transparent;")
        c_outer_lay = QVBoxLayout(composer_container)
        c_outer_lay.setContentsMargins(20, 4, 20, 14)

        # Attachment Banner
        self.att_banner = QFrame()
        self.att_banner.setStyleSheet("""
            QFrame {
                background: #18181b;
                border: 1px solid rgba(255, 255, 255, 0.08);
                border-radius: 6px;
                padding: 2px 8px;
            }
        """)
        att_lay = QHBoxLayout(self.att_banner)
        att_lay.setContentsMargins(4, 2, 4, 2)
        att_lay.setSpacing(6)

        self.att_label = QLabel("")
        self.att_label.setFont(get_code_font(8, QFont.Weight.Medium))
        self.att_label.setStyleSheet("color: #d4d4d8;")
        att_lay.addWidget(self.att_label)
        att_lay.addStretch()

        att_remove_btn = QPushButton("✕")
        att_remove_btn.setFont(get_ui_font(8, QFont.Weight.Bold))
        att_remove_btn.setFixedSize(16, 16)
        att_remove_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        att_remove_btn.setStyleSheet("""
            QPushButton {
                background: transparent;
                color: #71717a;
                border: none;
            }
            QPushButton:hover {
                color: #ef4444;
            }
        """)
        att_remove_btn.clicked.connect(self._clear_attachment)
        att_lay.addWidget(att_remove_btn)
        self.att_banner.hide()
        c_outer_lay.addWidget(self.att_banner)

        # Composer Box
        self.composer_box = QFrame()
        self.composer_box.setStyleSheet("""
            QFrame {
                background: #18181b;
                border: 1px solid rgba(255, 255, 255, 0.08);
                border-radius: 12px;
            }
            QFrame:focus-within {
                border: 1px solid rgba(255, 255, 255, 0.16);
            }
        """)
        comp_lay = QHBoxLayout(self.composer_box)
        comp_lay.setContentsMargins(8, 6, 8, 6)
        comp_lay.setSpacing(6)

        # File Attach Button
        self.attach_btn = QPushButton("📎")
        self.attach_btn.setFont(get_ui_font(10, QFont.Weight.Normal))
        self.attach_btn.setFixedSize(26, 26)
        self.attach_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.attach_btn.setToolTip("Attach File")
        self.attach_btn.setStyleSheet("""
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
        self.attach_btn.clicked.connect(self._open_file_attachment)
        comp_lay.addWidget(self.attach_btn, 0, Qt.AlignmentFlag.AlignBottom)

        # Text Input
        self.input_edit = AssistantComposerEdit()
        self.input_edit.setPlaceholderText("Ask Sherly anything (Enter to send, Shift+Enter for newline)...")
        self.input_edit.setFont(get_ui_font(9, QFont.Weight.Normal))
        self.input_edit.setFixedHeight(34)
        self.input_edit.setStyleSheet(f"""
            QTextEdit {{
                background: transparent;
                color: {C_TEXT_PRIMARY};
                border: none;
                padding: 6px 4px;
            }}
        """)
        self.input_edit.return_pressed.connect(self._handle_submit)
        comp_lay.addWidget(self.input_edit, stretch=1)

        # Voice Input Trigger
        self.voice_btn = QPushButton("🎙")
        self.voice_btn.setFont(get_ui_font(10, QFont.Weight.Normal))
        self.voice_btn.setFixedSize(26, 26)
        self.voice_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.voice_btn.setToolTip("Voice Input (Ctrl+Shift+L)")
        self.voice_btn.setStyleSheet("""
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
        comp_lay.addWidget(self.voice_btn, 0, Qt.AlignmentFlag.AlignBottom)

        # Send Button
        self.send_btn = QPushButton("↑")
        self.send_btn.setFont(get_ui_font(10, QFont.Weight.Bold))
        self.send_btn.setFixedSize(26, 26)
        self.send_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.send_btn.setToolTip("Send Prompt (Enter)")
        self.send_btn.setStyleSheet("""
            QPushButton {
                background: #f4f4f5;
                color: #18181b;
                border: none;
                border-radius: 13px;
            }
            QPushButton:hover {
                background: #ffffff;
            }
            QPushButton:pressed {
                background: #d4d4d8;
            }
        """)
        self.send_btn.clicked.connect(self._handle_submit)
        comp_lay.addWidget(self.send_btn, 0, Qt.AlignmentFlag.AlignBottom)

        c_outer_lay.addWidget(self.composer_box)
        main_lay.addWidget(composer_container)

    def _open_file_attachment(self) -> None:
        file_path, _ = QFileDialog.getOpenFileName(self, "Attach File to Context", str(Path.cwd()))
        if file_path:
            self._attached_file_path = file_path
            self.att_label.setText(f"Attached: {Path(file_path).name}")
            self.att_banner.show()

    def _clear_attachment(self) -> None:
        self._attached_file_path = None
        self.att_label.setText("")
        self.att_banner.hide()

    def _handle_submit(self) -> None:
        text = self.input_edit.toPlainText().strip()
        if not text:
            return

        self.add_user_message(text, self._attached_file_path)
        self.input_edit.clear()
        self._clear_attachment()
        self.show_task_status("Thinking...")
        self.message_submitted.emit(text)

    def add_user_message(self, prompt: str, attached_file: str | None = None) -> None:
        node = UserMessageNode(prompt, attached_file, self.timeline_widget)
        self.timeline_lay.insertWidget(self.timeline_lay.count() - 1, node)
        self._scroll_to_bottom()

    def add_assistant_message(self, response: str) -> None:
        self.hide_task_status()
        node = AssistantMessageNode(response, self.timeline_widget)
        self.timeline_lay.insertWidget(self.timeline_lay.count() - 1, node)
        self._scroll_to_bottom()

    def add_response(self, prompt: str, response: str) -> None:
        self.add_user_message(prompt)
        self.add_assistant_message(response)

    def show_task_status(self, text: str = "Thinking...") -> None:
        if self._task_node is None:
            self._task_node = TaskStatusNode(text, self.timeline_widget)
            self.timeline_lay.insertWidget(self.timeline_lay.count() - 1, self._task_node)
        else:
            self._task_node.set_text(text)
            self._task_node.show()
        self._scroll_to_bottom()

    def hide_task_status(self) -> None:
        if self._task_node:
            self._task_node.hide()

    def _scroll_to_bottom(self) -> None:
        QTimer.singleShot(50, lambda: self.scroll.verticalScrollBar().setValue(
            self.scroll.verticalScrollBar().maximum()
        ))
