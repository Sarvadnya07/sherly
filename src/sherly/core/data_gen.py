"""
DATA GENERATOR — data_gen.py
Upgrades:
  FS-#27  Alpaca-schema training data export aligned with Phase C feedback log.
           Sources: telemetry.jsonl (self_heal events) + feedback_log.jsonl (Phase C ratings).
           Output: sherly_training_data.jsonl in Alpaca format ready for local fine-tuning.
           Exposed as UI command: "export training data"
"""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from sherly.core.telemetry import TELEMETRY_FILE
from sherly.utils.runtime_utils import log


# ---------------------------------------------------------------------------
# FS-#27 — Alpaca dataset schema:
# { "instruction": str, "input": str, "output": str }
# ---------------------------------------------------------------------------

_OUTPUT_DIR = Path("memory_rag")
_TRAINING_FILE = _OUTPUT_DIR / "sherly_training_data.jsonl"


class DatasetGenerator:
    """
    Generates fine-tuning datasets from successful self-healing sessions
    and Phase C feedback ratings.

    FS-#27: Standardized to Alpaca schema.
    UI command: "export training data"
    """

    def __init__(self, telemetry_path: str = TELEMETRY_FILE) -> None:
        self.telemetry_path = telemetry_path
        self.dataset_path   = str(_TRAINING_FILE)

    # ------------------------------------------------------------------
    # Source 1: Telemetry (self-heal events)
    # ------------------------------------------------------------------

    def _load_telemetry_samples(self) -> list[dict[str, str]]:
        """Extract Alpaca-format samples from successful self-heal events."""
        samples: list[dict[str, str]] = []
        if not os.path.exists(self.telemetry_path):
            return samples

        try:
            with open(self.telemetry_path, "r", encoding="utf-8") as f:
                for line in f:
                    try:
                        entry = json.loads(line.strip())
                    except json.JSONDecodeError:
                        continue
                    if entry.get("event_type") != "self_heal":
                        continue
                    data = entry.get("data", {})
                    if not data.get("success"):
                        continue
                    samples.append({
                        "instruction": "You are Sherly AI. Fix the following error in the project.",
                        "input":       data.get("error", ""),
                        "output":      data.get("fix_applied", "Code modification applied successfully."),
                    })
        except Exception as exc:
            log(f"[DataGen] Telemetry load error: {exc}", level="error")

        return samples

    # ------------------------------------------------------------------
    # Source 2: Phase C feedback log (command_router.py FEEDBACK_FILE)
    # ------------------------------------------------------------------

    def _load_feedback_samples(self) -> list[dict[str, str]]:
        """
        FS-#27: Extract positively-rated (y) exchanges from feedback_log.jsonl.
        Expected format per line:
          {"user": "...", "assistant": "...", "rating": "y"/"n"}
        """
        samples: list[dict[str, str]] = []

        # Locate feedback_log.jsonl — check both CWD and the canonical logs/ path
        candidate_paths = [
            Path("feedback_log.jsonl"),
            Path(__file__).parent.parent / "logs" / "feedback_log.jsonl",
            Path("logs") / "feedback_log.jsonl",
        ]
        feedback_file: Path | None = None
        for p in candidate_paths:
            if p.exists():
                feedback_file = p
                break

        if feedback_file is None:
            return samples

        try:
            with open(feedback_file, "r", encoding="utf-8") as f:
                for line in f:
                    try:
                        entry = json.loads(line.strip())
                    except json.JSONDecodeError:
                        continue
                    if entry.get("rating", "").lower() != "y":
                        continue
                    user_text      = entry.get("user", "")
                    assistant_text = entry.get("assistant", "")
                    if not user_text or not assistant_text:
                        continue
                    samples.append({
                        "instruction": "You are Sherly AI, an autonomous developer assistant. Respond helpfully.",
                        "input":       user_text,
                        "output":      assistant_text,
                    })
        except Exception as exc:
            log(f"[DataGen] Feedback load error: {exc}", level="error")

        return samples

    # ------------------------------------------------------------------
    # Public export method
    # ------------------------------------------------------------------

    def export_successful_fixes(self) -> str:
        """
        FS-#27: Merge telemetry + feedback sources, deduplicate, and write
        to sherly_training_data.jsonl in Alpaca format.

        Returns a user-visible status string.
        """
        telemetry_samples = self._load_telemetry_samples()
        feedback_samples  = self._load_feedback_samples()
        all_samples       = telemetry_samples + feedback_samples

        if not all_samples:
            msg = (
                "⚠️  No training data found. Make sure:\n"
                "  • telemetry_enabled = true in config.json\n"
                "  • You have used Sherly in Phase C (SHERLY_PHASE=C)"
            )
            log("[DataGen] No samples found.", level="warning")
            return msg

        # Deduplicate by (input, output) pair
        seen:    set[tuple[str, str]] = set()
        unique:  list[dict[str, str]] = []
        for sample in all_samples:
            key = (sample["input"].strip(), sample["output"].strip())
            if key not in seen:
                seen.add(key)
                unique.append(sample)

        _OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        with open(self.dataset_path, "w", encoding="utf-8") as f:
            for item in unique:
                f.write(json.dumps(item, ensure_ascii=False) + "\n")

        msg = (
            f"✅ Exported {len(unique)} training samples "
            f"({len(telemetry_samples)} self-heal, {len(feedback_samples)} Phase C rated)\n"
            f"   → {self.dataset_path}"
        )
        log(f"[DataGen] {msg}")
        return msg

    def get_stats(self) -> dict[str, Any]:
        """Return statistics about available training data without exporting."""
        return {
            "telemetry_samples": len(self._load_telemetry_samples()),
            "feedback_samples":  len(self._load_feedback_samples()),
            "output_path":       self.dataset_path,
            "schema":            "alpaca",
            "timestamp":         datetime.now(timezone.utc).isoformat(),
        }
