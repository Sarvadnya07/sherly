"""
SIDEBAR COMPONENT — sherly_ui/sidebar.py
Left vertical icon navigation, Real Project Explorer file tree,
and bottom "Run project" action button.
"""

from __future__ import annotations

import os
from pathlib import Path
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QFrame, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QWidget, QTreeWidget, QTreeWidgetItem
)

from sherly_ui.theme import (
    C_BG_SIDEBAR, C_TEXT_PRIMARY, C_TEXT_MUTED, C_TEXT_DIM,
    C_PURPLE_MAIN, C_BORDER_SUBTLE
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
        self._active_tab = "workspace"
        self._buttons: dict[str, QPushButton] = {}
        self._setup_ui()
        self.refresh_project_tree()

    def _setup_ui(self) -> None:
        lay = QVBoxLayout(self)
        lay.setContentsMargins(12, 16, 12, 16)
        lay.setSpacing(12)

        # ── Project Title Header ──────────────────────────────────────────────
        proj_hdr = QFrame()
        proj_hdr.setStyleSheet("background: rgba(255,255,255,0.03); border-radius: 8px; padding: 6px 10px;")
        ph_lay = QVBoxLayout(proj_hdr)
        ph_lay.setContentsMargins(4, 4, 4, 4)
        ph_lay.setSpacing(2)

        p_lbl = QLabel("Project Explorer")
        p_lbl.setStyleSheet(f"color: {C_TEXT_PRIMARY}; font-size: 11px; font-weight: 700;")
        import sys
        p_sub = QLabel(f"Python {sys.version.split()[0]}")
        p_sub.setStyleSheet(f"color: {C_TEXT_MUTED}; font-size: 9px;")
        ph_lay.addWidget(p_lbl)
        ph_lay.addWidget(p_sub)
        lay.addWidget(proj_hdr)

        # ── Icon Navigation Bar ───────────────────────────────────────────────
        nav_box = QVBoxLayout()
        nav_box.setSpacing(4)

        tabs = [
            ("assistant", "💬 Assistant"),
            ("workspace", "📁 Workspace / Code"),
            ("models",    "⚙ Model Settings"),
            ("voice",     "🎙 Voice HUD"),
        ]

        for tab_id, label in tabs:
            btn = QPushButton(label)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setFixedHeight(34)
            btn.clicked.connect(lambda _, t=tab_id: self._select_tab(t))
            nav_box.addWidget(btn)
            self._buttons[tab_id] = btn

        lay.addLayout(nav_box)
        self._update_tab_styles()

        # ── Project Files Tree ────────────────────────────────────────────────
        files_hdr = QLabel("PROJECT FILES")
        files_hdr.setStyleSheet(f"color: {C_TEXT_DIM}; font-size: 9px; font-weight: 800; letter-spacing: 1.5px; margin-top: 6px;")
        lay.addWidget(files_hdr)

        self.tree = QTreeWidget()
        self.tree.setHeaderHidden(True)
        self.tree.setFrameShape(QFrame.Shape.NoFrame)
        self.tree.setStyleSheet(f"""
            QTreeWidget {{
                background: transparent;
                color: {C_TEXT_PRIMARY};
                font-size: 12px;
            }}
            QTreeWidget::item {{
                padding: 4px 6px;
                border-radius: 6px;
            }}
            QTreeWidget::item:hover {{
                background: rgba(255, 255, 255, 0.05);
            }}
            QTreeWidget::item:selected {{
                background: rgba(139, 92, 246, 0.2);
                color: #c4b5fd;
            }}
        """)
        self.tree.itemClicked.connect(self._on_tree_item_clicked)
        lay.addWidget(self.tree, stretch=1)

        # ── Run Project Bottom Action Button ──────────────────────────────────
        self.run_btn = QPushButton("▶ Run main.py")
        self.run_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.run_btn.setFixedHeight(38)
        self.run_btn.setStyleSheet(f"""
            QPushButton {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #8b5cf6, stop:1 #6d28d9);
                color: white;
                border: none;
                border-radius: 10px;
                font-size: 12px;
                font-weight: 700;
            }}
            QPushButton:hover {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #9d7aea, stop:1 #7c3aed);
            }}
            QPushButton:pressed {{
                background: #5b21b6;
            }}
        """)
        self.run_btn.clicked.connect(self.run_project.emit)
        lay.addWidget(self.run_btn)

    def refresh_project_tree(self) -> None:
        """Scan real project workspace directory and populate file tree."""
        self.tree.clear()
        root_dir = Path.cwd()

        # Folders/files to exclude from view
        exclude = {".git", ".pytest_cache", "__pycache__", ".ruff_cache", "venv", ".venv"}

        def populate_dir(parent_item: QTreeWidgetItem | QTreeWidget, dir_path: Path, max_depth: int = 2) -> None:
            if max_depth <= 0:
                return
            try:
                entries = sorted(list(dir_path.iterdir()), key=lambda p: (not p.is_dir(), p.name.lower()))
                for entry in entries:
                    if entry.name in exclude or entry.name.startswith("."):
                        continue
                    if entry.is_dir():
                        item = QTreeWidgetItem(parent_item, [f"📂 {entry.name}"])
                        item.setData(0, Qt.ItemDataRole.UserRole, str(entry))
                        populate_dir(item, entry, max_depth - 1)
                    else:
                        ext = entry.suffix.lower()
                        icon = "🐍" if ext == ".py" else ("📄" if ext in (".json", ".txt", ".md") else "📜")
                        item = QTreeWidgetItem(parent_item, [f"{icon} {entry.name}"])
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
                        background: rgba(139, 92, 246, 0.18);
                        color: #a78bfa;
                        border: 1px solid rgba(139, 92, 246, 0.4);
                        border-radius: 8px;
                        text-align: left;
                        padding-left: 12px;
                        font-size: 11px;
                        font-weight: 700;
                    }}
                """)
            else:
                btn.setStyleSheet(f"""
                    QPushButton {{
                        background: transparent;
                        color: {C_TEXT_MUTED};
                        border: 1px solid transparent;
                        border-radius: 8px;
                        text-align: left;
                        padding-left: 12px;
                        font-size: 11px;
                    }}
                    QPushButton:hover {{
                        background: rgba(255, 255, 255, 0.04);
                        color: {C_TEXT_PRIMARY};
                    }}
                """)
