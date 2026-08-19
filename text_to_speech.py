"""
TTS LAYER — text_to_speech.py
Fixes: #18 speech overlap (marks speaking state so STT won't listen)
"""

from __future__ import annotations

import time
import threading
import pyttsx3
try:
    import keyboard
except ImportError:
    keyboard = None

_engine = None
_stop_requested = threading.Event()


def stop_tts() -> None:
    """Programmatically cancel active TTS playback."""
    _stop_requested.set()


def _get_engine() -> pyttsx3.Engine:
    global _engine
    if _engine is None:
        _engine = pyttsx3.init()
        _engine.setProperty("rate", 170)
        voices = _engine.getProperty("voices")
        if voices is not None and len(voices) > 1:
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

    _stop_requested.clear()
    mark_speaking(True)
    engine = _get_engine()
    try:
        engine.say(text)
        engine.startLoop(False)

        while engine.isBusy():
            if _stop_requested.is_set() or (keyboard and keyboard.is_pressed("esc")):
                engine.stop()
                break
            engine.iterate()
            time.sleep(0.01)  # prevent busy-wait CPU spin

        engine.endLoop()

    except Exception as exc:
        print(f"[TTS] Error: {exc}")
        try:
            engine.endLoop()
        except Exception:
            pass
    finally:
        _stop_requested.clear()
        mark_speaking(False)


def sherly_speak(text: str) -> None:
    """Compatibility wrapper used by sherly_core callers."""
    speak(text)
