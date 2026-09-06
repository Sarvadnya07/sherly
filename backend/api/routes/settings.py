"""
SETTINGS ROUTES — backend/api/routes/settings.py
Manages application configuration, plugins, auto mode, and model mode.
"""

from __future__ import annotations

from fastapi import APIRouter

import config_manager
from backend.api.schemas.contracts import SettingsResponse, SettingsUpdateRequest
from plugin_manager import get_all_plugin_states, set_plugin_enabled

router = APIRouter(prefix="/api/settings", tags=["settings"])


@router.get("", response_model=SettingsResponse)
def get_settings():
    auto_mode = config_manager.get_auto_mode()
    model_mode = config_manager.get_model_mode()
    curr_model = config_manager.get_current_model()

    api_keys = {
        "openai": bool(config_manager.get_api_key("openai") and config_manager.get_api_key("openai") != "YOUR_OPENAI_KEY"),
        "gemini": bool(config_manager.get_api_key("gemini") and config_manager.get_api_key("gemini") != "YOUR_GEMINI_KEY"),
        "groq": bool(config_manager.get_api_key("groq") and config_manager.get_api_key("groq") != "YOUR_GROQ_KEY"),
    }

    plugins = get_all_plugin_states() or {}

    return SettingsResponse(
        auto_mode=auto_mode,
        model_mode=model_mode,
        current_model=curr_model,
        api_keys_configured=api_keys,
        plugins=plugins,
    )


@router.patch("")
def update_settings(req: SettingsUpdateRequest):
    if req.auto_mode is not None:
        config_manager.set_auto_mode(req.auto_mode)

    if req.model_mode is not None:
        config_manager.set_model_mode(req.model_mode)

    if req.plugins is not None:
        for name, enabled in req.plugins.items():
            set_plugin_enabled(name, enabled)

    return {"message": "Settings updated"}
