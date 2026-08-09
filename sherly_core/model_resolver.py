"""
MODEL RESOLVER — sherly_core/model_resolver.py

The single decision point for: "Which model should Sherly use right now?"

Resolution priority:
    1. User-pinned model   (manual mode)
    2. Auto-detected best  (auto mode)
    3. Previously configured model (fallback)
    4. None → graceful offline / error state

Nothing else in the project needs to know *how* model selection works.
"""

from __future__ import annotations

import logging

logger = logging.getLogger(__name__)


def resolve_model(config_manager, scanner) -> str | None:
    """
    Determine which model Sherly should use.

    Args:
        config_manager: The config_manager module (for reading / writing config).
        scanner:        The model_scanner module (for scanning Ollama).

    Returns:
        The model name string, or None if no model is available.
    """
    mode = config_manager.get_model_mode()

    logger.info("[ModelResolver] Mode: %s", mode.upper())

    # ── Manual mode: respect the user's explicit choice ──────────────
    if mode == "manual":
        pinned = config_manager.get_pinned_model()
        if pinned:
            logger.info("[ModelResolver] Using pinned model: %s", pinned)
            return pinned

        # Pinned is None but mode is manual — try current_model
        current = config_manager.get_current_model()
        if current:
            logger.info("[ModelResolver] Using current model: %s", current)
            return current

        # Manual mode with nothing set — fall through to auto-detect
        logger.warning(
            "[ModelResolver] Manual mode but no model configured. "
            "Falling back to auto-detection."
        )

    # ── Auto mode: scan and pick the best ────────────────────────────
    models = scanner.scan_ollama_models()

    if not models:
        # No models found — try whatever was previously configured
        current = config_manager.get_current_model()
        if current:
            logger.warning(
                "[ModelResolver] No models detected. Keeping previous: %s",
                current,
            )
            return current

        logger.error("[ModelResolver] No models available. Sherly is offline.")
        return None

    # Log what we found
    model_names = [m.get("name", "?") for m in models]
    for name in model_names:
        logger.info("[ModelScanner]   %s", name)

    selected = scanner.pick_best_model(models)

    if selected is None:
        return None

    model_name = selected["name"]

    # Write the selection into config (without overriding mode or pinned)
    config_manager.set_resolved_model(model_name)

    logger.info("[ModelResolver] Selected: %s", model_name)

    return model_name
