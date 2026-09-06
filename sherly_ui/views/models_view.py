"""
MODEL MANAGEMENT & SETTINGS VIEW — sherly_ui/views/models_view.py
Dynamic Model Repository & Inspector.
Full real-time binding to model_scanner, model_resolver, config_manager, and model_manager.
"""

from __future__ import annotations

import logging

from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QCheckBox,
    QDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QProgressBar,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

import config_manager
import model_manager
import model_scanner
from sherly_core.model_resolver import resolve_model
from sherly_ui.theme import (
    C_ACCENT_HOVER,
    C_ACCENT_LIGHT,
    C_ACCENT_PRIMARY,
    C_ACCENT_SURFACE,
    C_BG_CANVAS,
    C_BG_CARD,
    C_BG_INPUT,
    C_BG_SURFACE,
    C_BORDER_ACCENT,
    C_BORDER_MEDIUM,
    C_BORDER_SUBTLE,
    C_GREEN_BG,
    C_GREEN_SUCCESS,
    C_TEXT_DIM,
    C_TEXT_MUTED,
    C_TEXT_PRIMARY,
    C_TEXT_SECONDARY,
    get_code_font,
    get_ui_font,
)

logger = logging.getLogger(__name__)


class ApiKeyModalDialog(QDialog):
    """Custom dark modal dialog for configuring API keys."""

    def __init__(self, provider: str, current_key: str = "", parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle(f"Configure {provider.capitalize()} API Key")
        self.setFixedSize(400, 200)
        self.setModal(True)
        self.setStyleSheet(f"""
            QDialog {{
                background: {C_BG_CARD};
                border: 1px solid {C_BORDER_MEDIUM};
                border-radius: 12px;
            }}
        """)
        self._provider = provider
        self._key_value = current_key
        self._setup_ui()

    def _setup_ui(self) -> None:
        lay = QVBoxLayout(self)
        lay.setContentsMargins(20, 20, 20, 20)
        lay.setSpacing(14)

        title = QLabel(f"Configure {self._provider.capitalize()} API Key")
        title.setFont(get_ui_font(12, QFont.Weight.Bold))
        title.setStyleSheet(f"color: {C_TEXT_PRIMARY}; border: none; background: transparent;")
        lay.addWidget(title)

        desc = QLabel(f"Enter your {self._provider.capitalize()} secret API key. It will be stored locally in your configuration.")
        desc.setFont(get_ui_font(9, QFont.Weight.Normal))
        desc.setWordWrap(True)
        desc.setStyleSheet(f"color: {C_TEXT_MUTED}; border: none; background: transparent;")
        lay.addWidget(desc)

        self.input_edit = QLineEdit(self._key_value)
        self.input_edit.setEchoMode(QLineEdit.EchoMode.Password)
        self.input_edit.setPlaceholderText("sk-...")
        self.input_edit.setFont(get_code_font(9, QFont.Weight.Normal))
        self.input_edit.setStyleSheet(f"""
            QLineEdit {{
                background: {C_BG_INPUT};
                color: {C_TEXT_PRIMARY};
                border: 1px solid {C_BORDER_MEDIUM};
                border-radius: 6px;
                padding: 8px 10px;
            }}
            QLineEdit:focus {{
                border-color: {C_ACCENT_PRIMARY};
            }}
        """)
        lay.addWidget(self.input_edit)

        # Actions
        btn_row = QHBoxLayout()
        btn_row.addStretch()

        cancel_btn = QPushButton("Cancel")
        cancel_btn.setFont(get_ui_font(9, QFont.Weight.Medium))
        cancel_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        cancel_btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                color: {C_TEXT_MUTED};
                border: 1px solid {C_BORDER_SUBTLE};
                border-radius: 6px;
                padding: 6px 14px;
            }}
            QPushButton:hover {{
                background: rgba(255, 255, 255, 0.06);
                color: {C_TEXT_PRIMARY};
            }}
        """)
        cancel_btn.clicked.connect(self.reject)
        btn_row.addWidget(cancel_btn)

        save_btn = QPushButton("Save Key")
        save_btn.setFont(get_ui_font(9, QFont.Weight.Bold))
        save_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        save_btn.setStyleSheet(f"""
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
        save_btn.clicked.connect(self.accept)
        btn_row.addWidget(save_btn)

        lay.addLayout(btn_row)

    def get_key(self) -> str:
        return self.input_edit.text().strip()


class ModelCardWidget(QFrame):
    """Dynamic model repository card."""

    select_clicked = Signal(str)
    unload_clicked = Signal(str)

    def __init__(self, model_info: dict, is_active: bool = False, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.model_name = model_info.get("name", "Unknown")
        self.model_info = model_info
        self.is_active = is_active
        self.setObjectName("ModelCard")

        border_color = C_BORDER_ACCENT if is_active else C_BORDER_SUBTLE
        bg_color = "qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 rgba(124, 58, 237, 0.16), stop:1 rgba(124, 58, 237, 0.03))" if is_active else C_BG_CARD
        self.setStyleSheet(f"""
            #ModelCard {{
                background: {bg_color};
                border: 1px solid {border_color};
                border-radius: 10px;
            }}
            #ModelCard:hover {{
                border-color: {C_BORDER_ACCENT if is_active else C_BORDER_MEDIUM};
            }}
        """)
        self._setup_ui()

    def _setup_ui(self) -> None:
        lay = QVBoxLayout(self)
        lay.setContentsMargins(16, 14, 16, 14)
        lay.setSpacing(10)

        # Header Row
        hdr = QHBoxLayout()
        t_col = QVBoxLayout()
        t_col.setSpacing(2)

        t_lbl = QLabel(self.model_name)
        t_lbl.setFont(get_ui_font(11, QFont.Weight.Bold))
        t_lbl.setStyleSheet(f"color: {C_TEXT_PRIMARY}; border: none; background: transparent;")

        size_mb = self.model_info.get("size", 0) / (1024 * 1024 * 1024)
        subtitle = f"Local LLM • {size_mb:.1f} GB VRAM Footprint" if size_mb > 0 else "Local LLM"
        s_lbl = QLabel(subtitle)
        s_lbl.setFont(get_code_font(8, QFont.Weight.Normal))
        s_lbl.setStyleSheet(f"color: {C_TEXT_MUTED}; border: none; background: transparent;")
        t_col.addWidget(t_lbl)
        t_col.addWidget(s_lbl)
        hdr.addLayout(t_col)
        hdr.addStretch()

        if self.is_active:
            act_badge = QFrame()
            act_badge.setStyleSheet(f"""
                background: {C_GREEN_BG};
                border: 1px solid rgba(16, 185, 129, 0.35);
                border-radius: 12px;
                padding: 2px 8px;
            """)
            ab_lay = QHBoxLayout(act_badge)
            ab_lay.setContentsMargins(4, 2, 4, 2)
            ab_lay.setSpacing(5)
            dot = QLabel("●")
            dot.setFont(get_ui_font(6, QFont.Weight.Bold))
            dot.setStyleSheet(f"color: {C_GREEN_SUCCESS}; border: none; background: transparent;")
            lbl = QLabel("Active in Memory")
            lbl.setFont(get_ui_font(8, QFont.Weight.Bold))
            lbl.setStyleSheet(f"color: {C_GREEN_SUCCESS}; border: none; background: transparent;")
            ab_lay.addWidget(dot)
            ab_lay.addWidget(lbl)
            hdr.addWidget(act_badge)

        lay.addLayout(hdr)

        # Tags Row
        tags_row = QHBoxLayout()
        tags_row.setSpacing(6)
        tags = []
        if self.model_info.get("coding"):
            tags.append("Code Specialist")
        tags.append(self.model_info.get("family", "Model").upper())
        tag = self.model_info.get("tag", "")
        if tag and tag != "latest":
            tags.append(tag)
        tags.append("Ollama Local")

        for t in tags:
            tag_lbl = QLabel(t)
            tag_lbl.setFont(get_code_font(8, QFont.Weight.Medium))
            tag_lbl.setStyleSheet(f"""
                background: rgba(255, 255, 255, 0.05);
                color: {C_TEXT_SECONDARY};
                border: 1px solid rgba(255, 255, 255, 0.06);
                border-radius: 4px;
                padding: 2px 7px;
            """)
            tags_row.addWidget(tag_lbl)
        tags_row.addStretch()
        lay.addLayout(tags_row)

        # Status & Action Row
        st_row = QHBoxLayout()
        if self.is_active:
            st_lbl = QLabel("Ready for inference requests")
            st_lbl.setFont(get_ui_font(8, QFont.Weight.Normal))
            st_lbl.setStyleSheet(f"color: {C_TEXT_MUTED}; border: none; background: transparent;")
            st_row.addWidget(st_lbl)
            st_row.addStretch()

            act_btn = QPushButton("Unload from Memory")
            act_btn.setFont(get_ui_font(8, QFont.Weight.Medium))
            act_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            act_btn.setStyleSheet(f"""
                QPushButton {{
                    background: rgba(255, 255, 255, 0.05);
                    color: {C_TEXT_MUTED};
                    border: 1px solid {C_BORDER_SUBTLE};
                    border-radius: 5px;
                    padding: 5px 12px;
                }}
                QPushButton:hover {{
                    background: rgba(244, 63, 94, 0.15);
                    color: #f43f5e;
                    border-color: rgba(244, 63, 94, 0.35);
                }}
            """)
            act_btn.clicked.connect(lambda: self.unload_clicked.emit(self.model_name))
            st_row.addWidget(act_btn)
        else:
            st_lbl = QLabel("Installed on local drive")
            st_lbl.setFont(get_ui_font(8, QFont.Weight.Normal))
            st_lbl.setStyleSheet(f"color: {C_TEXT_MUTED}; border: none; background: transparent;")
            st_row.addWidget(st_lbl)
            st_row.addStretch()

            act_btn = QPushButton("Set Active Model")
            act_btn.setFont(get_ui_font(8, QFont.Weight.Bold))
            act_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            act_btn.setStyleSheet(f"""
                QPushButton {{
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 {C_ACCENT_PRIMARY}, stop:1 #9333ea);
                    color: #ffffff;
                    border: none;
                    border-radius: 6px;
                    padding: 5px 14px;
                }}
                QPushButton:hover {{
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 {C_ACCENT_HOVER}, stop:1 #a855f7);
                }}
            """)
            act_btn.clicked.connect(lambda: self.select_clicked.emit(self.model_name))
            st_row.addWidget(act_btn)

        lay.addLayout(st_row)


class ModelsView(QFrame):
    """Dynamic Model Management View with zero-leak inspector and responsive settings."""

    model_changed = Signal(str)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("ModelsView")
        self.setStyleSheet(f"""
            #ModelsView {{
                background: {C_BG_SURFACE};
            }}
        """)
        self._insp_container: QWidget | None = None
        self._setup_ui()
        self.refresh_models()

    def _setup_ui(self) -> None:
        main_lay = QHBoxLayout(self)
        main_lay.setContentsMargins(0, 0, 0, 0)
        main_lay.setSpacing(0)

        # ── Left Repository Section ───────────────────────────────────────────
        repo_sec = QWidget()
        r_lay = QVBoxLayout(repo_sec)
        r_lay.setContentsMargins(24, 20, 24, 20)
        r_lay.setSpacing(16)

        # Repository Header & Controls
        hdr_row = QHBoxLayout()
        rh_col = QVBoxLayout()
        rh_col.setSpacing(3)
        r_title = QLabel("Model Repository")
        r_title.setFont(get_ui_font(13, QFont.Weight.Bold))
        r_title.setStyleSheet(f"color: {C_TEXT_PRIMARY};")
        
        r_sub = QLabel("Manage local Ollama models and cloud remote API endpoints.")
        r_sub.setFont(get_ui_font(9, QFont.Weight.Normal))
        r_sub.setStyleSheet(f"color: {C_TEXT_MUTED};")
        
        rh_col.addWidget(r_title)
        rh_col.addWidget(r_sub)
        hdr_row.addLayout(rh_col)
        hdr_row.addStretch()

        self.auto_cb = QCheckBox("Auto Model Detection")
        self.auto_cb.setFont(get_ui_font(9, QFont.Weight.Medium))
        self.auto_cb.setChecked(config_manager.get_model_mode() == "auto")
        self.auto_cb.setStyleSheet(f"color: {C_ACCENT_LIGHT};")
        self.auto_cb.toggled.connect(self._on_auto_toggle)
        hdr_row.addWidget(self.auto_cb)

        refresh_btn = QPushButton("↻ Refresh")
        refresh_btn.setFont(get_ui_font(8, QFont.Weight.Bold))
        refresh_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        refresh_btn.setStyleSheet(f"""
            QPushButton {{
                background: rgba(255, 255, 255, 0.05);
                color: {C_TEXT_PRIMARY};
                border: 1px solid {C_BORDER_SUBTLE};
                border-radius: 6px;
                padding: 5px 12px;
            }}
            QPushButton:hover {{
                background: rgba(255, 255, 255, 0.10);
            }}
        """)
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
        rem_lbl = QLabel("REMOTE CLOUD PROVIDERS")
        rem_lbl.setFont(get_ui_font(8, QFont.Weight.Bold))
        rem_lbl.setStyleSheet(f"color: {C_TEXT_DIM}; letter-spacing: 1.2px; margin-top: 8px;")
        r_lay.addWidget(rem_lbl)

        self.remote_box = QVBoxLayout()
        self.remote_box.setSpacing(8)
        r_lay.addLayout(self.remote_box)

        main_lay.addWidget(repo_sec, stretch=6)

        # ── Right Inspector Panel ─────────────────────────────────────────────
        self.insp_panel = QFrame()
        self.insp_panel.setFixedWidth(310)
        self.insp_panel.setStyleSheet(f"background: {C_BG_CANVAS}; border-left: 1px solid {C_BORDER_SUBTLE};")
        self.i_lay = QVBoxLayout(self.insp_panel)
        self.i_lay.setContentsMargins(18, 20, 18, 20)
        self.i_lay.setSpacing(14)
        self.i_lay.setAlignment(Qt.AlignmentFlag.AlignTop)

        main_lay.addWidget(self.insp_panel, stretch=4)

    def refresh_models(self) -> None:
        """Scan real local models from Ollama and rebuild cards dynamically."""
        # Clear existing model cards cleanly
        while self.cards_layout.count():
            item = self.cards_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        # Clear remote providers cleanly
        while self.remote_box.count():
            item = self.remote_box.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        current_active = config_manager.get_current_model()
        models = model_scanner.scan_ollama_models()

        if not models:
            no_model_card = QFrame()
            no_model_card.setStyleSheet(f"background: {C_BG_CARD}; border: 1px dashed {C_BORDER_MEDIUM}; border-radius: 8px; padding: 20px;")
            nm_lay = QVBoxLayout(no_model_card)
            nm_lay.setAlignment(Qt.AlignmentFlag.AlignCenter)
            nm_lay.setSpacing(6)
            
            nm_lbl = QLabel("No Local Ollama Models Detected")
            nm_lbl.setFont(get_ui_font(11, QFont.Weight.Bold))
            nm_lbl.setStyleSheet(f"color: {C_TEXT_PRIMARY};")
            
            nm_sub = QLabel("Ensure Ollama is running and run 'ollama pull qwen2.5-coder:3b' in terminal.")
            nm_sub.setFont(get_ui_font(9, QFont.Weight.Normal))
            nm_sub.setWordWrap(True)
            nm_sub.setAlignment(Qt.AlignmentFlag.AlignCenter)
            nm_sub.setStyleSheet(f"color: {C_TEXT_MUTED};")
            
            nm_lay.addWidget(nm_lbl)
            nm_lay.addWidget(nm_sub)
            self.cards_layout.addWidget(no_model_card)
        else:
            local_hdr = QLabel(f"LOCAL OLLAMA MODELS ({len(models)})")
            local_hdr.setFont(get_ui_font(8, QFont.Weight.Bold))
            local_hdr.setStyleSheet(f"color: {C_TEXT_DIM}; letter-spacing: 1px;")
            self.cards_layout.addWidget(local_hdr)

            for m in models:
                name = m.get("name", "")
                is_act = (name == current_active)
                card = ModelCardWidget(m, is_active=is_act)
                card.select_clicked.connect(self._on_select_model)
                card.unload_clicked.connect(self._on_unload_model)
                self.cards_layout.addWidget(card)

        # Build Remote Providers
        providers = [
            ("openai", "OpenAI (API)", "GPT-4o, GPT-4o-mini"),
            ("gemini", "Google Gemini (API)", "Gemini 1.5 Pro, Flash"),
            ("groq",   "Groq (API)", "Llama 3 70B, Mixtral 8x7B"),
        ]

        for prov_id, prov_name, prov_desc in providers:
            key = config_manager.get_api_key(prov_id)
            is_cfg = bool(key and key != f"YOUR_{prov_id.upper()}_KEY")

            rem_frame = QFrame()
            rem_frame.setStyleSheet(f"""
                QFrame {{
                    background: {C_BG_CARD};
                    border: 1px solid {C_BORDER_SUBTLE};
                    border-radius: 8px;
                    padding: 8px 14px;
                }}
                QFrame:hover {{
                    border-color: {C_BORDER_MEDIUM};
                }}
            """)
            rf_lay = QHBoxLayout(rem_frame)
            rf_lay.setContentsMargins(4, 4, 4, 4)
            rf_lay.setSpacing(10)
            
            p_col = QVBoxLayout()
            p_col.setSpacing(1)
            p_lbl = QLabel(prov_name)
            p_lbl.setFont(get_ui_font(9, QFont.Weight.Bold))
            p_lbl.setStyleSheet(f"color: {C_TEXT_PRIMARY};")
            
            p_sub = QLabel(prov_desc)
            p_sub.setFont(get_code_font(8, QFont.Weight.Normal))
            p_sub.setStyleSheet(f"color: {C_TEXT_MUTED};")
            p_col.addWidget(p_lbl)
            p_col.addWidget(p_sub)
            rf_lay.addLayout(p_col)
            rf_lay.addStretch()

            if is_cfg:
                st = QLabel("● Configured")
                st.setFont(get_ui_font(8, QFont.Weight.Bold))
                st.setStyleSheet(f"color: {C_GREEN_SUCCESS};")
                rf_lay.addWidget(st)
                btn = QPushButton("Edit Key")
            else:
                st = QLabel("○ No Key")
                st.setFont(get_ui_font(8, QFont.Weight.Normal))
                st.setStyleSheet(f"color: {C_TEXT_MUTED};")
                rf_lay.addWidget(st)
                btn = QPushButton("Connect")

            btn.setFont(get_ui_font(8, QFont.Weight.Medium))
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setStyleSheet(f"""
                QPushButton {{
                    background: rgba(255, 255, 255, 0.06);
                    color: {C_TEXT_PRIMARY};
                    border: 1px solid {C_BORDER_SUBTLE};
                    border-radius: 5px;
                    padding: 4px 10px;
                }}
                QPushButton:hover {{
                    background: rgba(255, 255, 255, 0.12);
                    color: #ffffff;
                }}
            """)
            _prov = prov_id
            btn.clicked.connect(lambda _, p=_prov: self._configure_api_key(p))
            rf_lay.addWidget(btn)

            self.remote_box.addWidget(rem_frame)

        # Update Right Inspector cleanly (zero layout leaks)
        self._update_inspector(models, current_active)

    def _update_inspector(self, models: list[dict], active_name: str | None) -> None:
        """Update right inspector by replacing single container widget (zero leak)."""
        if self._insp_container:
            self.i_lay.removeWidget(self._insp_container)
            self._insp_container.deleteLater()
            self._insp_container = None

        self._insp_container = QWidget()
        ci_lay = QVBoxLayout(self._insp_container)
        ci_lay.setContentsMargins(0, 0, 0, 0)
        ci_lay.setSpacing(14)

        i_hdr = QLabel("MODEL INSPECTOR")
        i_hdr.setFont(get_ui_font(8, QFont.Weight.Bold))
        i_hdr.setStyleSheet(f"color: {C_TEXT_DIM}; letter-spacing: 1.2px;")
        ci_lay.addWidget(i_hdr)

        active_info = next((m for m in models if m.get("name") == active_name), None)
        if not active_info and models:
            active_info = models[0]

        if active_info:
            name = active_info.get("name", "Unknown")
            family = active_info.get("family", "Model")
            size_gb = active_info.get("size", 0) / (1024 * 1024 * 1024)

            i_title = QLabel(name)
            i_title.setFont(get_ui_font(12, QFont.Weight.Bold))
            i_title.setStyleSheet(f"color: {C_ACCENT_LIGHT};")
            
            i_desc = QLabel(f"Local {family} model loaded in Ollama engine. Optimized for desktop developer tasks.")
            i_desc.setFont(get_ui_font(9, QFont.Weight.Normal))
            i_desc.setWordWrap(True)
            i_desc.setStyleSheet(f"color: {C_TEXT_MUTED}; line-height: 1.4;")
            
            ci_lay.addWidget(i_title)
            ci_lay.addWidget(i_desc)

            # Capabilities Grid
            cap_lbl = QLabel("CAPABILITIES")
            cap_lbl.setFont(get_ui_font(8, QFont.Weight.Bold))
            cap_lbl.setStyleSheet(f"color: {C_TEXT_DIM}; letter-spacing: 1.2px; margin-top: 8px;")
            ci_lay.addWidget(cap_lbl)

            cap_grid = QWidget()
            cg_lay = QVBoxLayout(cap_grid)
            cg_lay.setContentsMargins(0, 0, 0, 0)
            cg_lay.setSpacing(6)

            is_coding = active_info.get("coding", False)
            row1 = QHBoxLayout()
            row1.addWidget(self._cap_box("Code Gen", active=is_coding))
            row1.addWidget(self._cap_box("Vision", active=False))
            cg_lay.addLayout(row1)

            row2 = QHBoxLayout()
            row2.addWidget(self._cap_box("Reasoning", active=True))
            row2.addWidget(self._cap_box("Instruct", active=True))
            cg_lay.addLayout(row2)
            ci_lay.addWidget(cap_grid)

            # Resource Allocation
            res_lbl = QLabel("RESOURCE ALLOCATION")
            res_lbl.setFont(get_ui_font(8, QFont.Weight.Bold))
            res_lbl.setStyleSheet(f"color: {C_TEXT_DIM}; letter-spacing: 1.2px; margin-top: 8px;")
            ci_lay.addWidget(res_lbl)

            ram_val = f"{size_gb:.1f} GB" if size_gb > 0 else "Dynamic"
            
            ram_row = QHBoxLayout()
            r_label = QLabel("Disk Footprint")
            r_label.setFont(get_ui_font(9, QFont.Weight.Normal))
            r_label.setStyleSheet(f"color: {C_TEXT_MUTED};")
            r_val = QLabel(ram_val)
            r_val.setFont(get_code_font(9, QFont.Weight.Bold))
            r_val.setStyleSheet(f"color: {C_TEXT_PRIMARY};")
            ram_row.addWidget(r_label)
            ram_row.addStretch()
            ram_row.addWidget(r_val)
            ci_lay.addLayout(ram_row)

            # Memory visual bar
            meter = QProgressBar()
            meter.setFixedHeight(5)
            meter.setTextVisible(False)
            meter.setRange(0, 100)
            pct = min(100, int((size_gb / 8.0) * 100)) if size_gb > 0 else 25
            meter.setValue(pct)
            meter.setStyleSheet(f"""
                QProgressBar {{
                    background: rgba(255, 255, 255, 0.08);
                    border: none;
                    border-radius: 2px;
                }}
                QProgressBar::chunk {{
                    background: {C_ACCENT_PRIMARY};
                    border-radius: 2px;
                }}
            """)
            ci_lay.addWidget(meter)

            for label, val in [("Host", "http://127.0.0.1:11434"), ("Provider", "Ollama Local"), ("Context Window", "32k tokens")]:
                r_row = QHBoxLayout()
                lbl = QLabel(label)
                lbl.setFont(get_ui_font(9, QFont.Weight.Normal))
                lbl.setStyleSheet(f"color: {C_TEXT_MUTED};")
                v = QLabel(val)
                v.setFont(get_code_font(9, QFont.Weight.Medium))
                v.setStyleSheet(f"color: {C_TEXT_PRIMARY};")
                r_row.addWidget(lbl)
                r_row.addStretch()
                r_row.addWidget(v)
                ci_lay.addLayout(r_row)

        else:
            i_title = QLabel("No Model Active")
            i_title.setFont(get_ui_font(10, QFont.Weight.Normal))
            i_title.setStyleSheet(f"color: {C_TEXT_MUTED};")
            ci_lay.addWidget(i_title)

        ci_lay.addStretch()
        self.i_lay.addWidget(self._insp_container)

    def _cap_box(self, text: str, active: bool = True) -> QFrame:
        box = QFrame()
        box.setStyleSheet(f"""
            background: {C_ACCENT_SURFACE if active else 'rgba(255,255,255,0.03)'};
            border: 1px solid {C_BORDER_ACCENT if active else C_BORDER_SUBTLE};
            border-radius: 6px;
            padding: 6px;
        """)
        b_lay = QVBoxLayout(box)
        b_lay.setContentsMargins(4, 4, 4, 4)
        lbl = QLabel(text)
        lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl.setFont(get_ui_font(8, QFont.Weight.Bold if active else QFont.Weight.Normal))
        lbl.setStyleSheet(f"color: {'#ffffff' if active else C_TEXT_MUTED}; border: none; background: transparent;")
        b_lay.addWidget(lbl)
        return box

    def _on_select_model(self, name: str) -> None:
        config_manager.set_current_model(name)
        self.model_changed.emit(name)
        QTimer.singleShot(0, self.refresh_models)

    def _on_unload_model(self, name: str) -> None:
        model_manager.unload_model()
        QTimer.singleShot(0, self.refresh_models)

    def _on_auto_toggle(self, checked: bool) -> None:
        if checked:
            config_manager.enable_auto_detection()
            resolve_model(config_manager, model_scanner)
        else:
            config_manager.set_model_mode("manual")
        QTimer.singleShot(0, self.refresh_models)

    def _configure_api_key(self, provider: str) -> None:
        current = config_manager.get_api_key(provider) or ""
        if current.startswith("YOUR_"):
            current = ""
        dlg = ApiKeyModalDialog(provider, current, self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            key = dlg.get_key()
            if key:
                config_manager.set_api_key(provider, key)
                QTimer.singleShot(0, self.refresh_models)
