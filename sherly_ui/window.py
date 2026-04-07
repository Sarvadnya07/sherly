import sys
import random
import time
from datetime import datetime
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QApplication,
    QGraphicsDropShadowEffect,
    QScrollArea,
    QFrame,
    QSizePolicy,
    QPushButton,
    QDialog,
    QFormLayout,
    QComboBox,
    QLineEdit,
    QCheckBox,
    QGroupBox,
)
from PySide6.QtCore import Qt, QPoint, QTimer, Signal, QObject, Property, QPropertyAnimation, QEasingCurve
from PySide6.QtGui import QColor, QFont, QLinearGradient, QPainter, QPixmap, QPen, QBrush

from config_manager import (
    get_api_key,
    get_auto_mode,
    get_current_model,
    set_api_key,
    set_auto_mode,
    set_current_model,
)
from plugin_manager import get_all_plugin_states, set_plugin_enabled

class UIUpdater(QObject):
    add_msg_sig = Signal(str, str)
    status_sig = Signal(str)
    toggle_power_sig = Signal(bool)
    listen_once_sig = Signal()
    set_auto_mode_sig = Signal(bool)

class WaveformWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(100)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update)
        self.timer.start(50)
        self.bars = 60
        self.amplitudes = [random.uniform(0.1, 0.5) for _ in range(self.bars)]
        self.is_active = False

    def setActive(self, active):
        self.is_active = active

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        width = self.width()
        height = self.height()
        
        bar_width = max(2, (width / self.bars) * 0.5)
        spacing = (width / self.bars) * 0.5
        
        gradient = QLinearGradient(0, 0, 0, height)
        if self.is_active:
            gradient.setColorAt(0, QColor(0, 200, 255))
            gradient.setColorAt(0.5, QColor(108, 99, 255))
            gradient.setColorAt(1, QColor(255, 50, 200))
        else:
            gradient.setColorAt(0, QColor(100, 100, 100, 60))
            gradient.setColorAt(1, QColor(50, 50, 50, 30))
        
        painter.setBrush(gradient)
        painter.setPen(Qt.PenStyle.NoPen)
        
        for i in range(self.bars):
            if self.is_active:
                self.amplitudes[i] += (random.uniform(0.1, 1.0) - self.amplitudes[i]) * 0.2
            else:
                self.amplitudes[i] += (0.05 - self.amplitudes[i]) * 0.1
            
            bar_h = self.amplitudes[i] * height
            x = i * (bar_width + spacing)
            y = (height - bar_h) / 2
            
            painter.drawRoundedRect(int(x), int(y), int(bar_width), int(bar_h), bar_width/2, bar_width/2)

class HistoryItem(QFrame):
    def __init__(self, text, response, time_str, parent=None):
        super().__init__(parent)
        self.text = text
        self.response = response
        
        self.setObjectName("HistoryItem")
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        self.setStyleSheet("""
            #HistoryItem {
                background: rgba(255, 255, 255, 0.04);
                border-radius: 16px;
                border: 1px solid rgba(255, 255, 255, 0.08);
            }
            #HistoryItem:hover {
                background: rgba(255, 255, 255, 0.07);
                border: 1px solid rgba(108, 99, 255, 0.4);
            }
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 12, 15, 12)
        layout.setSpacing(10)
        
        header_row = QHBoxLayout()
        time_label = QLabel(time_str)
        time_label.setStyleSheet("color: rgba(255, 255, 255, 0.2); font-size: 8px; font-weight: 600;")
        
        self.copy_btn = QPushButton("📋")
        self.copy_btn.setFixedSize(24, 24)
        self.copy_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.copy_btn.setStyleSheet("""
            QPushButton {
                background: rgba(255, 255, 255, 0.05); color: #aaa;
                border: none; border-radius: 6px; font-size: 10px;
            }
            QPushButton:hover {
                background: rgba(108, 99, 255, 0.2); color: #fff;
            }
        """)
        self.copy_btn.clicked.connect(self.copy_to_clipboard)
        
        header_row.addWidget(time_label)
        header_row.addStretch()
        header_row.addWidget(self.copy_btn)
        
        user_row = QHBoxLayout()
        u_tag = QLabel("YOU")
        u_tag.setFixedWidth(30)
        u_tag.setStyleSheet("color: #6C63FF; font-size: 7px; font-weight: 900; background: rgba(108, 99, 255, 0.1); padding: 2px; border-radius: 4px;")
        u_tag.setAlignment(Qt.AlignmentFlag.AlignCenter)
        user_text = QLabel(text)
        user_text.setStyleSheet("color: rgba(255, 255, 255, 0.7); font-size: 11px; font-weight: 500;")
        user_text.setWordWrap(True)
        user_row.addWidget(u_tag, 0, Qt.AlignmentFlag.AlignTop)
        user_row.addWidget(user_text, 1)
        
        resp_row = QHBoxLayout()
        s_tag = QLabel("AI")
        s_tag.setFixedWidth(30)
        s_tag.setStyleSheet("color: #00ffcc; font-size: 7px; font-weight: 900; background: rgba(0, 255, 204, 0.1); padding: 2px; border-radius: 4px;")
        s_tag.setAlignment(Qt.AlignmentFlag.AlignCenter)
        resp_text = QLabel(response)
        resp_text.setStyleSheet("color: #ffffff; font-size: 12px; font-weight: 400;")
        resp_text.setWordWrap(True)
        resp_row.addWidget(s_tag, 0, Qt.AlignmentFlag.AlignTop)
        resp_row.addWidget(resp_text, 1)
        
        layout.addLayout(header_row)
        layout.addLayout(user_row)
        layout.addLayout(resp_row)

    def copy_to_clipboard(self):
        full_text = f"You: {self.text}\nSherly: {self.response}"
        QApplication.clipboard().setText(full_text)
        original_style = self.copy_btn.styleSheet()
        self.copy_btn.setText("✔")
        self.copy_btn.setStyleSheet("background: #00ffcc; color: black; border-radius: 6px;")
        QTimer.singleShot(1000, lambda: self.reset_copy_btn(original_style))

    def reset_copy_btn(self, style):
        self.copy_btn.setText("📋")
        self.copy_btn.setStyleSheet(style)

class SherlyWindow(QWidget):
    def __init__(self):
        super().__init__()
        
        self.is_powered_on = True
        self.updater = UIUpdater()
        self.updater.add_msg_sig.connect(self._internal_add_message)
        self.updater.status_sig.connect(self._internal_set_status)
        
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint | 
            Qt.WindowType.WindowStaysOnTopHint | 
            Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setWindowOpacity(0.0) 
        
        self.oldPos = self.pos()
        self.setup_ui()
        
        self.anim = QPropertyAnimation(self, b"windowOpacity")
        self.anim.setDuration(500)
        self.anim.setStartValue(0.0)
        self.anim.setEndValue(0.98)
        self.anim.setEasingCurve(QEasingCurve.Type.InOutQuad)
        self.anim.start()

    def setup_ui(self):
        self.setFixedSize(760, 580)
        
        self.main_container = QFrame(self)
        self.main_container.setGeometry(10, 10, 740, 560)
        self.main_container.setObjectName("MainContainer")
        self.main_container.setStyleSheet("""
            #MainContainer {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #0a0a0f, stop:1 #12121a);
                border-radius: 32px;
                border: 1px solid rgba(255, 255, 255, 0.1);
            }
        """)
        
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(50)
        shadow.setColor(QColor(0, 0, 0, 220))
        shadow.setOffset(0, 15)
        self.main_container.setGraphicsEffect(shadow)
        
        layout = QHBoxLayout(self.main_container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # --- SIDEBAR ---
        self.sidebar = QFrame()
        self.sidebar.setFixedWidth(280)
        self.sidebar.setObjectName("Sidebar")
        self.sidebar.setStyleSheet("""
            #Sidebar {
                background: rgba(255, 255, 255, 0.01);
                border-right: 1px solid rgba(255, 255, 255, 0.04);
                border-top-left_radius: 32px;
                border-bottom-left-radius: 32px;
            }
        """)
        
        sidebar_layout = QVBoxLayout(self.sidebar)
        sidebar_layout.setContentsMargins(20, 30, 20, 30)
        sidebar_layout.setSpacing(20)
        
        side_title = QLabel("CONVERSATION MEMORY")
        side_title.setStyleSheet("color: rgba(255, 255, 255, 0.2); font-size: 9px; font-weight: 900; letter-spacing: 2px;")
        sidebar_layout.addWidget(side_title)
        
        self.history_scroll = QScrollArea()
        self.history_scroll.setWidgetResizable(True)
        self.history_scroll.setFrameShape(QFrame.Shape.NoFrame)
        self.history_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.history_scroll.setStyleSheet("background: transparent;")
        self.history_scroll.verticalScrollBar().setStyleSheet("""
            QScrollBar:vertical { border: none; background: transparent; width: 4px; }
            QScrollBar::handle:vertical { background: rgba(255, 255, 255, 0.05); border-radius: 2px; }
        """)
        
        self.history_container = QWidget()
        self.history_container.setStyleSheet("background: transparent;")
        self.history_layout = QVBoxLayout(self.history_container)
        self.history_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.history_layout.setSpacing(15)
        self.history_layout.setContentsMargins(0, 0, 5, 0)
        
        self.history_scroll.setWidget(self.history_container)
        sidebar_layout.addWidget(self.history_scroll)
        
        # --- CONTENT ---
        self.content = QFrame()
        content_layout = QVBoxLayout(self.content)
        content_layout.setContentsMargins(40, 30, 40, 30)
        
        # Header
        header = QHBoxLayout()
        self.logo = QLabel("S")
        self.logo.setFixedSize(36, 36)
        self.logo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.logo.setStyleSheet("""
            background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #6C63FF, stop:1 #8F94FB);
            color: white; font-weight: bold; font-size: 20px; border-radius: 10px;
        """)
        
        title_vbox = QVBoxLayout()
        title_vbox.setSpacing(0)
        title = QLabel("Sherly Assistant")
        title.setStyleSheet("color: #fff; font-size: 18px; font-weight: 700;")
        self.status_header = QLabel("Active")
        self.status_header.setStyleSheet("color: #00ffcc; font-size: 11px; font-weight: 800; text-transform: uppercase;")
        title_vbox.addWidget(title)
        title_vbox.addWidget(self.status_header)
        
        header.addWidget(self.logo)
        header.addLayout(title_vbox)
        header.addStretch()

        self.listen_btn = QPushButton("Listen Once")
        self.listen_btn.setFixedSize(110, 36)
        self.listen_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.listen_btn.setStyleSheet("""
            QPushButton {
                background: rgba(255, 255, 255, 0.05);
                color: #fff; border-radius: 18px;
                font-size: 11px; font-weight: 700;
            }
            QPushButton:hover {
                background: rgba(0, 255, 204, 0.2);
            }
        """)
        self.listen_btn.clicked.connect(self.request_single_listen)
        header.addWidget(self.listen_btn)
        header.addSpacing(8)
        
        # Power Toggle
        self.power_btn = QPushButton("⏻")
        self.power_btn.setFixedSize(40, 40)
        self.power_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.power_btn.setStyleSheet("""
            QPushButton {
                background: rgba(0, 255, 204, 0.1); color: #00ffcc;
                border: 1px solid rgba(0, 255, 204, 0.3); border-radius: 20px;
                font-size: 18px; font-weight: bold;
            }
            QPushButton:hover {
                background: rgba(0, 255, 204, 0.2);
            }
        """)
        self.power_btn.clicked.connect(self.toggle_power)
        header.addWidget(self.power_btn)
        header.addSpacing(10)
        
        self.settings_btn = QPushButton("⚙")
        self.settings_btn.setFixedSize(40, 40)
        self.settings_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.settings_btn.setStyleSheet("""
            QPushButton {
                background: rgba(255, 255, 255, 0.05);
                color: #fff; border-radius: 20px;
                font-size: 18px; font-weight: bold;
            }
            QPushButton:hover {
                background: rgba(108, 99, 255, 0.2);
            }
        """)
        self.settings_btn.clicked.connect(self.open_settings_panel)
        header.addWidget(self.settings_btn)

        self.close_btn = QPushButton("✕")
        self.close_btn.setFixedSize(40, 40)
        self.close_btn.setStyleSheet("""
            QPushButton { background: transparent; color: #444; font-size: 18px; border-radius: 20px; }
            QPushButton:hover { background: rgba(255, 50, 50, 0.15); color: #ff5555; }
        """)
        self.close_btn.clicked.connect(self.hide)
        header.addWidget(self.close_btn)
        
        content_layout.addLayout(header)
        content_layout.addSpacing(40)
        
        self.brain_container = QWidget()
        self.brain_container.setFixedHeight(220)
        brain_box = QVBoxLayout(self.brain_container)
        self.brain_label = QLabel()
        brain_pixmap = QPixmap("sherly_ui/assets/brain.png")
        if not brain_pixmap.isNull():
            brain_pixmap = brain_pixmap.scaled(200, 200, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            self.brain_label.setPixmap(brain_pixmap)
        else:
            self.brain_label.setText("🧠")
            self.brain_label.setStyleSheet("font-size: 100px;")
        self.brain_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        brain_box.addWidget(self.brain_label)
        content_layout.addWidget(self.brain_container)
        
        content_layout.addSpacing(30)
        self.waveform = WaveformWidget()
        content_layout.addWidget(self.waveform)
        
        content_layout.addStretch()
        self.footer_status = QLabel("System Ready")
        self.footer_status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.footer_status.setStyleSheet("color: rgba(255, 255, 255, 0.3); font-size: 14px; font-weight: 500;")
        content_layout.addWidget(self.footer_status)
        
        layout.addWidget(self.sidebar)
        layout.addWidget(self.content)

    def toggle_power(self):
        self.is_powered_on = not self.is_powered_on
        self.updater.toggle_power_sig.emit(self.is_powered_on)
        
        if self.is_powered_on:
            self.power_btn.setStyleSheet("""
                QPushButton {
                    background: rgba(0, 255, 204, 0.1); color: #00ffcc;
                    border: 1px solid rgba(0, 255, 204, 0.3); border-radius: 20px;
                    font-size: 18px; font-weight: bold;
                }
                QPushButton:hover { background: rgba(0, 255, 204, 0.2); }
            """)
            self.status_header.setText("Active")
            self.status_header.setStyleSheet("color: #00ffcc; font-size: 11px; font-weight: 800;")
            self.footer_status.setText("Back Online")
        else:
            self.power_btn.setStyleSheet("""
                QPushButton {
                    background: rgba(255, 50, 50, 0.1); color: #ff5555;
                    border: 1px solid rgba(255, 50, 50, 0.3); border-radius: 20px;
                    font-size: 18px; font-weight: bold;
                }
                QPushButton:hover { background: rgba(255, 50, 50, 0.2); }
            """)
            self.status_header.setText("Paused")
            self.status_header.setStyleSheet("color: #ff5555; font-size: 11px; font-weight: 800;")
            self.footer_status.setText("Sherly is Paused")
            self.waveform.setActive(False)

    def open_settings_panel(self):
        dialog = SettingsDialog(self)
        dialog.exec()

    def request_single_listen(self):
        self.updater.listen_once_sig.emit()
        self.footer_status.setText("Listening")

    def hide_to_tray(self):
        self.hide()

    def set_status(self, text):
        self.updater.status_sig.emit(text)

    def _internal_set_status(self, text):
        self.footer_status.setText(text)
        if not self.is_powered_on: return
        
        low_text = text.lower()
        if "listening" in low_text or "recording" in low_text or "waking" in low_text:
            self.waveform.setActive(True)
            self.status_header.setText("Listening")
            self.status_header.setStyleSheet("color: #00ffcc; font-size: 11px; font-weight: 800;")
        elif "speaking" in low_text or "processing" in low_text:
            self.waveform.setActive(True)
            self.status_header.setText("Talking")
            self.status_header.setStyleSheet("color: #6C63FF; font-size: 11px; font-weight: 800;")
        elif "thinking" in low_text:
            self.waveform.setActive(True)
            self.status_header.setText("Thinking")
            self.status_header.setStyleSheet("color: #ffaa33; font-size: 11px; font-weight: 800;")
        else:
            self.waveform.setActive(False)
            self.status_header.setText("Active")
            self.status_header.setStyleSheet("color: #00ffcc; font-size: 11px; font-weight: 800;")

    def add_message(self, text, response):
        self.updater.add_msg_sig.emit(text, response)
        
    def _internal_add_message(self, text, response):
        time_str = datetime.now().strftime("%I:%M %p")
        item = HistoryItem(text, response, time_str)
        self.history_layout.insertWidget(0, item)
        self.footer_status.setText("Commands Ready")

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.oldPos = event.globalPosition().toPoint()

    def mouseMoveEvent(self, event):
        if event.buttons() & Qt.MouseButton.LeftButton:
            delta = event.globalPosition().toPoint() - self.oldPos
            self.move(self.x() + delta.x(), self.y() + delta.y())
            self.oldPos = event.globalPosition().toPoint()


class SettingsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Sherly Settings")
        self.setModal(True)
        self.setFixedSize(420, 520)
        self.setStyleSheet("""
            background: #0d0d14;
            color: #fff;
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)

        form_layout = QFormLayout()
        form_layout.setLabelAlignment(Qt.AlignmentFlag.AlignLeft)
        form_layout.setSpacing(12)

        self.model_combo = QComboBox()
        for option in ["phi3", "tinyllama", "openai", "gemini", "groq"]:
            self.model_combo.addItem(option)
        self.model_combo.setCurrentText(get_current_model())
        form_layout.addRow("Active model", self.model_combo)

        self.api_inputs = {}
        for provider in ["openai", "gemini", "groq"]:
            field = QLineEdit(get_api_key(provider) or "")
            field.setPlaceholderText("Enter API key")
            field.setStyleSheet("background: rgba(255,255,255,0.05); border-radius: 6px;")
            self.api_inputs[provider] = field
            form_layout.addRow(f"{provider.upper()} API Key", field)

        layout.addLayout(form_layout)

        self.auto_checkbox = QCheckBox("Enable auto-mode (automatically process incoming text)")
        self.auto_checkbox.setChecked(get_auto_mode())
        layout.addWidget(self.auto_checkbox)

        plugin_group = QGroupBox("Plugin toggles")
        plugin_layout = QVBoxLayout()
        plugin_layout.setSpacing(8)
        plugin_layout.setContentsMargins(12, 12, 12, 12)

        self.plugin_checkboxes = {}
        plugin_states = get_all_plugin_states()
        if plugin_states:
            for name, enabled in plugin_states.items():
                checkbox = QCheckBox(name)
                checkbox.setChecked(enabled)
                plugin_layout.addWidget(checkbox)
                self.plugin_checkboxes[name] = checkbox
        else:
            plugin_layout.addWidget(QLabel("No plugins detected yet."))

        plugin_group.setLayout(plugin_layout)
        layout.addWidget(plugin_group)

        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        apply_btn = QPushButton("Apply")
        close_btn = QPushButton("Close")
        apply_btn.clicked.connect(self._apply_changes)
        close_btn.clicked.connect(self.reject)
        btn_layout.addWidget(apply_btn)
        btn_layout.addWidget(close_btn)
        layout.addLayout(btn_layout)

    def _apply_changes(self):
        set_current_model(self.model_combo.currentText())
        for provider, field in self.api_inputs.items():
            set_api_key(provider, field.text().strip())

        auto_mode = self.auto_checkbox.isChecked()
        set_auto_mode(auto_mode)
        parent = self.parent()
        if parent and hasattr(parent, "updater"):
            parent.updater.set_auto_mode_sig.emit(auto_mode)

        for name, checkbox in self.plugin_checkboxes.items():
            set_plugin_enabled(name, checkbox.isChecked())

        self.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = SherlyWindow()
    window.show()
    sys.exit(app.exec())
