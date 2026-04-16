import sys
import threading
import time

from PySide6.QtCore import QObject, QCoreApplication, Signal, Slot, Qt
from PySide6.QtGui import QAction, QIcon
from PySide6.QtNetwork import QTcpServer
from PySide6.QtWidgets import QApplication, QMenu, QMessageBox, QSystemTrayIcon

from command_router import route_command
from core.task_queue import add_task
from runtime_utils import log, safe_execute
from sherly_ui.window import SherlyWindow
from speech_to_text import transcribe
from text_to_speech import speak
try:
    from pynput import keyboard
except ImportError:
    keyboard = None

# Disable high-DPI scaling to avoid Windows DPI awareness warnings
QApplication.setAttribute(Qt.ApplicationAttribute.AA_DisableHighDpiScaling, True)


def is_valid_input(text):
    if not text:
        return False

    text = text.strip().lower()

    # reject noise patterns
    if len(text) < 3:
        return False

    if text in ["...", ".", "uh", "hmm"]:
        return False

    return True


class AssistantWorker(QObject):
    finished = Signal()
    new_message = Signal(str, str)
    status_changed = Signal(str)

    def __init__(self):
        super().__init__()
        self._running = True
        self._paused = False
        self._is_listening = False
        # Force manual trigger mode to stop continuous listening loops
        self._auto_mode = False
        self._is_processing = False

    @Slot(bool)
    def set_active(self, active):
        self._paused = not active
        if self._paused:
            self.status_changed.emit("Idle")

    @Slot(bool)
    def set_auto_mode(self, enabled):
        self._auto_mode = enabled

    @Slot()
    def request_listen(self):
        if self._paused or not self._running or self._is_listening or self._is_processing:
            return
        add_task(self._listen_once)

    @Slot(str)
    def process_chat_input(self, text: str):
        """Route a typed message through the same pipeline as voice."""
        if not text or self._paused or not self._running or self._is_processing:
            return
        if is_valid_input(text):
            self._is_processing = True
            add_task(self._process_text, text)

    @Slot()
    def stop(self):
        self._running = False

    def run(self):
        self.status_changed.emit("Idle")

        while self._running:
            if self._paused:
                time.sleep(0.5)
                continue

            if self._auto_mode and not self._is_listening and not self._is_processing:
                # In auto-mode, we wait for a moment and then listen
                time.sleep(1.0)
                if self._auto_mode and not self._paused:
                    self._listen_once()
            else:
                time.sleep(0.1)

    def _listen_once(self):
        if self._is_processing or self._paused or not self._running:
            return

        self._is_listening = True
        self.status_changed.emit("Listening")
        text = safe_execute(transcribe, "")
        self._is_listening = False

        if not self._running or self._paused:
            return

        if not is_valid_input(text):
            self.status_changed.emit("Filtered noise")
            return

        self._is_processing = True
        add_task(self._process_text, text)

    def _process_text(self, text):
        self.status_changed.emit("Thinking...")
        response = safe_execute(lambda: route_command(text), "I hit an error while processing that.")
        if not response:
            response = "No response generated."
        response = response[:2000]

        self.new_message.emit(text, response)
        self.status_changed.emit("Speaking")
        safe_execute(lambda: speak(response), "")
        self.status_changed.emit("Idle")
        self._is_processing = False


class SherlyApp:
    def __init__(self):
        # QApplication instance for type checkers
        instance = QApplication.instance()
        if instance is None or not isinstance(instance, QApplication):
            self.app: QApplication = QApplication(sys.argv)
        else:
            self.app: QApplication = instance

        self.instance_server = QTcpServer()
        if not self.instance_server.listen(port=49152):
            QMessageBox.critical(None, "Sherly AI", "Sherly is already running in the background.")
            sys.exit(0)

        self.app.setQuitOnLastWindowClosed(False)
        self.window = SherlyWindow()

        self.tray_icon = QSystemTrayIcon(self.app)
        self.tray_icon.setIcon(QIcon("sherly_ui/assets/brain.png"))

        tray_menu = QMenu()
        open_action = QAction("Open SherlyPanel", tray_menu)
        open_action.triggered.connect(self.window.show)
        exit_action = QAction("Force Exit", tray_menu)
        exit_action.triggered.connect(self.quit_app)

        tray_menu.addAction(open_action)
        tray_menu.addSeparator()
        tray_menu.addAction(exit_action)
        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.show()

        self.worker = AssistantWorker()
        self.worker.new_message.connect(self.window.add_message)
        self.worker.status_changed.connect(self.window.set_status)

        self.window.updater.toggle_power_sig.connect(self.worker.set_active)
        self.window.updater.listen_once_sig.connect(self.worker.request_listen)
        self.window.updater.set_auto_mode_sig.connect(self.worker.set_auto_mode)
        self.window.updater.chat_input_sig.connect(self.worker.process_chat_input)

        self.worker_thread = threading.Thread(target=self.worker.run, daemon=True)
        self.worker_thread.start()
        
        # Global Hotkey setup (optional if pynput is available)
        if keyboard:
            self.hotkey_thread = threading.Thread(target=self._setup_hotkeys, daemon=True)
            self.hotkey_thread.start()
            log("Sherly UI started with global hotkeys (Ctrl+Shift+L / Ctrl+Shift+P).")
        else:
            log("pynput not installed; global hotkeys disabled.")

        self.window.show()

    def _setup_hotkeys(self):
        if not keyboard:
            return
        try:
            def on_activate_listen():
                log("Hotkey Triggered: Listen Once")
                self.worker.request_listen()

            def on_activate_toggle():
                new_state = not self.window.is_powered_on
                log(f"Hotkey Triggered: Toggle Power -> {new_state}")
                # We need to call window toggle_power on the GUI thread
                self.window.updater.toggle_power_sig.emit(new_state)

            with keyboard.GlobalHotKeys({
                '<ctrl>+<shift>+l': on_activate_listen,
                '<ctrl>+<shift>+p': on_activate_toggle}) as h:
                h.join()
        except Exception as e:
            log(f"Hotkey Error: {e}")

    def quit_app(self):
        log("Shutting down Sherly.")
        self.worker.stop()
        self.worker_thread.join(timeout=2)
        QCoreApplication.quit()
        sys.exit(0)

    def run(self):
        return self.app.exec()


def start_app():
    app = SherlyApp()
    sys.exit(app.run())


if __name__ == "__main__":
    start_app()
