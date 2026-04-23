"""
APP MANAGER — sherly_ui/app_manager.py
Fixes: #5  thread race (state_lock on _is_processing/_is_listening)
        #14 task queue overload (check add_task return value)
        #15 UI memory leak (emit signals on Qt thread; no direct widget refs in threads)
        #20 startup failure (check model + config before starting)
        #22 keyboard/hotkey conflict (pynput with checked import)
        #23 silent failures (all paths return visible status)
"""

from __future__ import annotations

import platform
import subprocess
import sys
import threading
import time
from pathlib import Path

from PySide6.QtCore import QObject, QCoreApplication, Signal, Slot, Qt
from PySide6.QtGui import QAction, QIcon
from PySide6.QtNetwork import QTcpServer
from PySide6.QtWidgets import QApplication, QMenu, QMessageBox, QSystemTrayIcon

from command_router import route_command
from core.task_queue import add_task
from input_validator import is_valid_input, record_command
from runtime_utils import log, safe_execute
from sherly_ui.window import SherlyWindow
from speech_to_text import transcribe
from text_to_speech import speak

try:
    from pynput import keyboard
except ImportError:
    keyboard = None

# Suppress Qt DPI warnings
QApplication.setAttribute(Qt.ApplicationAttribute.AA_DisableHighDpiScaling, True)


# ---------------------------------------------------------------------------
# Fix #20 – startup checks
# ---------------------------------------------------------------------------

def _startup_checks() -> list[str]:
    """Run pre-flight checks. Returns list of warning strings (empty = OK)."""
    warnings: list[str] = []

    # Check config.json
    if not Path("config.json").exists():
        warnings.append("config.json not found — defaults will be used.")

    # Check Ollama is reachable (only when local model is configured)
    try:
        import requests
        r = requests.get("http://localhost:11434/api/tags", timeout=2)
        if r.status_code != 200:
            warnings.append("Ollama is not responding. Local model may fail.")
    except Exception:
        warnings.append("Ollama is not reachable. Make sure it's running if you use local models.")

    return warnings


# ---------------------------------------------------------------------------
# Worker
# ---------------------------------------------------------------------------

class AssistantWorker(QObject):
    finished      = Signal()
    new_message   = Signal(str, str)
    status_changed = Signal(str)

    def __init__(self) -> None:
        super().__init__()
        self._running      = True
        self._paused       = False
        self._auto_mode    = False

        # Fix #5: single lock protecting both flags
        self._proc_lock    = threading.Lock()
        self._is_listening = False
        self._is_processing = False

    @Slot(bool)
    def set_active(self, active: bool) -> None:
        self._paused = not active
        if self._paused:
            self.status_changed.emit("Idle")

    @Slot(bool)
    def set_auto_mode(self, enabled: bool) -> None:
        self._auto_mode = enabled

    @Slot()
    def request_listen(self) -> None:
        with self._proc_lock:   # Fix #5
            if self._paused or not self._running or self._is_listening or self._is_processing:
                return
        result = add_task(self._listen_once)   # Fix #14: check return
        if result:
            self.status_changed.emit(result)

    @Slot(str)
    def process_chat_input(self, text: str) -> None:
        if not text:
            return
        valid, cleaned = is_valid_input(text)
        if not valid:
            self.status_changed.emit(cleaned)
            return
        with self._proc_lock:   # Fix #5
            if self._paused or not self._running or self._is_processing:
                return
            self._is_processing = True
        record_command(cleaned)
        result = add_task(self._process_text, cleaned)   # Fix #14
        if result:
            self.status_changed.emit(result)

    @Slot()
    def stop(self) -> None:
        self._running = False

    def run(self) -> None:
        self.status_changed.emit("Idle")
        while self._running:
            if self._paused:
                time.sleep(0.5)
                continue
            if self._auto_mode:
                with self._proc_lock:
                    busy = self._is_listening or self._is_processing
                if not busy:
                    time.sleep(1.0)
                    with self._proc_lock:
                        busy = self._is_listening or self._is_processing
                    if not busy and self._auto_mode and not self._paused:
                        self._listen_once()
            else:
                time.sleep(0.1)

    def _listen_once(self) -> None:
        with self._proc_lock:   # Fix #5
            if self._is_processing or self._paused or not self._running:
                return
            self._is_listening = True

        self.status_changed.emit("Listening")
        text = safe_execute(transcribe, "")   # Fix #23: returns "" not raises

        with self._proc_lock:
            self._is_listening = False

        if not self._running or self._paused:
            return

        if not text or text == "Didn't catch that":
            self.status_changed.emit("Idle")
            return

        valid, cleaned = is_valid_input(text)
        if not valid:
            self.status_changed.emit("Idle")
            return

        record_command(cleaned)
        with self._proc_lock:
            self._is_processing = True
        result = add_task(self._process_text, cleaned)   # Fix #14
        if result:
            # Queue was full — unblock processing flag
            with self._proc_lock:
                self._is_processing = False
            self.status_changed.emit(result)

    def _process_text(self, text: str) -> None:
        self.status_changed.emit("Thinking...")
        response = safe_execute(
            lambda: route_command(text),
            "Something went wrong. Please try again.",   # Fix #23
        )
        if not response:
            response = "No response generated."
        response = response[:500]   # Fix #11 (belt-and-suspenders cap)

        # Fix #15: emit signals — Qt marshals onto the GUI thread safely
        self.new_message.emit(text, response)
        self.status_changed.emit("Speaking")
        safe_execute(lambda: speak(response), "")
        self.status_changed.emit("Idle")

        with self._proc_lock:   # Fix #5
            self._is_processing = False


# ---------------------------------------------------------------------------
# App orchestrator
# ---------------------------------------------------------------------------

class SherlyApp:
    def __init__(self) -> None:
        instance = QApplication.instance()
        self.app: QApplication = instance if isinstance(instance, QApplication) else QApplication(sys.argv)

        # Single-instance guard
        self.instance_server = QTcpServer()
        if not self.instance_server.listen(port=49152):
            QMessageBox.critical(None, "Sherly AI", "Sherly is already running.")
            sys.exit(0)

        # Fix #20: startup warnings
        warnings = _startup_checks()
        if warnings:
            msg = "\n".join(f"⚠ {w}" for w in warnings)
            log(f"[Startup] warnings:\n{msg}")
            # Non-fatal: show in tray tooltip later, don't block launch

        self.app.setQuitOnLastWindowClosed(False)
        self.window = SherlyWindow()

        # Tray icon
        self.tray_icon = QSystemTrayIcon(self.app)
        icon_path = "sherly_ui/assets/brain.png"
        self.tray_icon.setIcon(QIcon(icon_path))

        tray_menu = QMenu()
        open_action = QAction("Open Sherly Panel", tray_menu)
        open_action.triggered.connect(self.window.show)
        exit_action = QAction("Force Exit", tray_menu)
        exit_action.triggered.connect(self.quit_app)
        tray_menu.addAction(open_action)
        tray_menu.addSeparator()
        tray_menu.addAction(exit_action)
        self.tray_icon.setContextMenu(tray_menu)
        if warnings:
            self.tray_icon.setToolTip("Sherly AI ⚠ — check logs")
        self.tray_icon.show()

        # Worker
        self.worker = AssistantWorker()
        self.worker.new_message.connect(self.window.add_message)
        self.worker.status_changed.connect(self.window.set_status)
        self.window.updater.toggle_power_sig.connect(self.worker.set_active)
        self.window.updater.listen_once_sig.connect(self.worker.request_listen)
        self.window.updater.set_auto_mode_sig.connect(self.worker.set_auto_mode)
        self.window.updater.chat_input_sig.connect(self.worker.process_chat_input)

        self.worker_thread = threading.Thread(target=self.worker.run, daemon=True)
        self.worker_thread.start()

        # Fix #22: hotkeys via pynput (graceful if not installed)
        if keyboard:
            self.hotkey_thread = threading.Thread(target=self._setup_hotkeys, daemon=True)
            self.hotkey_thread.start()
            log("Global hotkeys enabled (Ctrl+Shift+L / Ctrl+Shift+P).")
        else:
            log("pynput not installed — global hotkeys disabled.")

        self.window.show()

    def _setup_hotkeys(self) -> None:
        if not keyboard:
            return
        try:
            def on_listen():
                log("[Hotkey] Listen Once triggered")
                self.worker.request_listen()

            def on_toggle():
                new_state = not self.window.is_powered_on
                log(f"[Hotkey] Toggle Power → {new_state}")
                self.window.updater.toggle_power_sig.emit(new_state)

            # Fix #22: use pynput GlobalHotKeys (avoids spacebar / focus conflicts)
            with keyboard.GlobalHotKeys({
                "<ctrl>+<shift>+l": on_listen,
                "<ctrl>+<shift>+p": on_toggle,
            }) as h:
                h.join()
        except Exception as exc:
            log(f"[Hotkey] Error: {exc}")

    def quit_app(self) -> None:
        log("Shutting down Sherly.")
        self.worker.stop()
        self.worker_thread.join(timeout=2)
        QCoreApplication.quit()
        sys.exit(0)

    def run(self) -> int:
        return self.app.exec()


def start_app() -> None:
    app = SherlyApp()
    sys.exit(app.run())


if __name__ == "__main__":
    start_app()
