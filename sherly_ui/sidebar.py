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
    C_ACCENT_PRIMARY, C_ACCENT_HOVER, C_ACCENT_LIGHT, C_ACCENT_SURFACE, C_ACCENT_GLOW,
    C_PURPLE_DARK, C_BORDER_SUBTLE, C_BORDER_MEDIUM, C_BORDER_ACCENT, C_GREEN_SUCCESS,
    FONT_FAMILY_UI, FONT_FAMILY_CODE, get_ui_font, get_code_font
)


class Sidebar(QFrame):
    """Sidebar navigation & real workspace file explorer panel."""

    view_changed  = Signal(str)      # Emits view ID: "assistant", "workspace", "models", "voice"
    file_selected = Signal(str)      # Emits path of clicked file
    run_project   = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setFixedWidth(240)
        self.setObjectName("Sidebar")
        self.setStyleSheet(f"""
            #Sidebar {{
                background: {C_BG_SIDEBAR};
                border-right: 1px solid {C_BORDER_SUBTLE};
            }}
        """)
        self._active_tab = "workspace"
        self._buttons: dict[str, QPushButton] = {}
        self._setup_ui()
        self.refresh_project_tree()

    def _setup_ui(self) -> None:
        lay = QVBoxLayout(self)
        lay.setContentsMargins(12, 14, 12, 14)
        lay.setSpacing(10)

        # ── Workspace Header ──────────────────────────────────────────────────
        proj_hdr = QFrame()
        proj_hdr.setStyleSheet(f"""
            QFrame {{
                background: {C_BG_CARD};
                border: 1px solid {C_BORDER_SUBTLE};
                border-radius: 8px;
                padding: 6px 10px;
            }}
        """)
        ph_lay = QVBoxLayout(proj_hdr)
        ph_lay.setContentsMargins(4, 4, 4, 4)
        ph_lay.setSpacing(2)

        top_row = QHBoxLayout()
        top_row.setSpacing(6)
        dot = QLabel("●")
        dot.setFont(get_ui_font(7, QFont.Weight.Bold))
        dot.setStyleSheet(f"color: {C_GREEN_SUCCESS};")
        
        p_lbl = QLabel("PROJECT WORKSPACE")
        p_lbl.setFont(get_ui_font(8, QFont.Weight.Bold))
        p_lbl.setStyleSheet(f"color: {C_TEXT_MUTED}; letter-spacing: 1px;")
        top_row.addWidget(dot)
        top_row.addWidget(p_lbl)
        top_row.addStretch()
        ph_lay.addLayout(top_row)

        import sys
        p_sub = QLabel(f"Python {sys.version.split()[0]} • Sherly Workspace")
        p_sub.setFont(get_code_font(8, QFont.Weight.Medium))
        p_sub.setStyleSheet(f"color: {C_TEXT_SECONDARY}; padding-left: 2px;")
        ph_lay.addWidget(p_sub)

        lay.addWidget(proj_hdr)

        # ── Group 1: Workspace Navigation ────────────────────────────────────
        ws_hdr = QLabel("WORKSPACE")
        ws_hdr.setFont(get_ui_font(8, QFont.Weight.Bold))
        ws_hdr.setStyleSheet(f"color: {C_TEXT_DIM}; letter-spacing: 1.2px; margin-top: 4px;")
        lay.addWidget(ws_hdr)

        ws_tabs = [
            ("assistant", "Assistant", "💬"),
            ("workspace", "Code Workspace", "📁"),
        ]

        for tab_id, label, icon_str in ws_tabs:
            btn = QPushButton(f"  {icon_str}  {label}")
            btn.setFont(get_ui_font(9, QFont.Weight.Medium))
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setFixedHeight(34)
            btn.clicked.connect(lambda _, t=tab_id: self._select_tab(t))
            lay.addWidget(btn)
            self._buttons[tab_id] = btn

        # ── Group 2: Runtime & System Navigation ──────────────────────────────
        sys_hdr = QLabel("RUNTIME & SYSTEM")
        sys_hdr.setFont(get_ui_font(8, QFont.Weight.Bold))
        sys_hdr.setStyleSheet(f"color: {C_TEXT_DIM}; letter-spacing: 1.2px; margin-top: 6px;")
        lay.addWidget(sys_hdr)

        sys_tabs = [
            ("models", "Model Settings", "⚙"),
            ("voice",  "Voice HUD", "🎙"),
        ]

        for tab_id, label, icon_str in sys_tabs:
            btn = QPushButton(f"  {icon_str}  {label}")
            btn.setFont(get_ui_font(9, QFont.Weight.Medium))
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setFixedHeight(34)
            btn.clicked.connect(lambda _, t=tab_id: self._select_tab(t))
            lay.addWidget(btn)
            self._buttons[tab_id] = btn

        self._update_tab_styles()

        # ── Project Files Tree ────────────────────────────────────────────────
        files_hdr = QLabel("PROJECT FILES")
        files_hdr.setFont(get_ui_font(8, QFont.Weight.Bold))
        files_hdr.setStyleSheet(f"color: {C_TEXT_DIM}; letter-spacing: 1.2px; margin-top: 8px;")
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
                padding: 4px 6px;
                border-radius: 4px;
            }}
            QTreeWidget::item:hover {{
                background: rgba(255, 255, 255, 0.05);
                color: {C_TEXT_PRIMARY};
            }}
            QTreeWidget::item:selected {{
                background: {C_ACCENT_SURFACE};
                color: {C_ACCENT_LIGHT};
                border-left: 2px solid {C_ACCENT_PRIMARY};
            }}
        """)
        self.tree.itemClicked.connect(self._on_tree_item_clicked)
        lay.addWidget(self.tree, stretch=1)

        # ── Run Project Bottom Action Button ──────────────────────────────────
        self.run_btn = QPushButton("▶  Run main.py")
        self.run_btn.setFont(get_ui_font(9, QFont.Weight.Bold))
        self.run_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.run_btn.setFixedHeight(36)
        self.run_btn.setStyleSheet(f"""
            QPushButton {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 {C_ACCENT_PRIMARY}, stop:1 #9333ea);
                color: #ffffff;
                border: 1px solid rgba(255, 255, 255, 0.15);
                border-radius: 8px;
            }}
            QPushButton:hover {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 {C_ACCENT_HOVER}, stop:1 #a855f7);
            }}
            QPushButton:pressed {{
                background: {C_PURPLE_DARK};
            }}
        """)
        self.run_btn.clicked.connect(self.run_project.emit)
        lay.addWidget(self.run_btn)

    def set_active_view(self, view_id: str) -> None:
        """Programmatically set active view highlight without emitting signal."""
        if view_id in self._buttons:
            self._active_tab = view_id
            self._update_tab_styles()

    def refresh_project_tree(self) -> None:
        """Scan real project workspace directory and populate file tree."""
        self.tree.clear()
        root_dir = Path.cwd()

        # Folders/files to exclude from view
        exclude = {".git", ".pytest_cache", "__pycache__", ".ruff_cache", "venv", ".venv", "dist", "node_modules"}

        def populate_dir(parent_item: QTreeWidgetItem | QTreeWidget, dir_path: Path, max_depth: int = 3) -> None:
            if max_depth <= 0:
                return
            try:
                entries = sorted(list(dir_path.iterdir()), key=lambda p: (not p.is_dir(), p.name.lower()))
                for entry in entries:
                    if entry.name in exclude or entry.name.startswith("."):
                        continue
                    if entry.is_dir():
                        item = QTreeWidgetItem(parent_item, [f"▸ {entry.name}"])
                        item.setData(0, Qt.ItemDataRole.UserRole, str(entry))
                        populate_dir(item, entry, max_depth - 1)
                    else:
                        ext = entry.suffix.lower()
                        prefix = "[py]" if ext == ".py" else ("[ts]" if ext in (".ts", ".tsx") else ("[cfg]" if ext in (".json", ".toml", ".yaml", ".env") else " • "))
                        item = QTreeWidgetItem(parent_item, [f"{prefix} {entry.name}"])
                        item.setData(0, Qt.ItemDataRole.UserRole, str(entry))
            except Exception:
                pass

        populate_dir(self.tree, root_dir)

    def _on_tree_item_clicked(self, item: QTreeWidgetItem, column: int) -> None:
        path_str = item.data(0, Qt.ItemDataRole.UserRole)
        if path_str and Path(path_str).is_file():
            self._select_tab("workspace")
            self.file_selected.emit(path_str)

    def _select_tab(self, tab_id: str) -> None:
        self._active_tab = tab_id
        self._update_tab_styles()
        self.view_changed.emit(tab_id)

    def _update_tab_styles(self) -> None:
        for tid, btn in self._buttons.items():
            if tid == self._active_tab:
                btn.setStyleSheet(f"""
                    QPushButton {{
                        background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 rgba(124, 58, 237, 0.28), stop:1 rgba(124, 58, 237, 0.08));
                        color: #ffffff;
                        border: 1px solid {C_BORDER_ACCENT};
                        border-left: 3px solid {C_ACCENT_PRIMARY};
                        border-radius: 6px;
                        text-align: left;
                        padding-left: 10px;
                        font-weight: 600;
                    }}
                """)
            else:
                btn.setStyleSheet(f"""
                    QPushButton {{
                        background: transparent;
                        color: {C_TEXT_SECONDARY};
                        border: 1px solid transparent;
                        border-radius: 6px;
                        text-align: left;
                        padding-left: 10px;
                    }}
                    QPushButton:hover {{
                        background: rgba(255, 255, 255, 0.05);
                        color: {C_TEXT_PRIMARY};
                    }}
                """)


