"""
VOICE OVERLAY VIEW — sherly_ui/views/voice_overlay.py
Dynamic Voice Listening overlay querying real hardware microphones via sounddevice,
with live visualizer and real recording controls.
"""

from __future__ import annotations

import random
from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtGui import QPainter, QColor, QRadialGradient, QPen
from PySide6.QtWidgets import (
    QFrame, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QComboBox, QWidget
)

from sherly_ui.theme import (
    C_BG_DARK, C_TEXT_PRIMARY, C_TEXT_MUTED, C_PURPLE_MAIN, C_PURPLE_GLOW
)
import sounddevice as sd


class PulsingMicWidget(QWidget):
    """Animated concentric glowing purple radial microphone HUD."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setFixedSize(160, 160)
        self._pulse = 0.0
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._animate)
        self._timer.start(40)

    def _animate(self) -> None:
        self._pulse = (self._pulse + 0.05) % 6.28
        self.update()

    def paintEvent(self, _) -> None:
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        cx, cy = self.width() / 2, self.height() / 2
        import math
        ring_scale = 1.0 + 0.08 * math.sin(self._pulse)

        grad = QRadialGradient(cx, cy, 70 * ring_scale)
        grad.setColorAt(0, QColor(139, 92, 246, 120))
        grad.setColorAt(0.5, QColor(109, 40, 217, 60))
        grad.setColorAt(1, QColor(0, 0, 0, 0))
        p.setBrush(grad)
        p.setPen(Qt.PenStyle.NoPen)
        p.drawEllipse(int(cx - 70 * ring_scale), int(cy - 70 * ring_scale), int(140 * ring_scale), int(140 * ring_scale))

        p.setBrush(QColor(22, 18, 36))
        p.setPen(QPen(QColor(139, 92, 246, 180), 2))
        p.drawEllipse(int(cx - 30), int(cy - 30), 60, 60)

        p.setPen(QColor(243, 244, 246))
        p.setFont(self.font())
        p.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, "🎙")


class AudioEqualizerWidget(QWidget):
    """Purple vertical equalizer audio visualizer bars."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setFixedSize(120, 36)
        self._bars = 7
        self._heights = [0.3] * self._bars
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._animate)
        self._timer.start(60)

    def _animate(self) -> None:
        for i in range(self._bars):
            self._heights[i] += (random.uniform(0.15, 0.95) - self._heights[i]) * 0.3
        self.update()

    def paintEvent(self, _) -> None:
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        w, h = self.width(), self.height()
        bw = 8
        gap = 6
        total_w = self._bars * bw + (self._bars - 1) * gap
        start_x = (w - total_w) / 2

        p.setBrush(QColor(139, 92, 246))
        p.setPen(Qt.PenStyle.NoPen)

        for i in range(self._bars):
            bh = max(4, int(self._heights[i] * h))
            x = start_x + i * (bw + gap)
            y = (h - bh) / 2
            p.drawRoundedRect(int(x), int(y), bw, bh, 3, 3)


class VoiceOverlayView(QFrame):
    """Dynamic Voice Listening Overlay."""

    stop_clicked   = Signal()
    cancel_clicked = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("VoiceOverlay")
        self.setStyleSheet(f"""
            #VoiceOverlay {{
                background: {C_BG_DARK};
            }}
        """)
        self._transcription = "Listening to audio input..."
        self._cursor_visible = True
        self._cursor_timer = QTimer(self)
        self._cursor_timer.timeout.connect(self._toggle_cursor)
        self._cursor_timer.start(500)
        self._setup_ui()
        self._refresh_mic_devices()

    def _setup_ui(self) -> None:
        lay = QVBoxLayout(self)
        lay.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lay.setContentsMargins(32, 32, 32, 32)
        lay.setSpacing(24)

        lay.addStretch()

        self.mic_hud = PulsingMicWidget()
        lay.addWidget(self.mic_hud, 0, Qt.AlignmentFlag.AlignCenter)

        status_lbl = QLabel("● LISTENING...")
        status_lbl.setStyleSheet("color: #a78bfa; font-size: 11px; font-weight: 800; letter-spacing: 2px;")
        lay.addWidget(status_lbl, 0, Qt.AlignmentFlag.AlignCenter)

        self.transcript_lbl = QLabel()
        self.transcript_lbl.setWordWrap(True)
        self.transcript_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.transcript_lbl.setStyleSheet(f"""
            color: {C_TEXT_PRIMARY};
            font-size: 20px;
            font-weight: 600;
        """)
        self._update_transcript_text()
        lay.addWidget(self.transcript_lbl, 0, Qt.AlignmentFlag.AlignCenter)

        self.equalizer = AudioEqualizerWidget()
        lay.addWidget(self.equalizer, 0, Qt.AlignmentFlag.AlignCenter)

        lay.addStretch()

        ctrl_bar = QFrame()
        ctrl_bar.setStyleSheet("""
            QFrame {
                background: rgba(22, 22, 34, 0.9);
                border: 1px solid rgba(255, 255, 255, 0.1);
                border-radius: 20px;
                padding: 4px;
            }
        """)
        c_lay = QHBoxLayout(ctrl_bar)
        c_lay.setContentsMargins(12, 6, 12, 6)
        c_lay.setSpacing(12)

        cancel_btn = QPushButton("✕ Cancel")
        cancel_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        cancel_btn.setStyleSheet("""
            QPushButton {
                background: transparent; color: #888; border: none; font-size: 12px; font-weight: 600; padding: 6px 12px;
            }
            QPushButton:hover { color: #f3f4f6; }
        """)
        cancel_btn.clicked.connect(self.cancel_clicked.emit)
        c_lay.addWidget(cancel_btn)

        stop_btn = QPushButton("⏹ Stop Recording")
        stop_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        stop_btn.setStyleSheet("""
            QPushButton {
                background: #8b5cf6; color: white; border: none; border-radius: 12px;
                font-size: 12px; font-weight: 700; padding: 8px 18px;
            }
            QPushButton:hover { background: #9d7aea; }
        """)
        stop_btn.clicked.connect(self.stop_clicked.emit)
        c_lay.addWidget(stop_btn)

        self.mic_combo = QComboBox()
        self.mic_combo.setStyleSheet("""
            QComboBox {
                background: rgba(255,255,255,0.05); color: #ccc; border: 1px solid rgba(255,255,255,0.1);
                border-radius: 12px; padding: 6px 12px; font-size: 11px;
            }
        """)
        c_lay.addWidget(self.mic_combo)

        lay.addWidget(ctrl_bar, 0, Qt.AlignmentFlag.AlignCenter)

    def _refresh_mic_devices(self) -> None:
        """Query real input hardware microphones from sounddevice."""
        self.mic_combo.clear()
        try:
            devices = sd.query_devices()
            count = 0
            for dev in devices:
                if dev.get("max_input_channels", 0) > 0:
                    name = dev.get("name", "Unknown Mic")
                    self.mic_combo.addItem(f"🎙 {name}")
                    count += 1
            if count == 0:
                self.mic_combo.addItem("🎙 System Default Mic")
        except Exception:
            self.mic_combo.addItem("🎙 Default Microphone")

    def set_transcription(self, text: str) -> None:
        self._transcription = text
        self._update_transcript_text()

    def _toggle_cursor(self) -> None:
        self._cursor_visible = not self._cursor_visible
        self._update_transcript_text()

    def _update_transcript_text(self) -> None:
        cursor = "_" if self._cursor_visible else " "
        self.transcript_lbl.setText(f'"{self._transcription}{cursor}"')
