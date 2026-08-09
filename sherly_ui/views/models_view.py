"""
MODEL MANAGEMENT VIEW — sherly_ui/views/models_view.py
Dynamic Model Repository & Inspector.
Displays ONLY models actually detected by Ollama or configured remote APIs.
Full real-time binding to model_scanner, model_resolver, config_manager, and model_manager.
"""

from __future__ import annotations

import logging
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QFrame, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QCheckBox,
    QProgressBar, QWidget, QScrollArea, QInputDialog, QLineEdit, QMessageBox
)

from sherly_ui.theme import (
    C_BG_PANEL, C_BG_CARD, C_TEXT_PRIMARY, C_TEXT_MUTED, C_TEXT_DIM,
    C_PURPLE_MAIN, C_GREEN_SUCCESS, C_BORDER_SUBTLE, C_RED_DANGER
)
import config_manager
import model_scanner
import model_manager
from sherly_core.model_resolver import resolve_model

logger = logging.getLogger(__name__)


class ModelCardWidget(QFrame):
    """Real dynamic model repository card."""

    select_clicked = Signal(str)
    unload_clicked = Signal(str)

    def __init__(self, model_info: dict, is_active: bool = False, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.model_name = model_info.get("name", "Unknown")
        self.model_info = model_info
        self.is_active = is_active
        self.setObjectName("ModelCard")

        border_color = "rgba(139, 92, 246, 0.6)" if is_active else C_BORDER_SUBTLE
        bg_color = "rgba(139, 92, 246, 0.08)" if is_active else C_BG_CARD
        self.setStyleSheet(f"""
            #ModelCard {{
                background: {bg_color};
                border: 1px solid {border_color};
                border-radius: 12px;
            }}
        """)
        self._setup_ui()

    def _setup_ui(self) -> None:
        lay = QVBoxLayout(self)
        lay.setContentsMargins(14, 12, 14, 12)
        lay.setSpacing(10)

        # Header Row
        hdr = QHBoxLayout()
        icon = QLabel("⚡" if self.is_active else "📦")
        hdr.addWidget(icon)

        t_col = QVBoxLayout()
        t_col.setSpacing(1)
        t_lbl = QLabel(self.model_name)
        t_lbl.setStyleSheet(f"color: {C_TEXT_PRIMARY}; font-size: 13px; font-weight: 700;")

        size_mb = self.model_info.get("size", 0) / (1024 * 1024 * 1024)
        subtitle = f"Local • {size_mb:.1f} GB" if size_mb > 0 else "Local Model"
        s_lbl = QLabel(subtitle)
        s_lbl.setStyleSheet(f"color: {C_TEXT_MUTED}; font-size: 10px;")
        t_col.addWidget(t_lbl)
        t_col.addWidget(s_lbl)
        hdr.addLayout(t_col)
        hdr.addStretch()
        lay.addLayout(hdr)

        # Tags Row (Derived dynamically)
        tags_row = QHBoxLayout()
        tags_row.setSpacing(6)
        tags = []
        if self.model_info.get("coding"):
            tags.append("Code")
        tags.append(self.model_info.get("family", "Model").upper())
        tag = self.model_info.get("tag", "")
        if tag and tag != "latest":
            tags.append(tag)

        for t in tags:
            tag_lbl = QLabel(t)
            tag_lbl.setStyleSheet("background: rgba(255,255,255,0.05); color: #aaa; border-radius: 6px; padding: 2px 8px; font-size: 10px;")
            tags_row.addWidget(tag_lbl)
        tags_row.addStretch()
        lay.addLayout(tags_row)

        # Status & Action Row
        st_row = QHBoxLayout()
        if self.is_active:
            st_lbl = QLabel("🟢 Active / Running")
            st_lbl.setStyleSheet("color: #10b981; font-size: 11px; font-weight: 600;")
            st_row.addWidget(st_lbl)
            st_row.addStretch()

            act_btn = QPushButton("Unload")
            act_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            act_btn.setStyleSheet("background: transparent; color: #888; border: none; font-size: 11px;")
            act_btn.clicked.connect(lambda: self.unload_clicked.emit(self.model_name))
            st_row.addWidget(act_btn)
        else:
            st_lbl = QLabel("📦 Installed")
            st_lbl.setStyleSheet(f"color: {C_TEXT_MUTED}; font-size: 11px;")
            st_row.addWidget(st_lbl)
            st_row.addStretch()

            act_btn = QPushButton("Set Active")
            act_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            act_btn.setStyleSheet("background: rgba(139, 92, 246, 0.2); color: #c4b5fd; border: 1px solid rgba(139, 92, 246, 0.4); border-radius: 6px; padding: 3px 12px; font-size: 11px; font-weight: 600;")
            act_btn.clicked.connect(lambda: self.select_clicked.emit(self.model_name))
            st_row.addWidget(act_btn)

        lay.addLayout(st_row)


class ModelsView(QFrame):
    """Dynamic Model Management View."""

    model_changed = Signal(str)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("ModelsView")
        self.setStyleSheet(f"""
            #ModelsView {{
                background: {C_BG_PANEL};
            }}
        """)
        self._setup_ui()
        self.refresh_models()

    def _setup_ui(self) -> None:
        main_lay = QHBoxLayout(self)
        main_lay.setContentsMargins(0, 0, 0, 0)
        main_lay.setSpacing(0)

        # ── Left Repository Section ───────────────────────────────────────────
        repo_sec = QWidget()
        r_lay = QVBoxLayout(repo_sec)
        r_lay.setContentsMargins(20, 20, 20, 20)
        r_lay.setSpacing(16)

        # Repository Header & Controls
        hdr_row = QHBoxLayout()
        rh_col = QVBoxLayout()
        rh_col.setSpacing(2)
        r_title = QLabel("Model Repository")
        r_title.setStyleSheet(f"color: {C_TEXT_PRIMARY}; font-size: 18px; font-weight: 700;")
        r_sub = QLabel("Manage local Ollama models and remote API endpoints.")
        r_sub.setStyleSheet(f"color: {C_TEXT_MUTED}; font-size: 11px;")
        rh_col.addWidget(r_title)
        rh_col.addWidget(r_sub)
        hdr_row.addLayout(rh_col)
        hdr_row.addStretch()

        self.auto_cb = QCheckBox("Auto Model Detection")
        self.auto_cb.setChecked(config_manager.get_model_mode() == "auto")
        self.auto_cb.setStyleSheet("color: #a78bfa; font-size: 11px; font-weight: 600;")
        self.auto_cb.toggled.connect(self._on_auto_toggle)
        hdr_row.addWidget(self.auto_cb)

        refresh_btn = QPushButton("↻ Refresh")
        refresh_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        refresh_btn.setStyleSheet("background: rgba(255,255,255,0.06); color: #fff; border-radius: 8px; padding: 6px 12px; font-size: 11px;")
        refresh_btn.clicked.connect(self.refresh_models)
        hdr_row.addWidget(refresh_btn)

        r_lay.addLayout(hdr_row)

        # Scroll Area for Model Cards
        self.repo_scroll = QScrollArea()
        self.repo_scroll.setWidgetResizable(True)
        self.repo_scroll.setFrameShape(QFrame.Shape.NoFrame)

        self.cards_container = QWidget()
        self.cards_layout = QVBoxLayout(self.cards_container)
        self.cards_layout.setContentsMargins(0, 0, 0, 0)
        self.cards_layout.setSpacing(12)
        self.cards_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        self.repo_scroll.setWidget(self.cards_container)
        r_lay.addWidget(self.repo_scroll, stretch=1)

        # Remote Providers Section
        rem_lbl = QLabel("Remote API Providers")
        rem_lbl.setStyleSheet(f"color: {C_TEXT_PRIMARY}; font-size: 13px; font-weight: 700; margin-top: 8px;")
        r_lay.addWidget(rem_lbl)

        self.remote_box = QVBoxLayout()
        self.remote_box.setSpacing(8)
        r_lay.addLayout(self.remote_box)

        main_lay.addWidget(repo_sec, stretch=6)

        # ── Right Inspector Panel ─────────────────────────────────────────────
        self.insp_panel = QFrame()
        self.insp_panel.setFixedWidth(300)
        self.insp_panel.setStyleSheet(f"background: #0b0b11; border-left: 1px solid {C_BORDER_SUBTLE};")
        self.i_lay = QVBoxLayout(self.insp_panel)
        self.i_lay.setContentsMargins(18, 20, 18, 20)
        self.i_lay.setSpacing(14)

        main_lay.addWidget(self.insp_panel, stretch=4)

    def refresh_models(self) -> None:
        """Scan real local models from Ollama and rebuild cards dynamically."""
        # Clear existing cards
        while self.cards_layout.count():
            item = self.cards_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        # Clear remote providers
        while self.remote_box.count():
            item = self.remote_box.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        # Get active model from config/resolver
        current_active = config_manager.get_current_model()

        # Scan real Ollama models
        models = model_scanner.scan_ollama_models()

        if not models:
            no_model_card = QFrame()
            no_model_card.setStyleSheet(f"background: {C_BG_CARD}; border: 1px dashed rgba(255,255,255,0.15); border-radius: 12px; padding: 16px;")
            nm_lay = QVBoxLayout(no_model_card)
            nm_lay.setAlignment(Qt.AlignmentFlag.AlignCenter)
            nm_lbl = QLabel("⚠️ No Local Ollama Models Detected")
            nm_lbl.setStyleSheet(f"color: {C_TEXT_PRIMARY}; font-size: 13px; font-weight: 700;")
            nm_sub = QLabel("Ensure Ollama is running and run 'ollama pull qwen2.5-coder:3b' in terminal.")
            nm_sub.setWordWrap(True)
            nm_sub.setAlignment(Qt.AlignmentFlag.AlignCenter)
            nm_sub.setStyleSheet(f"color: {C_TEXT_MUTED}; font-size: 11px;")
            nm_lay.addWidget(nm_lbl)
            nm_lay.addWidget(nm_sub)
            self.cards_layout.addWidget(no_model_card)
        else:
            local_hdr = QLabel(f"Local Models ({len(models)})")
            local_hdr.setStyleSheet(f"color: {C_TEXT_MUTED}; font-size: 10px; font-weight: 800; letter-spacing: 1px;")
            self.cards_layout.addWidget(local_hdr)

            for m in models:
                name = m.get("name", "")
                is_act = (name == current_active)
                card = ModelCardWidget(m, is_active=is_act)
                card.select_clicked.connect(self._on_select_model)
                card.unload_clicked.connect(self._on_unload_model)
                self.cards_layout.addWidget(card)

        # Build Real Remote Providers
        for prov in ["openai", "gemini", "groq"]:
            key = config_manager.get_api_key(prov)
            is_cfg = bool(key and key != f"YOUR_{prov.upper()}_KEY")

            rem_frame = QFrame()
            rem_frame.setStyleSheet(f"background: {C_BG_CARD}; border-radius: 10px; padding: 10px 14px;")
            rf_lay = QHBoxLayout(rem_frame)
            rf_lay.addWidget(QLabel(f"❖ {prov.capitalize()} (API)", styleSheet=f"color: {C_TEXT_PRIMARY}; font-size: 12px; font-weight: 600;"))
            rf_lay.addStretch()

            if is_cfg:
                rf_lay.addWidget(QLabel("Configured", styleSheet="color: #10b981; font-size: 11px; font-weight: 600;"))
                btn = QPushButton("Edit")
            else:
                rf_lay.addWidget(QLabel("No Key", styleSheet=f"color: {C_TEXT_MUTED}; font-size: 11px;"))
                btn = QPushButton("Connect")

            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setStyleSheet("background: rgba(255,255,255,0.08); color: #fff; border-radius: 6px; padding: 3px 10px; font-size: 11px;")
            _prov = prov
            btn.clicked.connect(lambda _, p=_prov: self._configure_api_key(p))
            rf_lay.addWidget(btn)

            self.remote_box.addWidget(rem_frame)

        # Update Right Inspector
        self._update_inspector(models, current_active)

    def _update_inspector(self, models: list[dict], active_name: str | None) -> None:
        """Update right inspector with real active model info."""
        while self.i_lay.count():
            item = self.i_lay.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        i_hdr = QLabel("ⓘ Model Inspector")
        i_hdr.setStyleSheet(f"color: {C_TEXT_PRIMARY}; font-size: 14px; font-weight: 700;")
        self.i_lay.addWidget(i_hdr)

        active_info = next((m for m in models if m.get("name") == active_name), None)

        if not active_info and models:
            active_info = models[0]

        if active_info:
            name = active_info.get("name", "Unknown")
            family = active_info.get("family", "Model")
            size_gb = active_info.get("size", 0) / (1024 * 1024 * 1024)

            i_title = QLabel(name)
            i_title.setStyleSheet("color: #a78bfa; font-size: 15px; font-weight: 700;")
            i_desc = QLabel(f"Local {family} model optimized for fast execution.")
            i_desc.setWordWrap(True)
            i_desc.setStyleSheet(f"color: {C_TEXT_MUTED}; font-size: 11px; line-height: 1.3;")
            self.i_lay.addWidget(i_title)
            self.i_lay.addWidget(i_desc)

            # Capabilities Grid
            cap_lbl = QLabel("CAPABILITIES")
            cap_lbl.setStyleSheet(f"color: {C_TEXT_DIM}; font-size: 9px; font-weight: 800; letter-spacing: 1.5px; margin-top: 6px;")
            self.i_lay.addWidget(cap_lbl)

            cap_grid = QWidget()
            cg_lay = QVBoxLayout(cap_grid)
            cg_lay.setContentsMargins(0, 0, 0, 0)
            cg_lay.setSpacing(6)

            is_coding = active_info.get("coding", False)
            row1 = QHBoxLayout()
            row1.addWidget(self._cap_box("💻 Code Gen", active=is_coding))
            row1.addWidget(self._cap_box("👁 Vision", active=False))
            cg_lay.addLayout(row1)

            row2 = QHBoxLayout()
            row2.addWidget(self._cap_box("🧠 Reasoning", active=True))
            row2.addWidget(self._cap_box("💬 Instruct", active=True))
            cg_lay.addLayout(row2)
            self.i_lay.addWidget(cap_grid)

            # Resource Allocation
            res_lbl = QLabel("RESOURCE ALLOCATION")
            res_lbl.setStyleSheet(f"color: {C_TEXT_DIM}; font-size: 9px; font-weight: 800; letter-spacing: 1.5px; margin-top: 6px;")
            self.i_lay.addWidget(res_lbl)

            ram_val = f"{size_gb:.1f} GB" if size_gb > 0 else "Dynamic"
            ram_row = QHBoxLayout()
            ram_row.addWidget(QLabel("Disk Size", styleSheet=f"color: {C_TEXT_MUTED}; font-size: 11px;"))
            ram_row.addStretch()
            ram_row.addWidget(QLabel(ram_val, styleSheet=f"color: {C_TEXT_PRIMARY}; font-size: 11px; font-weight: 600;"))
            self.i_lay.addLayout(ram_row)

            for label, val in [("Host", "http://127.0.0.1:11434"), ("Provider", "Ollama Local")]:
                r_row = QHBoxLayout()
                r_row.addWidget(QLabel(label, styleSheet=f"color: {C_TEXT_MUTED}; font-size: 11px;"))
                r_row.addStretch()
                r_row.addWidget(QLabel(val, styleSheet=f"color: {C_TEXT_PRIMARY}; font-size: 11px; font-weight: 600;"))
                self.i_lay.addLayout(r_row)

        else:
            i_title = QLabel("No Model Active")
            i_title.setStyleSheet(f"color: {C_TEXT_MUTED}; font-size: 13px;")
            self.i_lay.addWidget(i_title)

        self.i_lay.addStretch()

    def _cap_box(self, text: str, active: bool = True) -> QFrame:
        box = QFrame()
        box.setStyleSheet(f"""
            background: {"rgba(139, 92, 246, 0.12)" if active else "rgba(255,255,255,0.03)"};
            border: 1px solid {"rgba(139, 92, 246, 0.3)" if active else "rgba(255,255,255,0.05)"};
            border-radius: 8px; padding: 6px;
        """)
        b_lay = QVBoxLayout(box)
        b_lay.setContentsMargins(6, 6, 6, 6)
        lbl = QLabel(text)
        lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl.setStyleSheet(f"color: {'#c4b5fd' if active else '#555'}; font-size: 10px; font-weight: {'600' if active else '400'};")
        b_lay.addWidget(lbl)
        return box

    def _on_select_model(self, name: str) -> None:
        config_manager.set_current_model(name)
        self.refresh_models()
        self.model_changed.emit(name)

    def _on_unload_model(self, name: str) -> None:
        model_manager.unload_model()
        self.refresh_models()

    def _on_auto_toggle(self, checked: bool) -> None:
        if checked:
            config_manager.enable_auto_detection()
            resolve_model(config_manager, model_scanner)
        else:
            config_manager.set_model_mode("manual")
        self.refresh_models()

    def _configure_api_key(self, provider: str) -> None:
        current = config_manager.get_api_key(provider) or ""
        key, ok = QInputDialog.getText(
            self, f"Configure {provider.capitalize()} API Key",
            f"Enter your {provider.capitalize()} API Key:",
            QLineEdit.EchoMode.Password, current
        )
        if ok and key:
            config_manager.set_api_key(provider, key.strip())
            self.refresh_models()
