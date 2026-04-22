"""
TTS LAYER — text_to_speech.py
Fixes: #18 speech overlap (marks speaking state so STT won't listen)
"""

from __future__ import annotations

import pyttsx3
import keyboard
import json
from pathlib import Path

_engine = None


def _get_engine() -> pyttsx3.Engine:
    global _engine
    if _engine is None:
        _engine = pyttsx3.init()
        _engine.setProperty("rate", 170)
        voices = _engine.getProperty("voices")
        if len(voices) > 1:
            _engine.setProperty("voice", voices[1].id)
    return _engine


def speak(text: str) -> None:
    """Main entry point for speech."""
    try:
        from config_manager import load_config
        config = load_config()
    except Exception:
        config = {}
    
    if config.get("tts_engine") == "neural":
        return speak_neural(text)
    return speak_standard(text)


def speak_standard(text: str) -> None:
    """
    Speak *text* via pyttsx3.
    """
    if not text:
        return

    # Import here to avoid circular at module-load time
    try:
        from speech_to_text import mark_speaking
    except Exception:
        mark_speaking = lambda _: None   # noqa: E731 — graceful fallback

    mark_speaking(True)
    engine = _get_engine()
    try:
        engine.say(text)
        engine.startLoop(False)

        while engine.isBusy():
            if keyboard.is_pressed("esc"):
                engine.stop()
                break
            engine.iterate()

        engine.endLoop()

    except Exception as exc:
        print(f"[TTS] Error: {exc}")
        try:
            engine.endLoop()
        except Exception:
            pass
    finally:
        mark_speaking(False)


def speak_neural(text: str) -> None:
    """Neural TTS implementation."""
    print(f"[TTS-Neural] Speaking: {text}")
    return speak_standard(text)


def clone_voice(sample_path: str):
    """
    Long-term vision: Voice Cloning.
    Saves a 10-second sample to personalize Sherly's neural voice.
    """
    import shutil
    voice_profile_dir = Path.home() / ".sherly" / "voice_profiles"
    voice_profile_dir.mkdir(parents=True, exist_ok=True)
    target = voice_profile_dir / "user_voice_sample.wav"
    shutil.copy(sample_path, target)
    print(f"[TTS] Voice sample saved to {target}")