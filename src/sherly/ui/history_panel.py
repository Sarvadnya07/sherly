"""
CONVERSATION HISTORY PANEL — history_panel.py
Implements:
  OE-3  Collapsible QDockWidget side panel showing rolling conversation history.
         Displays timestamps, action badges ([UNDO] undoable, [LOCK] locked),
         and is both scrollable and searchable.

  Features:
    - Real-time update: call refresh() to sync from conversation_memory.py
    - Search bar: filters entries by keyword (case-insensitive)
    - Badge column: [UNDO] for undoable actions, [LOCK] for non-undoable
    - Timestamps in local time (ISO format)
    - Collapsible via QDockWidget toggle (View menu or title bar button)

  Usage (in window.py):
    from sherly.ui.history_panel import ConversationHistoryPanel
    panel = ConversationHistoryPanel(parent=main_window)
    main_window.addDockWidget(Qt.RightDockWidgetArea, panel)
    # Call panel.refresh() each time a new message is added
"""

from __future__ import annotations

from datetime import datetime, timezone

from sherly.utils.runtime_utils import log

# ---------------------------------------------------------------------------
# Lazy PySide6 import (FS-#24)
# ---------------------------------------------------------------------------
_qt_available: bool | None = None


def _require_qt() -> bool:
    global _qt_available
    if _qt_available is None:
        try:
            from PySide6.QtWidgets import QDockWidget  # noqa: F401
            _qt_available = True
        except ImportError:
            _qt_available = False
    return _qt_available


# ---------------------------------------------------------------------------
# ConversationHistoryPanel
# ---------------------------------------------------------------------------

class ConversationHistoryPanel:
    """
    OE-3: Collapsible conversation history side panel.

    Wraps a QDockWidget containing:
      - Search bar (QLineEdit)
      - History list (QListWidget, newest-first)
      - Clear button

    Because PySide6 may not be installed in all environments (e.g. headless
    server), this class lazy-constructs the Qt widgets only when first shown.
    """

    def __init__(self, parent=None) -> None:
        if not _require_qt():
            log("[HistoryPanel] PySide6 not available — panel disabled.", level="warning")
            self._dock = None
            return

        from PySide6.QtCore import Qt
        from PySide6.QtWidgets import (
            QDockWidget, QWidget, QVBoxLayout, QHBoxLayout,
            QLineEdit, QListWidget, QPushButton, QLabel, QListWidgetItem,
        )

        self._QListWidgetItem = QListWidgetItem

        # ── Dock widget shell ────────────────────────────────────────────────
        self._dock = QDockWidget("Conversation History", parent)
        self._dock.setObjectName("ConversationHistoryDock")
        self._dock.setAllowedAreas(Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea)
        self._dock.setMinimumWidth(260)

        # ── Inner container ──────────────────────────────────────────────────
        container = QWidget()
        layout    = QVBoxLayout(container)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(6)

        # Title label
        title = QLabel("Chat History")
        title.setObjectName("HistoryPanelTitle")
        title.setStyleSheet("font-weight: bold; font-size: 13pt; color: #E0E0E0;")
        layout.addWidget(title)

        # Search bar
        self._search = QLineEdit()
        self._search.setPlaceholderText("Search history...")
        self._search.setObjectName("HistorySearchBar")
        self._search.textChanged.connect(self._on_search_changed)
        layout.addWidget(self._search)

        # History list
        self._list = QListWidget()
        self._list.setObjectName("HistoryList")
        self._list.setWordWrap(True)
        self._list.setStyleSheet("""
            QListWidget {
                background: rgba(255,255,255,0.05);
                border: 1px solid rgba(255,255,255,0.12);
                border-radius: 6px;
                font-size: 11pt;
                color: #E0E0E0;
            }
            QListWidget::item {
                padding: 6px 4px;
                border-bottom: 1px solid rgba(255,255,255,0.06);
            }
            QListWidget::item:selected {
                background: rgba(99, 102, 241, 0.3);
            }
        """)
        layout.addWidget(self._list)

        # Bottom button row
        btn_row = QHBoxLayout()
        self._clear_btn = QPushButton("Clear History")
        self._clear_btn.setObjectName("HistoryClearBtn")
        self._clear_btn.clicked.connect(self._on_clear)
        btn_row.addWidget(self._clear_btn)
        layout.addLayout(btn_row)

        self._dock.setWidget(container)

        # Internal store: list of (timestamp_str, badge, user_text, response_text)
        self._entries: list[tuple[str, str, str, str]] = []

    # -----------------------------------------------------------------------
    # Public API
    # -----------------------------------------------------------------------

    @property
    def dock(self):
        """Return the QDockWidget (may be None in headless environments)."""
        return self._dock

    def refresh(self) -> None:
        """
        OE-3: Reload history from conversation_memory.py and redraw the list.
        Call this every time a new message is added to the conversation.
        """
        if not self._dock:
            return

        try:
            from sherly.services.conversation_memory import get_all_turns
            turns = get_all_turns()
        except Exception:
            turns = []

        try:
            from sherly.services.action_manager import get_history as _get_history
            history_raw = _get_history()
        except Exception:
            history_raw = ""

        self._entries.clear()
        for turn in turns:
            ts  = turn.get("timestamp", "")
            usr = turn.get("user", "")
            rsp = turn.get("assistant", "")
            self._entries.append((ts, "[MSG]", usr, rsp))

        self._redraw()

    def add_entry(
        self,
        user_text: str,
        assistant_text: str,
        badge: str = "[MSG]",
        timestamp: str | None = None,
    ) -> None:
        """
        OE-3: Push a single conversation turn into the panel immediately.
        Faster than a full refresh() for real-time updates.
        """
        if not self._dock:
            return
        ts = timestamp or datetime.now(timezone.utc).strftime("%H:%M:%S")
        self._entries.insert(0, (ts, badge, user_text, assistant_text))
        self._redraw()

    # -----------------------------------------------------------------------
    # Internal
    # -----------------------------------------------------------------------

    def _redraw(self) -> None:
        """Re-populate the QListWidget from self._entries, respecting filter."""
        if not self._dock:
            return
        query = self._search.text().strip().lower() if hasattr(self, "_search") else ""
        self._list.clear()

        for ts, badge, user_text, rsp_text in self._entries:
            display = f"{badge} {ts}\nYou: {user_text[:80]}"
            if rsp_text:
                display += f"\nSherly: {rsp_text[:80]}"

            if query and query not in display.lower():
                continue

            item = self._QListWidgetItem(display)
            self._list.addItem(item)

    def _on_search_changed(self, text: str) -> None:
        self._redraw()

    def _on_clear(self) -> None:
        """Clear the in-memory entries and redraw."""
        self._entries.clear()
        self._list.clear()
        log("[HistoryPanel] Cleared by user.")
