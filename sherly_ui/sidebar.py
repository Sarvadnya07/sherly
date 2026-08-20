"""
SIDEBAR COMPONENT — sherly_ui/sidebar.py
Left vertical navigation, grouped workspace tabs, project explorer file tree,
and bottom "Run main.py" action button.
"""

from __future__ import annotations

import os
from pathlib import Path
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont, QColor
from PySide6.QtWidgets import (
    QFrame, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QWidget, QTreeWidget, QTreeWidgetItem
)

from sherly_ui.theme import (
    C_BG_SIDEBAR, C_BG_CARD, C_TEXT_PRIMARY, C_TEXT_SECONDARY, C_TEXT_MUTED, C_TEXT_DIM,
    C_ACCENT_PRIMARY, C_ACCENT_HOVER, C_ACCENT_LIGHT, C_BORDER_SUBTLE, C_BORDER_MEDIUM,
    C_GREEN_SUCCESS, get_ui_font, get_code_font
)


class Sidebar(QFrame):
    """Sidebar navigation & real workspace file explorer panel."""

    view_changed  = Signal(str)      # Emits view ID: "assistant", "workspace", "models", "voice"
    file_selected = Signal(str)      # Emits path of clicked file
    run_project   = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setFixedWidth(220)
        self.setObjectName("Sidebar")
        self.setStyleSheet(f"""
            #Sidebar {{
                background: {C_BG_SIDEBAR};
                border-right: 1px solid {C_BORDER_SUBTLE};
            }}
        """)
        self._active_tab = "assistant"
        self._buttons: dict[str, QPushButton] = {}
        self._setup_ui()
        self.refresh_project_tree()

    def _setup_ui(self) -> None:
        lay = QVBoxLayout(self)
        lay.setContentsMargins(10, 12, 10, 12)
        lay.setSpacing(8)

        # ── Workspace Header ──────────────────────────────────────────────────
        proj_hdr = QFrame()
        proj_hdr.setStyleSheet("""
            QFrame {
                background: rgba(255, 255, 255, 0.03);
                border: 1px solid rgba(255, 255, 255, 0.06);
                border-radius: 6px;
                padding: 4px 8px;
            }
        """)
        ph_lay = QHBoxLayout(proj_hdr)
        ph_lay.setContentsMargins(4, 2, 4, 2)
        ph_lay.setSpacing(6)

        dot = QLabel("●")
        dot.setFont(get_ui_font(7, QFont.Weight.Bold))
        dot.setStyleSheet(f"color: {C_GREEN_SUCCESS};")
        ph_lay.addWidget(dot)

        p_lbl = QLabel("Sherly Workspace")
        p_lbl.setFont(get_ui_font(9, QFont.Weight.Medium))
        p_lbl.setStyleSheet(f"color: {C_TEXT_PRIMARY};")
        ph_lay.addWidget(p_lbl)
        ph_lay.addStretch()

        ver_lbl = QLabel("v2.0")
        ver_lbl.setFont(get_code_font(8, QFont.Weight.Normal))
        ver_lbl.setStyleSheet(f"color: {C_TEXT_MUTED};")
        ph_lay.addWidget(ver_lbl)

        lay.addWidget(proj_hdr)

        # ── Group 1: Workspace Navigation ────────────────────────────────────
        ws_hdr = QLabel("WORKSPACE")
        ws_hdr.setFont(get_ui_font(8, QFont.Weight.Bold))
        ws_hdr.setStyleSheet(f"color: {C_TEXT_DIM}; letter-spacing: 1px; margin-top: 4px; padding-left: 4px;")
        lay.addWidget(ws_hdr)

        ws_tabs = [
            ("assistant", "Assistant"),
            ("workspace", "Code Workspace"),
        ]

        for tab_id, label in ws_tabs:
            btn = QPushButton(f"  {label}")
            btn.setFont(get_ui_font(9, QFont.Weight.Medium))
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setFixedHeight(30)
            btn.clicked.connect(lambda _, t=tab_id: self._select_tab(t))
            lay.addWidget(btn)
            self._buttons[tab_id] = btn

        # ── Group 2: Runtime & System Navigation ──────────────────────────────
        sys_hdr = QLabel("SYSTEM")
        sys_hdr.setFont(get_ui_font(8, QFont.Weight.Bold))
        sys_hdr.setStyleSheet(f"color: {C_TEXT_DIM}; letter-spacing: 1px; margin-top: 6px; padding-left: 4px;")
        lay.addWidget(sys_hdr)

        sys_tabs = [
            ("models", "Model Settings"),
            ("voice",  "Voice HUD"),
        ]

        for tab_id, label in sys_tabs:
            btn = QPushButton(f"  {label}")
            btn.setFont(get_ui_font(9, QFont.Weight.Medium))
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setFixedHeight(30)
            btn.clicked.connect(lambda _, t=tab_id: self._select_tab(t))
            lay.addWidget(btn)
            self._buttons[tab_id] = btn

        self._update_tab_styles()

        # ── Project Files Tree ────────────────────────────────────────────────
        files_hdr = QLabel("EXPLORER")
        files_hdr.setFont(get_ui_font(8, QFont.Weight.Bold))
        files_hdr.setStyleSheet(f"color: {C_TEXT_DIM}; letter-spacing: 1px; margin-top: 8px; padding-left: 4px;")
        lay.addWidget(files_hdr)

        self.tree = QTreeWidget()
        self.tree.setHeaderHidden(True)
        self.tree.setFrameShape(QFrame.Shape.NoFrame)
        self.tree.setFont(get_code_font(9, QFont.Weight.Normal))
        self.tree.setStyleSheet(f"""
            QTreeWidget {{
                background: transparent;
                color: {C_TEXT_SECONDARY};
                border: none;
            }}
            QTreeWidget::item {{
                padding: 3px 4px;
                border-radius: 4px;
            }}
            QTreeWidget::item:hover {{
                background: rgba(255, 255, 255, 0.05);
                color: {C_TEXT_PRIMARY};
            }}
            QTreeWidget::item:selected {{
                background: #27272a;
                color: #ffffff;
            }}
        """)
        self.tree.itemClicked.connect(self._on_tree_item_clicked)
        lay.addWidget(self.tree, stretch=1)

        # ── Run Action Button ─────────────────────────────────────────────────
        self.run_btn = QPushButton("▶  Run main.py")
        self.run_btn.setFont(get_ui_font(9, QFont.Weight.DemiBold))
        self.run_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.run_btn.setFixedHeight(32)
        self.run_btn.setStyleSheet("""
            QPushButton {
                background: #27272a;
                color: #f4f4f5;
                border: 1px solid rgba(255, 255, 255, 0.08);
                border-radius: 6px;
            }
            QPushButton:hover {
                background: #3f3f46;
                color: #ffffff;
                border: 1px solid rgba(255, 255, 255, 0.14);
            }
            QPushButton:pressed {
                background: #18181b;
            }
        """)
        self.run_btn.clicked.connect(self._handle_run_clicked)
        lay.addWidget(self.run_btn)

    def set_active_view(self, tab_id: str) -> None:
        self._active_tab = tab_id
        self._update_tab_styles()

    def _select_tab(self, tab_id: str) -> None:
        if self._active_tab != tab_id:
            self._active_tab = tab_id
            self._update_tab_styles()
            self.view_changed.emit(tab_id)

    def _update_tab_styles(self) -> None:
        for tab_id, btn in self._buttons.items():
            if tab_id == self._active_tab:
                btn.setStyleSheet(f"""
                    QPushButton {{
                        background: #27272a;
                        color: #ffffff;
                        font-weight: 600;
                        border: 1px solid rgba(255, 255, 255, 0.08);
                        border-radius: 6px;
                        text-align: left;
                        padding-left: 8px;
                    }}
                """)
            else:
                btn.setStyleSheet(f"""
                    QPushButton {{
                        background: transparent;
                        color: {C_TEXT_SECONDARY};
                        border: none;
                        border-radius: 6px;
                        text-align: left;
                        padding-left: 8px;
                    }}
                    QPushButton:hover {{
                        background: rgba(255, 255, 255, 0.05);
                        color: {C_TEXT_PRIMARY};
                    }}
                """)

    def _handle_run_clicked(self) -> None:
        self._select_tab("workspace")
        self.run_project.emit()

    def refresh_project_tree(self) -> None:
        self.tree.clear()
        root_path = Path.cwd()
        root_item = QTreeWidgetItem([f"📁 {root_path.name}"])
        root_item.setData(0, Qt.ItemDataRole.UserRole, str(root_path))
        self.tree.addTopLevelItem(root_item)
        self._populate_tree(root_path, root_item)
        root_item.setExpanded(True)

    def _populate_tree(self, path: Path, parent_item: QTreeWidgetItem) -> None:
        try:
            entries = sorted(list(path.iterdir()), key=lambda p: (not p.is_dir(), p.name.lower()))
            for entry in entries:
                if entry.name.startswith((".", "__pycache__", "node_modules", "dist", "build", "venv", ".git")):
                    continue
                if entry.is_dir():
                    item = QTreeWidgetItem([f"📁 {entry.name}"])
                    item.setData(0, Qt.ItemDataRole.UserRole, str(entry))
                    parent_item.addChild(item)
                    if len(entry.name) < 20:
                        self._populate_tree(entry, item)
                else:
                    ext = entry.suffix.lower()
                    icon = "🐍" if ext == ".py" else ("📜" if ext in (".ts", ".js", ".json") else "📄")
                    item = QTreeWidgetItem([f"{icon} {entry.name}"])
                    item.setData(0, Qt.ItemDataRole.UserRole, str(entry))
                    parent_item.addChild(item)
        except PermissionError:
            pass

    def _on_tree_item_clicked(self, item: QTreeWidgetItem, column: int) -> None:
        path_str = item.data(0, Qt.ItemDataRole.UserRole)
        if path_str and Path(path_str).is_file():
            self._select_tab("workspace")
            self.file_selected.emit(path_str)
