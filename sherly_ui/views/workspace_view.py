"""
DEVELOPER WORKSPACE VIEW — sherly_ui/views/workspace_view.py
Dynamic Developer Workspace:
  - Real project code file loading & editing
  - Real git diff / AI patch diff viewer with functional Accept/Reject actions
  - Interactive Terminal executing real subprocesses with streaming output
  - Real-time Git branch & system status bar
"""

from __future__ import annotations

import os
import sys
import subprocess
from pathlib import Path
from PySide6.QtCore import Qt, Signal, QProcess, QTimer
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QFrame, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QTextEdit,
    QLineEdit, QWidget, QScrollArea, QSplitter
)

from sherly_ui.theme import (
    C_BG_SURFACE, C_BG_CARD, C_BG_CANVAS, C_BG_INPUT,
    C_TEXT_PRIMARY, C_TEXT_SECONDARY, C_TEXT_MUTED, C_TEXT_DIM,
    C_ACCENT_PRIMARY, C_ACCENT_HOVER, C_ACCENT_SURFACE,
    C_GREEN_SUCCESS, C_GREEN_BG, C_RED_DANGER, C_RED_BG,
    C_BORDER_SUBTLE, C_BORDER_MEDIUM, C_BORDER_ACCENT,
    FONT_FAMILY_UI, FONT_FAMILY_CODE, get_ui_font, get_code_font
)
import config_manager


class DynamicDiffEditorWidget(QFrame):
    """Dynamic Code & Diff Viewer Widget."""

    accepted = Signal()
    rejected = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("DiffEditor")
        self.setStyleSheet(f"""
            #DiffEditor {{
                background: {C_BG_CANVAS};
                border: 1px solid {C_BORDER_MEDIUM};
                border-radius: 8px;
            }}
        """)
        self._current_filepath: Path | None = None
        self._pending_diff_content: str | None = None
        self._setup_ui()

    def _setup_ui(self) -> None:
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)

        # Header Bar
        self.hdr = QFrame()
        self.hdr.setStyleSheet(f"""
            background: rgba(255, 255, 255, 0.02);
            border-bottom: 1px solid {C_BORDER_SUBTLE};
            padding: 4px 12px;
        """)
        h_lay = QHBoxLayout(self.hdr)
        h_lay.setContentsMargins(12, 6, 12, 6)
        h_lay.setSpacing(8)

        self.filename_lbl = QLabel("No File Selected")
        self.filename_lbl.setFont(get_code_font(9, QFont.Weight.DemiBold))
        self.filename_lbl.setStyleSheet(f"color: {C_TEXT_PRIMARY};")
        h_lay.addWidget(self.filename_lbl)
        h_lay.addStretch()

        self.accept_btn = QPushButton("Accept Patch (Ctrl+Enter)")
        self.accept_btn.setFont(get_ui_font(8, QFont.Weight.Bold))
        self.accept_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.accept_btn.setStyleSheet(f"""
            QPushButton {{
                background: {C_GREEN_BG};
                color: {C_GREEN_SUCCESS};
                border: 1px solid rgba(16, 185, 129, 0.40);
                border-radius: 4px;
                padding: 4px 12px;
            }}
            QPushButton:hover {{
                background: rgba(16, 185, 129, 0.25);
            }}
        """)
        self.accept_btn.clicked.connect(self._on_accept)

        self.reject_btn = QPushButton("Reject (Esc)")
        self.reject_btn.setFont(get_ui_font(8, QFont.Weight.Bold))
        self.reject_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.reject_btn.setStyleSheet(f"""
            QPushButton {{
                background: {C_RED_BG};
                color: {C_RED_DANGER};
                border: 1px solid rgba(244, 63, 94, 0.30);
                border-radius: 4px;
                padding: 4px 12px;
            }}
            QPushButton:hover {{
                background: rgba(244, 63, 94, 0.22);
            }}
        """)
        self.reject_btn.clicked.connect(self._on_reject)

        self.accept_btn.hide()
        self.reject_btn.hide()

        h_lay.addWidget(self.accept_btn)
        h_lay.addWidget(self.reject_btn)
        lay.addWidget(self.hdr)

        # Code Editor / Viewer Text Area
        self.editor = QTextEdit()
        self.editor.setFrameShape(QFrame.Shape.NoFrame)
        self.editor.setFont(get_code_font(9, QFont.Weight.Normal))
        self.editor.setStyleSheet(f"""
            QTextEdit {{
                background: transparent;
                color: {C_TEXT_PRIMARY};
                font-family: {FONT_FAMILY_CODE};
                padding: 10px 14px;
                line-height: 1.45;
            }}
        """)
        lay.addWidget(self.editor, stretch=1)

    def load_file(self, filepath: str) -> None:
        """Load real file content from disk."""
        path = Path(filepath)
        self._current_filepath = path
        self.filename_lbl.setText(path.name)
        self.accept_btn.hide()
        self.reject_btn.hide()

        try:
            content = path.read_text(encoding="utf-8", errors="replace")
            lines = content.splitlines()
            html_lines = []
            for idx, line in enumerate(lines, 1):
                escaped = line.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace(" ", "&nbsp;")
                html_lines.append(f"<span style='color:#52525b; width:36px; display:inline-block;'>{idx:>3}</span> &nbsp; {escaped}")
            self.editor.setHtml("<br>".join(html_lines))
        except Exception as exc:
            self.editor.setPlainText(f"Error loading file: {exc}")

    def show_diff(self, filename: str, old_code: str, new_code: str) -> None:
        """Display diff viewer mode with working Accept/Reject buttons."""
        self.filename_lbl.setText(f"Diff: {filename}")
        self._pending_diff_content = new_code
        self.accept_btn.show()
        self.reject_btn.show()

        html_rows = []
        old_lines = old_code.splitlines()
        new_lines = new_code.splitlines()

        for idx, line in enumerate(old_lines, 1):
            escaped = line.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace(" ", "&nbsp;")
            html_rows.append(f"<div style='background:{C_RED_BG}; color:#fb7185; padding: 2px 4px;'><span style='color:#71717a;'>{idx:>3} -</span> &nbsp; {escaped}</div>")

        for idx, line in enumerate(new_lines, 1):
            escaped = line.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace(" ", "&nbsp;")
            html_rows.append(f"<div style='background:{C_GREEN_BG}; color:#34d399; font-weight:bold; padding: 2px 4px;'><span style='color:#71717a;'>{idx:>3} +</span> &nbsp; {escaped}</div>")

        self.editor.setHtml("".join(html_rows))

    def _on_accept(self) -> None:
        if self._current_filepath and self._pending_diff_content is not None:
            try:
                self._current_filepath.write_text(self._pending_diff_content, encoding="utf-8")
                self.load_file(str(self._current_filepath))
            except Exception as exc:
                print(f"Failed to write file: {exc}")
        self.accepted.emit()

    def _on_reject(self) -> None:
        if self._current_filepath:
            self.load_file(str(self._current_filepath))
        self.rejected.emit()


class DynamicTerminalWidget(QFrame):
    """Interactive Integrated Terminal Panel executing real processes."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setFixedHeight(180)
        self.setObjectName("TerminalPanel")
        self.setStyleSheet(f"""
            #TerminalPanel {{
                background: {C_BG_CANVAS};
                border-top: 1px solid {C_BORDER_MEDIUM};
            }}
        """)
        self._process: QProcess | None = None
        self._setup_ui()

    def _setup_ui(self) -> None:
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)

        # Tab bar
        tabs_hdr = QFrame()
        tabs_hdr.setStyleSheet(f"""
            background: rgba(255, 255, 255, 0.02);
            border-bottom: 1px solid {C_BORDER_SUBTLE};
        """)
        t_lay = QHBoxLayout(tabs_hdr)
        t_lay.setContentsMargins(14, 4, 14, 4)

        t1 = QLabel("TERMINAL")
        t1.setFont(get_code_font(8, QFont.Weight.Bold))
        t1.setStyleSheet(f"color: #c4b5fd; border-bottom: 2px solid {C_ACCENT_PRIMARY}; padding-bottom: 2px;")
        t_lay.addWidget(t1)
        t_lay.addStretch()

        clear_btn = QPushButton("Clear")
        clear_btn.setFont(get_ui_font(8, QFont.Weight.Medium))
        clear_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        clear_btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                color: {C_TEXT_MUTED};
                border: none;
            }}
            QPushButton:hover {{
                color: {C_TEXT_PRIMARY};
            }}
        """)
        clear_btn.clicked.connect(self.clear_output)
        t_lay.addWidget(clear_btn)

        lay.addWidget(tabs_hdr)

        # Output text
        self.output_edit = QTextEdit()
        self.output_edit.setReadOnly(True)
        self.output_edit.setFrameShape(QFrame.Shape.NoFrame)
        self.output_edit.setFont(get_code_font(9, QFont.Weight.Normal))
        self.output_edit.setStyleSheet(f"""
            QTextEdit {{
                background: transparent;
                color: #e5e7eb;
                font-family: {FONT_FAMILY_CODE};
                padding: 6px 14px;
            }}
        """)
        self.output_edit.append("<span style='color:#a78bfa;'>Sherly Interactive Terminal Ready.</span>")
        lay.addWidget(self.output_edit, stretch=1)

        # Input Prompt Bar
        prompt_bar = QFrame()
        prompt_bar.setStyleSheet(f"""
            background: rgba(255, 255, 255, 0.02);
            border-top: 1px solid {C_BORDER_SUBTLE};
        """)
        p_lay = QHBoxLayout(prompt_bar)
        p_lay.setContentsMargins(14, 4, 14, 4)
        p_lay.setSpacing(6)

        prompt_lbl = QLabel("➔ $")
        prompt_lbl.setFont(get_code_font(9, QFont.Weight.Bold))
        prompt_lbl.setStyleSheet("color: #38bdf8;")
        p_lay.addWidget(prompt_lbl)

        self.cmd_input = QLineEdit()
        self.cmd_input.setFont(get_code_font(9, QFont.Weight.Normal))
        self.cmd_input.setPlaceholderText("Type a command (e.g. python main.py)...")
        self.cmd_input.setStyleSheet(f"""
            QLineEdit {{
                background: transparent;
                color: {C_TEXT_PRIMARY};
                border: none;
            }}
        """)
        self.cmd_input.returnPressed.connect(self._run_typed_command)
        p_lay.addWidget(self.cmd_input, stretch=1)

        lay.addWidget(prompt_bar)

    def run_cmd(self, command_str: str) -> None:
        """Run a command asynchronously in terminal."""
        self.output_edit.append(f"<span style='color:#38bdf8;'>➔ {command_str}</span>")
        self._process = QProcess(self)
        self._process.setProcessChannelMode(QProcess.ProcessChannelMode.MergedChannels)
        self._process.readyReadStandardOutput.connect(self._on_stdout)
        self._process.finished.connect(self._on_finished)
        self._process.start("cmd.exe" if sys.platform == "win32" else "bash", ["/c" if sys.platform == "win32" else "-c", command_str])

    def _run_typed_command(self) -> None:
        cmd = self.cmd_input.text().strip()
        if cmd:
            self.cmd_input.clear()
            self.run_cmd(cmd)

    def _on_stdout(self) -> None:
        if self._process:
            data = self._process.readAllStandardOutput().data().decode("utf-8", errors="replace")
            self.output_edit.insertPlainText(data)
            sb = self.output_edit.verticalScrollBar()
            sb.setValue(sb.maximum())

    def _on_finished(self, exit_code: int, exit_status) -> None:
        color = "#10b981" if exit_code == 0 else "#f43f5e"
        self.output_edit.append(f"<span style='color:{color};'>[Process exited with code {exit_code}]</span>\n")

    def clear_output(self) -> None:
        self.output_edit.clear()


class WorkspaceView(QFrame):
    """Dynamic Developer Workspace view."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("WorkspaceView")
        self.setStyleSheet(f"""
            #WorkspaceView {{
                background: {C_BG_SURFACE};
            }}
        """)
        self._setup_ui()
        self.update_status_bar()

    def _setup_ui(self) -> None:
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)

        # Main Splitter: Editor on top, Terminal on bottom
        splitter = QSplitter(Qt.Orientation.Vertical)
        splitter.setChildrenCollapsible(False)

        editor_area = QWidget()
        ea_lay = QVBoxLayout(editor_area)
        ea_lay.setContentsMargins(14, 10, 14, 10)
        ea_lay.setSpacing(6)

        # Tab bar
        self.tab_bar_lay = QHBoxLayout()
        self.tab_bar_lay.setSpacing(6)
        ea_lay.addLayout(self.tab_bar_lay)

        # Code & Diff Editor
        self.diff_editor = DynamicDiffEditorWidget()
        ea_lay.addWidget(self.diff_editor, stretch=1)

        splitter.addWidget(editor_area)

        # Terminal Panel
        self.terminal = DynamicTerminalWidget()
        splitter.addWidget(self.terminal)

        lay.addWidget(splitter, stretch=1)

        # Footer Status Bar
        self.footer = QFrame()
        self.footer.setFixedHeight(24)
        self.footer.setStyleSheet(f"""
            background: {C_BG_CANVAS};
            border-top: 1px solid {C_BORDER_SUBTLE};
        """)
        f_lay = QHBoxLayout(self.footer)
        f_lay.setContentsMargins(12, 0, 12, 0)

        self.git_lbl = QLabel("git: main")
        self.git_lbl.setFont(get_code_font(8, QFont.Weight.Medium))
        self.git_lbl.setStyleSheet(f"color: {C_TEXT_MUTED};")
        f_lay.addWidget(self.git_lbl)
        f_lay.addStretch()

        self.status_lbl = QLabel(f"UTF-8   Python {sys.version.split()[0]}   ● Sherly Active")
        self.status_lbl.setFont(get_code_font(8, QFont.Weight.Normal))
        self.status_lbl.setStyleSheet(f"color: {C_TEXT_MUTED};")
        f_lay.addWidget(self.status_lbl)

        lay.addWidget(self.footer)

        # Load initial file if available
        initial_file = Path("main.py")
        if initial_file.exists():
            self.load_file(str(initial_file))

    def load_file(self, filepath: str) -> None:
        """Load a real project file into the editor."""
        self.diff_editor.load_file(filepath)
        path = Path(filepath)

        # Rebuild Tab Bar
        while self.tab_bar_lay.count():
            item = self.tab_bar_lay.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        tab_btn = QPushButton(f"{path.name}  ✕")
        tab_btn.setFont(get_code_font(9, QFont.Weight.Medium))
        tab_btn.setStyleSheet(f"""
            QPushButton {{
                background: {C_BG_CANVAS};
                color: {C_TEXT_PRIMARY};
                border: 1px solid {C_BORDER_MEDIUM};
                border-bottom: none;
                border-radius: 6px 6px 0 0;
                padding: 5px 12px;
            }}
        """)
        self.tab_bar_lay.addWidget(tab_btn)
        self.tab_bar_lay.addStretch()

    def run_main_project(self) -> None:
        """Execute main.py in the interactive terminal."""
        self.terminal.run_cmd("python main.py")

    def update_status_bar(self) -> None:
        """Update branch and model status dynamically."""
        try:
            res = subprocess.run(["git", "branch", "--show-current"], capture_output=True, text=True, timeout=2)
            branch = res.stdout.strip() or "main"
            self.git_lbl.setText(f"git: {branch}")
        except Exception:
            self.git_lbl.setText("git: main")

        curr_model = config_manager.get_current_model() or "Active"
        self.status_lbl.setText(f"UTF-8   Python {sys.version.split()[0]}   ● Sherly [{curr_model}]")

