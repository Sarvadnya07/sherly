"""
Tests for core/data_gen.py — Alpaca Training Data Export (FS-#27)
"""

from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

from sherly.core.data_gen import DatasetGenerator


# ---------------------------------------------------------------------------
# Fixtures — write fake telemetry and feedback files
# ---------------------------------------------------------------------------

@pytest.fixture
def tmp_telemetry(tmp_path: Path) -> str:
    tel_file = tmp_path / "telemetry.jsonl"
    records  = [
        # Successful self-heal
        json.dumps({
            "event_type": "self_heal",
            "data": {
                "success": True,
                "error":  "ModuleNotFoundError: No module named 'requests'",
                "fix_applied": "pip install requests",
            }
        }),
        # Failed self-heal (should be excluded)
        json.dumps({
            "event_type": "self_heal",
            "data": {
                "success": False,
                "error":  "AttributeError: 'NoneType' has no attribute 'run'",
                "fix_applied": "",
            }
        }),
        # Another success
        json.dumps({
            "event_type": "self_heal",
            "data": {
                "success": True,
                "error":  "SyntaxError: invalid syntax",
                "fix_applied": "Fixed the missing colon on line 12.",
            }
        }),
    ]
    tel_file.write_text("\n".join(records), encoding="utf-8")
    return str(tel_file)


@pytest.fixture
def tmp_feedback(tmp_path: Path) -> Path:
    fb_file = tmp_path / "feedback_log.jsonl"
    records = [
        # Positive rating
        json.dumps({
            "user":      "open vscode",
            "assistant": "Opening Visual Studio Code now.",
            "rating":    "y",
        }),
        # Negative rating (excluded)
        json.dumps({
            "user":      "search for cats",
            "assistant": "I searched for cats.",
            "rating":    "n",
        }),
    ]
    fb_file.write_text("\n".join(records), encoding="utf-8")
    return fb_file


# ---------------------------------------------------------------------------
# DatasetGenerator._load_telemetry_samples
# ---------------------------------------------------------------------------

def test_telemetry_loads_only_successes(tmp_telemetry: str, tmp_path: Path) -> None:
    gen     = DatasetGenerator(telemetry_path=tmp_telemetry)
    samples = gen._load_telemetry_samples()
    assert len(samples) == 2   # 2 successful out of 3


def test_telemetry_sample_has_alpaca_keys(tmp_telemetry: str) -> None:
    gen     = DatasetGenerator(telemetry_path=tmp_telemetry)
    samples = gen._load_telemetry_samples()
    for sample in samples:
        assert "instruction" in sample
        assert "input"       in sample
        assert "output"      in sample


def test_telemetry_missing_file_returns_empty(tmp_path: Path) -> None:
    gen = DatasetGenerator(telemetry_path=str(tmp_path / "nonexistent.jsonl"))
    assert gen._load_telemetry_samples() == []


# ---------------------------------------------------------------------------
# DatasetGenerator.get_stats
# ---------------------------------------------------------------------------

def test_get_stats_structure(tmp_telemetry: str) -> None:
    gen   = DatasetGenerator(telemetry_path=tmp_telemetry)
    stats = gen.get_stats()
    assert "telemetry_samples" in stats
    assert "feedback_samples"  in stats
    assert "output_path"       in stats
    assert "schema"            in stats
    assert stats["schema"]     == "alpaca"


# ---------------------------------------------------------------------------
# DatasetGenerator.export_successful_fixes (full pipeline)
# ---------------------------------------------------------------------------

def test_export_creates_output_file(tmp_telemetry: str, tmp_path: Path) -> None:
    gen              = DatasetGenerator(telemetry_path=tmp_telemetry)
    gen.dataset_path = str(tmp_path / "train.jsonl")
    result           = gen.export_successful_fixes()
    assert "Exported" in result
    assert Path(gen.dataset_path).exists()


def test_export_output_is_valid_jsonl(tmp_telemetry: str, tmp_path: Path) -> None:
    gen              = DatasetGenerator(telemetry_path=tmp_telemetry)
    gen.dataset_path = str(tmp_path / "train.jsonl")
    gen.export_successful_fixes()
    lines = Path(gen.dataset_path).read_text().strip().splitlines()
    for line in lines:
        record = json.loads(line)
        assert "instruction" in record
        assert "input"       in record
        assert "output"      in record


def test_export_deduplication(tmp_path: Path) -> None:
    """Duplicate (input, output) pairs should be collapsed to one."""
    dup_entry = json.dumps({
        "event_type": "self_heal",
        "data": {"success": True, "error": "same error", "fix_applied": "same fix"},
    })
    tel_file = tmp_path / "dup_telemetry.jsonl"
    tel_file.write_text(dup_entry + "\n" + dup_entry + "\n", encoding="utf-8")

    gen              = DatasetGenerator(telemetry_path=str(tel_file))
    gen.dataset_path = str(tmp_path / "dedup.jsonl")
    gen.export_successful_fixes()

    lines = Path(gen.dataset_path).read_text().strip().splitlines()
    assert len(lines) == 1, f"Expected 1 deduplicated line, got {len(lines)}"


def test_export_no_data_returns_warning(tmp_path: Path) -> None:
    gen              = DatasetGenerator(telemetry_path=str(tmp_path / "empty.jsonl"))
    gen.dataset_path = str(tmp_path / "train.jsonl")
    result           = gen.export_successful_fixes()
    assert "⚠️" in result or "No training data" in result
