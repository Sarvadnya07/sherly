"""
DEVELOPER WORKSPACE VIEW — sherly_ui/views/workspace_view.py
Dynamic Developer Workspace:
  - Real project code file loading & editing
  - Real git diff / AI patch diff viewer with functional Accept/Reject actions
  - Dynamic AI performance insight card
  - Interactive Terminal executing real sub-processes with streaming output
  - Real-time Git branch & system status bar
"""

from __future__ import annotations

import os
import sys
import subprocess
from pathlib import Path
from PySide6.QtCore import Qt, Signal, QProcess, QTimer
from PySide6.QtWidgets import (
    QFrame, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QTextEdit,
    QLineEdit, QWidget, QScrollArea, QSplitter
)

from sherly_ui.theme import (
    C_BG_PANEL, C_BG_CARD, C_TEXT_PRIMARY, C_TEXT_MUTED, C_TEXT_DIM,
    C_PURPLE_MAIN, C_GREEN_SUCCESS, C_RED_DANGER, C_BORDER_SUBTLE
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
                background: #0d0d15;
                border: 1px solid {C_BORDER_SUBTLE};
                border-radius: 12px;
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
        self.hdr.setStyleSheet("background: rgba(255,255,255,0.02); border-bottom: 1px solid rgba(255,255,255,0.06); padding: 6px 16px;")
        h_lay = QHBoxLayout(self.hdr)
        h_lay.setContentsMargins(16, 6, 16, 6)

        self.filename_lbl = QLabel("No File Selected")
        self.filename_lbl.setStyleSheet(f"color: {C_TEXT_PRIMARY}; font-size: 12px; font-weight: 700;")
        h_lay.addWidget(self.filename_lbl)
        h_lay.addStretch()

        self.accept_btn = QPushButton("✓ Accept")
        self.accept_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.accept_btn.setStyleSheet("""
            QPushButton {
                background: rgba(16, 185, 129, 0.15); color: #10b981; border: 1px solid rgba(16, 185, 129, 0.4);
                border-radius: 8px; padding: 4px 14px; font-size: 11px; font-weight: 700;
            }
            QPushButton:hover { background: rgba(16, 185, 129, 0.28); }
        """)
        self.accept_btn.clicked.connect(self._on_accept)

        self.reject_btn = QPushButton("✕ Reject")
        self.reject_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.reject_btn.setStyleSheet("""
            QPushButton {
                background: rgba(255, 255, 255, 0.05); color: #888; border: 1px solid rgba(255, 255, 255, 0.1);
                border-radius: 8px; padding: 4px 14px; font-size: 11px; font-weight: 700;
            }
            QPushButton:hover { background: rgba(239, 68, 68, 0.2); color: #ef4444; }
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
        self.editor.setStyleSheet("""
            QTextEdit {
                background: transparent;
                color: #e5e7eb;
                font-family: 'Consolas', 'Courier New', monospace;
                font-size: 12px;
                padding: 12px 16px;
                line-height: 1.4;
            }
        """)
        lay.addWidget(self.editor, stretch=1)

    def load_file(self, filepath: str) -> None:
        """Load real file content from disk."""
        path = Path(filepath)
        self._current_filepath = path
        self.filename_lbl.setText(f"File: {path.name}")
        self.accept_btn.hide()
        self.reject_btn.hide()

        try:
            content = path.read_text(encoding="utf-8", errors="replace")
            # Format lines with line numbers
            lines = content.splitlines()
            html_lines = []
            for idx, line in enumerate(lines, 1):
                escaped = line.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace(" ", "&nbsp;")
                html_lines.append(f"<span style='color:#555; width:40px;'>{idx:>3}</span> &nbsp; {escaped}")
            self.editor.setHtml("<br>".join(html_lines))
        except Exception as exc:
            self.editor.setPlainText(f"Error loading file: {exc}")

    def show_diff(self, filename: str, old_code: str, new_code: str) -> None:
        """Display diff viewer mode with working Accept/Reject buttons."""
        self.filename_lbl.setText(f"Diff view: {filename}")
        self._pending_diff_content = new_code
        self.accept_btn.show()
        self.reject_btn.show()

        html_rows = []
        old_lines = old_code.splitlines()
        new_lines = new_code.splitlines()

        for idx, line in enumerate(old_lines, 1):
            escaped = line.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace(" ", "&nbsp;")
            html_rows.append(f"<div style='background:rgba(239,68,68,0.15); color:#f87171;'><span style='color:#888;'>{idx:>3} -</span> &nbsp; {escaped}</div>")

        for idx, line in enumerate(new_lines, 1):
            escaped = line.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace(" ", "&nbsp;")
            html_rows.append(f"<div style='background:rgba(16,185,129,0.15); color:#34d399; font-weight:bold;'><span style='color:#888;'>{idx:>3} +</span> &nbsp; {escaped}</div>")

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
                background: #08080c;
                border-top: 1px solid {C_BORDER_SUBTLE};
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
        tabs_hdr.setStyleSheet("background: rgba(255,255,255,0.02); border-bottom: 1px solid rgba(255,255,255,0.05);")
        t_lay = QHBoxLayout(tabs_hdr)
        t_lay.setContentsMargins(16, 4, 16, 4)

        t1 = QLabel("TERMINAL")
        t1.setStyleSheet(f"color: #a78bfa; font-size: 10px; font-weight: 800; border-bottom: 2px solid {C_PURPLE_MAIN}; padding-bottom: 4px;")
        t2 = QLabel("OUTPUT")
        t2.setStyleSheet(f"color: {C_TEXT_DIM}; font-size: 10px; font-weight: 800;")

        t_lay.addWidget(t1)
        t_lay.addSpacing(16)
        t_lay.addWidget(t2)
        t_lay.addStretch()

        clear_btn = QPushButton("🗑 Clear")
        clear_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        clear_btn.setStyleSheet("background: transparent; color: #888; border: none; font-size: 10px;")
        clear_btn.clicked.connect(self.clear_output)
        t_lay.addWidget(clear_btn)

        lay.addWidget(tabs_hdr)

        # Output text
        self.output_edit = QTextEdit()
        self.output_edit.setReadOnly(True)
        self.output_edit.setFrameShape(QFrame.Shape.NoFrame)
        self.output_edit.setStyleSheet("""
            QTextEdit {
                background: transparent;
                color: #34d399;
                font-family: 'Consolas', 'Courier New', monospace;
                font-size: 11px;
                padding: 6px 16px;
            }
        """)
        self.output_edit.append("<span style='color:#a78bfa;'>Sherly Interactive Terminal Ready.</span>")
        lay.addWidget(self.output_edit, stretch=1)

        # Input Prompt Bar
        prompt_bar = QFrame()
        prompt_bar.setStyleSheet("background: rgba(255,255,255,0.02); border-top: 1px solid rgba(255,255,255,0.05);")
        p_lay = QHBoxLayout(prompt_bar)
        p_lay.setContentsMargins(16, 4, 16, 4)

        prompt_lbl = QLabel("➔ $")
        prompt_lbl.setStyleSheet("color: #00f0ff; font-family: monospace; font-weight: bold;")
        p_lay.addWidget(prompt_lbl)

        self.cmd_input = QLineEdit()
        self.cmd_input.setPlaceholderText("Type a command (e.g. python main.py)...")
        self.cmd_input.setStyleSheet("background: transparent; color: #f3f4f6; border: none; font-family: monospace; font-size: 11px;")
        self.cmd_input.returnPressed.connect(self._run_typed_command)
        p_lay.addWidget(self.cmd_input, stretch=1)

        lay.addWidget(prompt_bar)

    def run_cmd(self, command_str: str) -> None:
        """Run a command asynchronously in terminal."""
        self.output_edit.append(f"<span style='color:#00f0ff;'>➔ {command_str}</span>")
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
        self.output_edit.append(f"<span style='color:#888;'>[Process exited with code {exit_code}]</span>\n")

    def clear_output(self) -> None:
        self.output_edit.clear()


class WorkspaceView(QFrame):
    """Dynamic Developer Workspace view."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("WorkspaceView")
        self.setStyleSheet(f"""
            #WorkspaceView {{
                background: {C_BG_PANEL};
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
        ea_lay.setContentsMargins(16, 12, 16, 12)
        ea_lay.setSpacing(8)

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
        self.footer.setStyleSheet("background: #060609; border-top: 1px solid rgba(255,255,255,0.05); font-size: 10px; color: #777; padding: 0 12px;")
        f_lay = QHBoxLayout(self.footer)
        f_lay.setContentsMargins(12, 0, 12, 0)

        self.git_lbl = QLabel("🌿 main")
        self.status_lbl = QLabel(f"UTF-8   Python {sys.version.split()[0]}   ● Sherly Active")
        f_lay.addWidget(self.git_lbl)
        f_lay.addStretch()
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

        tab_btn = QPushButton(f"🐍 {path.name} ✕" if path.suffix == ".py" else f"📄 {path.name} ✕")
        tab_btn.setStyleSheet("""
            background: #0d0d15; color: #f3f4f6; border: 1px solid rgba(255,255,255,0.08);
            border-bottom: none; border-radius: 6px 6px 0 0; padding: 6px 14px; font-size: 11px; font-weight: 600;
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
            self.git_lbl.setText(f"🌿 {branch}")
        except Exception:
            self.git_lbl.setText("🌿 main")

        curr_model = config_manager.get_current_model() or "Active"
        self.status_lbl.setText(f"UTF-8   Python {sys.version.split()[0]}   ● Sherly [{curr_model}]")
