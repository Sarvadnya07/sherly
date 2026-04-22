"""
TTS LAYER — text_to_speech.py
Fixes: #18 speech overlap (marks speaking state so STT won't listen)
"""

from __future__ import annotations

import pyttsx3
import keyboard

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
    """
    Speak *text* via pyttsx3.
    Fix #18: marks speaking state in speech_to_text so the mic loop
             never captures Sherly's own voice.
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