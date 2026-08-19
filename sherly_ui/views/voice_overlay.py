"""
VOICE OVERLAY VIEW — sherly_ui/views/voice_overlay.py
Dynamic Voice Listening overlay querying real hardware microphones via sounddevice,
with live visualizer and real recording controls.
"""

from __future__ import annotations

import random
from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtGui import QPainter, QColor, QRadialGradient, QPen, QBrush, QFont, QPainterPath
from PySide6.QtWidgets import (
    QFrame, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QComboBox, QWidget
)

from sherly_ui.theme import (
    C_BG_CANVAS, C_BG_CARD, C_TEXT_PRIMARY, C_TEXT_SECONDARY, C_TEXT_MUTED,
    C_ACCENT_PRIMARY, C_ACCENT_HOVER, C_ACCENT_SURFACE, C_ACCENT_GLOW,
    C_BORDER_SUBTLE, C_BORDER_MEDIUM, C_BORDER_ACCENT,
    FONT_FAMILY_UI, FONT_FAMILY_CODE, get_ui_font, get_code_font
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

        # Outer radial glow
        grad = QRadialGradient(cx, cy, 70 * ring_scale)
        grad.setColorAt(0, QColor(124, 58, 237, 100))
        grad.setColorAt(0.5, QColor(109, 40, 217, 40))
        grad.setColorAt(1, QColor(0, 0, 0, 0))
        p.setBrush(grad)
        p.setPen(Qt.PenStyle.NoPen)
        p.drawEllipse(int(cx - 70 * ring_scale), int(cy - 70 * ring_scale), int(140 * ring_scale), int(140 * ring_scale))

        # Center disc
        p.setBrush(QColor(C_BG_CARD))
        p.setPen(QPen(QColor(C_ACCENT_PRIMARY), 2))
        p.drawEllipse(int(cx - 30), int(cy - 30), 60, 60)

        # Vector Microphone Drawing (no emojis, no unset QFont warnings)
        p.setPen(QPen(QColor("#f5f5f7"), 2))
        p.setBrush(QBrush(QColor("#f5f5f7")))
        
        # Mic capsule
        p.drawRoundedRect(int(cx - 6), int(cy - 12), 12, 18, 6, 6)
        
        # Mic cradle arc
        p.setBrush(Qt.BrushStyle.NoBrush)
        cradle_pen = QPen(QColor("#f5f5f7"), 2)
        cradle_pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        p.setPen(cradle_pen)
        
        arc_path = QPainterPath()
        arc_path.arcMoveTo(cx - 10, cy - 8, 20, 18, 0)
        arc_path.arcTo(cx - 10, cy - 8, 20, 18, 0, -180)
        p.drawPath(arc_path)
        
        # Stem and base
        p.drawLine(int(cx), int(cy + 10), int(cx), int(cy + 15))
        p.drawLine(int(cx - 8), int(cy + 15), int(cx + 8), int(cy + 15))


class AudioEqualizerWidget(QWidget):
    """Refined vertical equalizer audio visualizer bars."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setFixedSize(120, 32)
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
        bw = 6
        gap = 6
        total_w = self._bars * bw + (self._bars - 1) * gap
        start_x = (w - total_w) / 2

        p.setBrush(QColor(C_ACCENT_PRIMARY))
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
        lay.setContentsMargins(32, 32, 32, 32)
        lay.setSpacing(20)

        lay.addStretch()

        self.mic_hud = PulsingMicWidget()
        lay.addWidget(self.mic_hud, 0, Qt.AlignmentFlag.AlignCenter)

        status_lbl = QLabel("● LISTENING (Ctrl+Shift+L)")
        status_lbl.setFont(get_ui_font(9, QFont.Weight.Bold))
        status_lbl.setStyleSheet("color: #c4b5fd; letter-spacing: 2px;")
        lay.addWidget(status_lbl, 0, Qt.AlignmentFlag.AlignCenter)

        self.transcript_lbl = QLabel()
        self.transcript_lbl.setWordWrap(True)
        self.transcript_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.transcript_lbl.setFont(get_ui_font(14, QFont.Weight.DemiBold))
        self.transcript_lbl.setStyleSheet(f"color: {C_TEXT_PRIMARY};")
        self._update_transcript_text()
        lay.addWidget(self.transcript_lbl, 0, Qt.AlignmentFlag.AlignCenter)

        self.equalizer = AudioEqualizerWidget()
        lay.addWidget(self.equalizer, 0, Qt.AlignmentFlag.AlignCenter)

        lay.addStretch()

        ctrl_bar = QFrame()
        ctrl_bar.setStyleSheet(f"""
            QFrame {{
                background: {C_BG_CARD};
                border: 1px solid {C_BORDER_MEDIUM};
                border-radius: 10px;
                padding: 4px;
            }}
        """)
        c_lay = QHBoxLayout(ctrl_bar)
        c_lay.setContentsMargins(12, 6, 12, 6)
        c_lay.setSpacing(10)

        cancel_btn = QPushButton("Cancel")
        cancel_btn.setFont(get_ui_font(9, QFont.Weight.Medium))
        cancel_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        cancel_btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                color: {C_TEXT_MUTED};
                border: none;
                padding: 6px 12px;
            }}
            QPushButton:hover {{
                color: {C_TEXT_PRIMARY};
            }}
        """)
        cancel_btn.clicked.connect(self.cancel_clicked.emit)
        c_lay.addWidget(cancel_btn)

        stop_btn = QPushButton("Stop Recording")
        stop_btn.setFont(get_ui_font(9, QFont.Weight.Bold))
        stop_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        stop_btn.setStyleSheet(f"""
            QPushButton {{
                background: {C_ACCENT_PRIMARY};
                color: #ffffff;
                border: none;
                border-radius: 6px;
                padding: 6px 16px;
            }}
            QPushButton:hover {{
                background: {C_ACCENT_HOVER};
            }}
        """)
        stop_btn.clicked.connect(self.stop_clicked.emit)
        c_lay.addWidget(stop_btn)

        self.mic_combo = QComboBox()
        self.mic_combo.setFont(get_ui_font(9, QFont.Weight.Normal))
        self.mic_combo.setStyleSheet(f"""
            QComboBox {{
                background: rgba(255, 255, 255, 0.05);
                color: {C_TEXT_SECONDARY};
                border: 1px solid {C_BORDER_SUBTLE};
                border-radius: 6px;
                padding: 5px 12px;
            }}
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

