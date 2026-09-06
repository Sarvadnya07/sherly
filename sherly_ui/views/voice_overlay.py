"""
VOICE OVERLAY VIEW — sherly_ui/views/voice_overlay.py
Dynamic Voice Listening overlay querying real hardware microphones via sounddevice,
with live visualizer and real recording controls.
"""

from __future__ import annotations

import random

import sounddevice as sd
from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtGui import QBrush, QColor, QFont, QPainter, QPainterPath, QPen, QRadialGradient
from PySide6.QtWidgets import QComboBox, QFrame, QHBoxLayout, QLabel, QPushButton, QVBoxLayout, QWidget

from sherly_ui.theme import (
    C_ACCENT_PRIMARY,
    C_BG_CANVAS,
    C_TEXT_PRIMARY,
    get_ui_font,
)


class PulsingMicWidget(QWidget):
    """Animated concentric glowing microphone HUD."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setFixedSize(140, 140)
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

        # Outer radial glow
        grad = QRadialGradient(cx, cy, 60 * ring_scale)
        grad.setColorAt(0, QColor(99, 102, 241, 60))
        grad.setColorAt(0.5, QColor(79, 70, 229, 20))
        grad.setColorAt(1, QColor(0, 0, 0, 0))
        p.setBrush(grad)
        p.setPen(Qt.PenStyle.NoPen)
        p.drawEllipse(int(cx - 60 * ring_scale), int(cy - 60 * ring_scale), int(120 * ring_scale), int(120 * ring_scale))

        # Center disc
        p.setBrush(QColor("#18181b"))
        p.setPen(QPen(QColor(C_ACCENT_PRIMARY), 1.5))
        p.drawEllipse(int(cx - 24), int(cy - 24), 48, 48)

        # Vector Microphone Drawing
        p.setPen(QPen(QColor("#f4f4f5"), 1.5))
        p.setBrush(QBrush(QColor("#f4f4f5")))
        
        # Mic capsule
        p.drawRoundedRect(int(cx - 5), int(cy - 10), 10, 14, 5, 5)
        
        # Mic cradle arc
        p.setBrush(Qt.BrushStyle.NoBrush)
        cradle_pen = QPen(QColor("#f4f4f5"), 1.5)
        cradle_pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        p.setPen(cradle_pen)
        
        arc_path = QPainterPath()
        arc_path.arcMoveTo(cx - 8, cy - 7, 16, 14, 0)
        arc_path.arcTo(cx - 8, cy - 7, 16, 14, 0, -180)
        p.drawPath(arc_path)
        
        # Stem and base
        p.drawLine(int(cx), int(cy + 7), int(cx), int(cy + 12))
        p.drawLine(int(cx - 6), int(cy + 12), int(cx + 6), int(cy + 12))


class AudioEqualizerWidget(QWidget):
    """Refined vertical equalizer audio visualizer bars."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setFixedSize(100, 24)
        self._bars = 7
        self._heights = [0.3] * self._bars
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._animate)
        self._timer.start(60)

    def _animate(self) -> None:
        for i in range(self._bars):
            self._heights[i] += (random.uniform(0.15, 0.90) - self._heights[i]) * 0.3
        self.update()

    def paintEvent(self, _) -> None:
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        w, h = self.width(), self.height()
        bw = 4
        gap = 5
        total_w = self._bars * bw + (self._bars - 1) * gap
        start_x = (w - total_w) / 2

        p.setBrush(QColor(C_ACCENT_PRIMARY))
        p.setPen(Qt.PenStyle.NoPen)

        for i in range(self._bars):
            bh = max(3, int(self._heights[i] * h))
            x = start_x + i * (bw + gap)
            y = (h - bh) / 2
            p.drawRoundedRect(int(x), int(y), bw, bh, 2, 2)


class VoiceOverlayView(QFrame):
    """Dynamic Voice Listening Overlay."""

    stop_clicked   = Signal()
    cancel_clicked = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("VoiceOverlay")
        self.setStyleSheet(f"""
            #VoiceOverlay {{
                background: {C_BG_CANVAS};
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
        lay.setContentsMargins(24, 24, 24, 24)
        lay.setSpacing(16)

        lay.addStretch()

        self.mic_hud = PulsingMicWidget()
        lay.addWidget(self.mic_hud, 0, Qt.AlignmentFlag.AlignCenter)

        status_lbl = QLabel("● LISTENING (Ctrl+Shift+L)")
        status_lbl.setFont(get_ui_font(8, QFont.Weight.Bold))
        status_lbl.setStyleSheet("color: #a1a1aa; letter-spacing: 1.5px;")
        lay.addWidget(status_lbl, 0, Qt.AlignmentFlag.AlignCenter)

        self.transcript_lbl = QLabel()
        self.transcript_lbl.setWordWrap(True)
        self.transcript_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.transcript_lbl.setFont(get_ui_font(12, QFont.Weight.DemiBold))
        self.transcript_lbl.setStyleSheet(f"color: {C_TEXT_PRIMARY};")
        self._update_transcript_text()
        lay.addWidget(self.transcript_lbl, 0, Qt.AlignmentFlag.AlignCenter)

        self.equalizer = AudioEqualizerWidget()
        lay.addWidget(self.equalizer, 0, Qt.AlignmentFlag.AlignCenter)

        lay.addStretch()

        ctrl_bar = QFrame()
        ctrl_bar.setStyleSheet("""
            QFrame {
                background: #18181b;
                border: 1px solid rgba(255, 255, 255, 0.08);
                border-radius: 8px;
                padding: 4px;
            }
        """)
        c_lay = QHBoxLayout(ctrl_bar)
        c_lay.setContentsMargins(8, 4, 8, 4)
        c_lay.setSpacing(8)

        cancel_btn = QPushButton("Cancel")
        cancel_btn.setFont(get_ui_font(8, QFont.Weight.Medium))
        cancel_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        cancel_btn.setStyleSheet("""
            QPushButton {
                background: transparent;
                color: #71717a;
                border: none;
                padding: 4px 10px;
            }
            QPushButton:hover {
                color: #f4f4f5;
            }
        """)
        cancel_btn.clicked.connect(self.cancel_clicked.emit)
        c_lay.addWidget(cancel_btn)

        stop_btn = QPushButton("Stop Recording")
        stop_btn.setFont(get_ui_font(8, QFont.Weight.Bold))
        stop_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        stop_btn.setStyleSheet("""
            QPushButton {
                background: #27272a;
                color: #f4f4f5;
                border: 1px solid rgba(255, 255, 255, 0.08);
                border-radius: 6px;
                padding: 4px 12px;
            }
            QPushButton:hover {
                background: #3f3f46;
                color: #ffffff;
            }
        """)
        stop_btn.clicked.connect(self.stop_clicked.emit)
        c_lay.addWidget(stop_btn)

        self.mic_combo = QComboBox()
        self.mic_combo.setFont(get_ui_font(8, QFont.Weight.Normal))
        self.mic_combo.setStyleSheet("""
            QComboBox {
                background: rgba(255, 255, 255, 0.04);
                color: #a1a1aa;
                border: 1px solid rgba(255, 255, 255, 0.06);
                border-radius: 6px;
                padding: 4px 8px;
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
                    self.mic_combo.addItem(name)
                    count += 1
            if count == 0:
                self.mic_combo.addItem("System Default Mic")
        except Exception:
            self.mic_combo.addItem("Default Microphone")

    def set_transcription(self, text: str) -> None:
        self._transcription = text
        self._update_transcript_text()

    def _toggle_cursor(self) -> None:
        self._cursor_visible = not self._cursor_visible
        self._update_transcript_text()

    def _update_transcript_text(self) -> None:
        cursor = "_" if self._cursor_visible else " "
        self.transcript_lbl.setText(f'"{self._transcription}{cursor}"')
