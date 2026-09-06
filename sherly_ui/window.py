"""
SHERLY ASSISTANT — MAIN WINDOW (FULLY DYNAMIC & FUNCTIONAL)
100% dynamic bindings across all 4 views:
  1. Main Assistant (Real AI prompt execution, QFileDialog attachments, timeline stream)
  2. Developer Workspace (Real project file loader, git status, live subprocess terminal)
  3. Model Management (Real Ollama scanner, real API provider configuration, auto-detect toggle)
  4. Voice Listening HUD (Real hardware mic query via sounddevice)
"""

from __future__ import annotations

import sys

from PySide6.QtCore import QObject, Qt, Signal
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication, QFrame, QHBoxLayout, QStackedWidget, QVBoxLayout, QWidget

import config_manager
from sherly_ui.header_bar import HeaderBar
from sherly_ui.sidebar import Sidebar
from sherly_ui.theme import C_BG_DARK, C_BORDER_SUBTLE, STYLE_MAIN_WINDOW
from sherly_ui.views.assistant_view import AssistantView
from sherly_ui.views.models_view import ModelsView
from sherly_ui.views.voice_overlay import VoiceOverlayView
from sherly_ui.views.workspace_view import WorkspaceView


# ── Shared Signals Object ─────────────────────────────────────────────────────
class UIUpdater(QObject):
    add_msg_sig          = Signal(str, str)
    status_sig           = Signal(str)
    toggle_power_sig     = Signal(bool)
    listen_once_sig      = Signal()
    set_auto_mode_sig    = Signal(bool)
    chat_input_sig       = Signal(str)
    refresh_actions_sig  = Signal()


class SherlyWindow(QWidget):
    """Main Sherly Assistant Application Window."""

    def __init__(self) -> None:
        super().__init__()
        self.updater = UIUpdater()
        self.is_powered_on = True

        self.setWindowTitle("Sherly — Developer Workspace")
        self.setWindowIcon(QIcon("sherly_ui/assets/brain.png"))
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setStyleSheet(STYLE_MAIN_WINDOW)

        self._setup_ui()

        # Connect updater signals
        self.updater.add_msg_sig.connect(self._on_add_message)
        self.updater.status_sig.connect(self._on_status)

        # Update initial model badge
        self.refresh_header_model()

    def _setup_ui(self) -> None:
        self.resize(1120, 740)

        # Outer Frame
        outer = QFrame(self)
        outer.setObjectName("Outer")
        outer.setStyleSheet(f"""
            #Outer {{
                background: {C_BG_DARK};
                border: 1px solid {C_BORDER_SUBTLE};
                border-radius: 10px;
            }}
        """)

        outer_lay = QVBoxLayout(self)
        outer_lay.setContentsMargins(0, 0, 0, 0)
        outer_lay.addWidget(outer)

        main_box = QVBoxLayout(outer)
        main_box.setContentsMargins(0, 0, 0, 0)
        main_box.setSpacing(0)

        # 1. Top Header Bar
        self.header = HeaderBar(self)
        self.header.settings_clicked.connect(lambda: self.switch_view("models"))
        self.header.minimize_clicked.connect(self.showMinimized)
        self.header.maximize_clicked.connect(self._toggle_maximize)
        self.header.close_clicked.connect(self.close)
        main_box.addWidget(self.header)

        # 2. Main Body (Sidebar + Stacked Views)
        body = QWidget()
        body_lay = QHBoxLayout(body)
        body_lay.setContentsMargins(0, 0, 0, 0)
        body_lay.setSpacing(0)

        # Left Sidebar
        self.sidebar = Sidebar(self)
        self.sidebar.view_changed.connect(self.switch_view)
        self.sidebar.file_selected.connect(self._on_file_selected)
        self.sidebar.run_project.connect(self._on_run_project)
        body_lay.addWidget(self.sidebar)

        # Stacked Views
        self.views_stack = QStackedWidget()

        self.assistant_view = AssistantView()
        self.assistant_view.message_submitted.connect(self._on_user_typed)

        self.workspace_view = WorkspaceView()

        self.models_view    = ModelsView()
        self.models_view.model_changed.connect(self._on_model_changed)

        self.voice_overlay  = VoiceOverlayView()
        self.voice_overlay.stop_clicked.connect(lambda: self.switch_view("assistant"))
        self.voice_overlay.cancel_clicked.connect(lambda: self.switch_view("workspace"))

        self.views_stack.addWidget(self.assistant_view)   # index 0: "assistant"
        self.views_stack.addWidget(self.workspace_view)   # index 1: "workspace"
        self.views_stack.addWidget(self.models_view)       # index 2: "models"
        self.views_stack.addWidget(self.voice_overlay)     # index 3: "voice"

        # Default view: Developer Workspace
        self.views_stack.setCurrentIndex(1)
        self.header.set_title("Sherly — Developer Workspace")

        body_lay.addWidget(self.views_stack, stretch=1)
        main_box.addWidget(body, stretch=1)

    def switch_view(self, view_id: str) -> None:
        self.sidebar.set_active_view(view_id)
        if view_id == "assistant":
            self.views_stack.setCurrentWidget(self.assistant_view)
            self.header.set_title("Sherly — Main Assistant")
        elif view_id == "workspace":
            self.views_stack.setCurrentWidget(self.workspace_view)
            self.header.set_title("Sherly — Developer Workspace")
            self.workspace_view.update_status_bar()
        elif view_id == "models":
            self.models_view.refresh_models()
            self.views_stack.setCurrentWidget(self.models_view)
            self.header.set_title("Sherly — Model Management")
        elif view_id == "voice":
            self.views_stack.setCurrentWidget(self.voice_overlay)
            self.header.set_title("Sherly — Voice Listening")

    def refresh_header_model(self) -> None:
        curr_model = config_manager.get_current_model() or "No Model Selected"
        self.header.set_model_name(curr_model)

    def _on_model_changed(self, model_name: str) -> None:
        self.refresh_header_model()
        self.workspace_view.update_status_bar()

    def _on_file_selected(self, filepath: str) -> None:
        self.workspace_view.load_file(filepath)

    def _on_run_project(self) -> None:
        self.switch_view("workspace")
        self.workspace_view.run_main_project()

    def _toggle_maximize(self) -> None:
        if self.isMaximized():
            self.showNormal()
        else:
            self.showMaximized()

    def _on_user_typed(self, text: str) -> None:
        self.updater.chat_input_sig.emit(text)

    def _on_add_message(self, text: str, response: str) -> None:
        self.assistant_view.add_response(text, response)

    def _on_status(self, text: str) -> None:
        if "listening" in text.lower():
            self.switch_view("voice")

    def add_message(self, text: str, response: str) -> None:
        self.updater.add_msg_sig.emit(text, response)

    def set_status(self, text: str) -> None:
        self.updater.status_sig.emit(text)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = SherlyWindow()
    win.show()
    sys.exit(app.exec())
