from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel
from PySide6.QtCore import Qt, QTimer

class StatusOverlay(QWidget):
    """
    Long-term vision: Desktop Overlay UI.
    A transparent, always-on-top overlay to show Sherly's status.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(
            Qt.WindowStaysOnTopHint | 
            Qt.FramelessWindowHint | 
            Qt.Tool |
            Qt.WindowTransparentForInput
        )
        self.setAttribute(Qt.WA_TranslucentBackground)
        
        self.layout = QVBoxLayout(self)
        self.label = QLabel("Sherly: Listening...")
        self.label.setStyleSheet("""
            color: #00ff00;
            background-color: rgba(0, 0, 0, 150);
            padding: 10px;
            border-radius: 10px;
            font-weight: bold;
            font-family: 'Segoe UI', sans-serif;
        """)
        self.layout.addWidget(self.label)
        
        self.setFixedSize(200, 50)
        self.move(20, 20) # Top left

    def set_status(self, text: str):
        self.label.setText(f"Sherly: {text}")
        self.show()
        # Auto-hide after 5 seconds if not busy
        if "Listening" not in text:
            QTimer.singleShot(5000, self.hide)
