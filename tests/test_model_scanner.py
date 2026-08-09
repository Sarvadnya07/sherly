"""
Tests for the model scanner and model resolver.

Run:  pytest tests/test_model_scanner.py -v
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from unittest.mock import MagicMock

# Ensure project root is importable
_ROOT = str(Path(__file__).resolve().parent.parent)
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from model_scanner import normalize_model, pick_best_model, _score_model

# Import model_resolver directly (bypassing sherly_core/__init__.py which
# eagerly imports TTS — unavailable in the test environment).
_resolver_path = Path(_ROOT) / "sherly_core" / "model_resolver.py"
_spec = importlib.util.spec_from_file_location("model_resolver", _resolver_path)
_resolver_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_resolver_mod)
resolve_model = _resolver_mod.resolve_model


# ── Scanner tests ────────────────────────────────────────────────────────

class TestNormalizeModel:
    def test_basic_normalization(self):
        raw = {"name": "qwen2.5-coder:3b", "size": 1_900_000_000}
        result = normalize_model(raw)

        assert result["name"] == "qwen2.5-coder:3b"
        assert result["family"] == "qwen2.5-coder"
        assert result["tag"] == "3b"
        assert result["size"] == 1_900_000_000
        assert result["coding"] is True
        assert result["local"] is True

    def test_latest_tag(self):
        raw = {"name": "mistral", "size": 4_000_000_000}
        result = normalize_model(raw)

        assert result["family"] == "mistral"
        assert result["tag"] == "latest"
        assert result["coding"] is False

    def test_general_model(self):
        raw = {"name": "llama3:8b", "size": 8_000_000_000}
        result = normalize_model(raw)

        assert result["family"] == "llama3"
        assert result["tag"] == "8b"
        assert result["coding"] is False

    def test_unknown_model(self):
        raw = {"name": "some-random-model:latest"}
        result = normalize_model(raw)

        assert result["family"] == "some-random-model"
        assert result["coding"] is False


class TestScoring:
    def test_coding_model_scores_highest(self):
        coder = normalize_model({"name": "qwen2.5-coder:3b", "size": 1_900_000_000})
        general = normalize_model({"name": "llama3:8b", "size": 8_000_000_000})

        assert _score_model(coder) > _score_model(general)

    def test_unknown_model_scores_low(self):
        unknown = normalize_model({"name": "some-random:latest", "size": 1_000_000})
        known = normalize_model({"name": "phi3:latest", "size": 3_800_000_000})

        assert _score_model(known) > _score_model(unknown)


class TestPickBestModel:
    def test_qwen_coder_wins(self):
        models = [
            normalize_model({"name": "mistral:latest", "size": 4_100_000_000}),
            normalize_model({"name": "qwen2.5-coder:3b", "size": 1_900_000_000}),
            normalize_model({"name": "phi3:latest", "size": 3_800_000_000}),
        ]

        selected = pick_best_model(models)

        assert selected is not None
        assert selected["name"] == "qwen2.5-coder:3b"

    def test_fallback_to_available_model(self):
        models = [
            normalize_model({"name": "some-random-model:latest", "size": 1_000_000}),
        ]

        selected = pick_best_model(models)

        assert selected is not None
        assert selected["name"] == "some-random-model:latest"

    def test_no_models(self):
        assert pick_best_model([]) is None

    def test_coding_beats_general(self):
        models = [
            normalize_model({"name": "llama3:8b", "size": 8_000_000_000}),
            normalize_model({"name": "codellama:7b", "size": 7_000_000_000}),
        ]

        selected = pick_best_model(models)

        assert selected is not None
        assert selected["name"] == "codellama:7b"

    def test_deepseek_coder_v2(self):
        """Ollama naming like deepseek-coder-v2:16b should be recognized."""
        models = [
            normalize_model({"name": "phi3:latest", "size": 3_800_000_000}),
            normalize_model({"name": "deepseek-coder-v2:16b", "size": 16_000_000_000}),
        ]

        selected = pick_best_model(models)

        assert selected is not None
        assert selected["name"] == "deepseek-coder-v2:16b"


# ── Resolver tests ───────────────────────────────────────────────────────

class TestModelResolver:
    def test_manual_mode_uses_pinned(self):
        """Manual mode should use pinned model, not auto-detect."""


        mock_config = MagicMock()
        mock_config.get_model_mode.return_value = "manual"
        mock_config.get_pinned_model.return_value = "mistral:7b"

        mock_scanner = MagicMock()

        result = resolve_model(mock_config, mock_scanner)

        assert result == "mistral:7b"
        mock_scanner.scan_ollama_models.assert_not_called()

    def test_manual_mode_not_overridden_by_auto(self):
        """Even if better models exist, manual mode sticks with pinned."""


        mock_config = MagicMock()
        mock_config.get_model_mode.return_value = "manual"
        mock_config.get_pinned_model.return_value = "phi3:latest"

        mock_scanner = MagicMock()
        # Scanner has a better model available, but shouldn't be consulted
        mock_scanner.scan_ollama_models.return_value = [
            normalize_model({"name": "qwen2.5-coder:3b"}),
        ]

        result = resolve_model(mock_config, mock_scanner)

        assert result == "phi3:latest"
        mock_scanner.scan_ollama_models.assert_not_called()

    def test_auto_mode_selects_best(self):
        """Auto mode should scan and pick the best model."""


        mock_config = MagicMock()
        mock_config.get_model_mode.return_value = "auto"

        mock_scanner = MagicMock()
        mock_scanner.scan_ollama_models.return_value = [
            normalize_model({"name": "mistral:latest", "size": 4_000_000_000}),
            normalize_model({"name": "qwen2.5-coder:3b", "size": 1_900_000_000}),
        ]
        mock_scanner.pick_best_model.return_value = normalize_model(
            {"name": "qwen2.5-coder:3b", "size": 1_900_000_000}
        )

        result = resolve_model(mock_config, mock_scanner)

        assert result == "qwen2.5-coder:3b"
        mock_config.set_resolved_model.assert_called_once_with("qwen2.5-coder:3b")

    def test_no_models_returns_none(self):
        """When no models are found and nothing is configured, return None."""


        mock_config = MagicMock()
        mock_config.get_model_mode.return_value = "auto"
        mock_config.get_current_model.return_value = None

        mock_scanner = MagicMock()
        mock_scanner.scan_ollama_models.return_value = []

        result = resolve_model(mock_config, mock_scanner)

        assert result is None

    def test_manual_mode_falls_back_to_auto_when_no_pinned(self):
        """Manual mode with no pinned model should fall through to auto."""


        mock_config = MagicMock()
        mock_config.get_model_mode.return_value = "manual"
        mock_config.get_pinned_model.return_value = None
        mock_config.get_current_model.return_value = None

        mock_scanner = MagicMock()
        mock_scanner.scan_ollama_models.return_value = [
            normalize_model({"name": "qwen2.5-coder:3b", "size": 1_900_000_000}),
        ]
        mock_scanner.pick_best_model.return_value = normalize_model(
            {"name": "qwen2.5-coder:3b", "size": 1_900_000_000}
        )

        result = resolve_model(mock_config, mock_scanner)

        assert result == "qwen2.5-coder:3b"
