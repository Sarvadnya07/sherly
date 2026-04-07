import sys
import threading
import time
from queue import Empty

from PySide6.QtCore import QObject, QCoreApplication, Signal, Slot
from PySide6.QtGui import QAction, QIcon
from PySide6.QtNetwork import QTcpServer
from PySide6.QtWidgets import QApplication, QMenu, QMessageBox, QSystemTrayIcon

from command_router import route_command
from config_manager import get_auto_mode
from core.task_queue import add_task
from runtime_utils import log, safe_execute
from sherly_ui.window import SherlyWindow
from speech_to_text import transcribe
from text_to_speech import speak


class AssistantWorker(QObject):
    finished = Signal()
    new_message = Signal(str, str)
    status_changed = Signal(str)

    def __init__(self):
        super().__init__()
        self._running = True
        self._paused = False
        self._is_listening = False
        self._auto_mode = get_auto_mode()
        self._is_processing = False

    @Slot(bool)
    def set_active(self, active):
        self._paused = not active
        if self._paused:
            self.status_changed.emit("Idle")

    @Slot(bool)
    def set_auto_mode(self, enabled):
        self._auto_mode = bool(enabled)
        if self._auto_mode and not self._paused:
            self.request_listen()

    @Slot()
    def request_listen(self):
        if self._paused or not self._running or self._is_listening or self._is_processing:
            return
        add_task(self._listen_once)

    @Slot()
    def stop(self):
        self._running = False
        task_queue.put("stop")

    def run(self):
        self.status_changed.emit("Idle")

        while self._running:
            if self._paused:
                time.sleep(0.2)
                continue

            if self._auto_mode and not self._is_listening and not self._is_processing:
                add_task(self._listen_once)

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
        if not text or len(text.strip()) < 2:
            self.status_changed.emit("Idle")
            return

        self._is_processing = True
        add_task(self._process_text, text)

    def _process_text(self, text):
        self.status_changed.emit("Thinking...")
        response = safe_execute(lambda: route_command(text), "I hit an error while processing that.")
        if not response:
            response = "No response generated."
        response = response[:250]

        self.new_message.emit(text, response)
        self.status_changed.emit("Speaking")
        safe_execute(lambda: speak(response), "")
        self.status_changed.emit("Idle")
        self._is_processing = False


class SherlyApp:
    def __init__(self):
        self.app = QApplication.instance() or QApplication(sys.argv)

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

        self.worker_thread = threading.Thread(target=self.worker.run, daemon=True)
        self.worker_thread.start()
        self.window.show()
        log("Sherly UI started.")

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
