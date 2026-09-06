"""
VOICE ROUTES — backend/api/routes/voice.py
Handles microphone querying, STT status, voice recording triggers, and TTS cancellation.
"""

from __future__ import annotations

import sounddevice as sd
from fastapi import APIRouter

import speech_to_text
import text_to_speech
from backend.api.schemas.contracts import AudioDevicesResponse, VoiceStatusResponse
from backend.api.websocket.ws_manager import manager

router = APIRouter(prefix="/api/voice", tags=["voice"])


@router.get("/status", response_model=VoiceStatusResponse)
def get_voice_status():
    return VoiceStatusResponse(
        is_listening=False,
        is_speaking=speech_to_text.is_speaking(),
        current_device="System Default Microphone",
    )


@router.get("/devices", response_model=AudioDevicesResponse)
def get_audio_devices():
    device_names = []
    try:
        devices = sd.query_devices()
        for dev in devices:
            if dev.get("max_input_channels", 0) > 0:
                name = dev.get("name", "")
                if name and name not in device_names:
                    device_names.append(name)
    except Exception as exc:
        try:
            from runtime_utils import log

            log(f"[VoiceRoute] device enumeration failed: {exc}", level="warning")
        except Exception:
            pass
    if not device_names:
        device_names = ["System Default Microphone"]
    return AudioDevicesResponse(devices=device_names)


@router.post("/start")
async def start_listening():
    await manager.broadcast_event("status", {"status": "listening"})
    return {"message": "Listening started"}


@router.post("/stop")
async def stop_listening():
    await manager.broadcast_event("status", {"status": "ready"})
    return {"message": "Listening stopped"}


@router.post("/stop_speaking")
async def stop_speaking():
    text_to_speech.stop_tts()
    await manager.broadcast_event("status", {"status": "ready"})
    return {"message": "TTS playback stopped"}
