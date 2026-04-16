"""
INPUT LAYER — speech_to_text.py
Fixes:  #1  audio device chaos (auto-select best mic, fallback to default)
         #2  buffer overflow / freeze (hard recording timeout, blocksize guard)
         #18 speech overlap (don't listen while TTS is speaking)
"""

from __future__ import annotations

import threading
import time

import numpy as np
import sounddevice as sd
from faster_whisper import WhisperModel

# ---------------------------------------------------------------------------
# Model — ultra-light profile
# ---------------------------------------------------------------------------
model = WhisperModel("tiny", device="cpu", compute_type="int8")

# ---------------------------------------------------------------------------
# Audio thresholds
# ---------------------------------------------------------------------------
_SAMPLE_RATE       = 16_000
_RECORD_SECONDS    = 4          # hard max recording window
_RECORD_TIMEOUT    = 6.0        # wall-clock abort (Fix #2)
_SILENCE_THRESHOLD = 0.006
_FLOOR_RMS         = 0.002
_MIN_TEXT_CHARS    = 4
_MAX_TEXT_CHARS    = 400

# ---------------------------------------------------------------------------
# Fix #18 – speech-overlap gate
# ---------------------------------------------------------------------------
_speaking = threading.Event()   # set while TTS is active

def mark_speaking(active: bool) -> None:
    """Call from text_to_speech: True=started, False=finished."""
    if active:
        _speaking.set()
    else:
        _speaking.clear()

def is_speaking() -> bool:
    return _speaking.is_set()

# ---------------------------------------------------------------------------
# Fix #1 – device auto-selection
# ---------------------------------------------------------------------------

def _pick_input_device() -> int | None:
    """
    Return the device index for the best available input device.
    Priority: first non-virtual, non-loopback microphone.
    Falls back to sounddevice default (None = use system default).
    """
    try:
        devices = sd.query_devices()
        for idx, dev in enumerate(devices):
            if dev.get("max_input_channels", 0) > 0:
                name = dev.get("name", "").lower()
                # Skip virtual / loopback devices
                if any(skip in name for skip in ("loopback", "virtual", "stereo mix", "what u hear")):
                    continue
                return idx
    except Exception:
        pass
    return None   # let sounddevice use system default

_input_device: int | None = _pick_input_device()

# ---------------------------------------------------------------------------
# Audio helpers
# ---------------------------------------------------------------------------

def record_audio(seconds: float = _RECORD_SECONDS, fs: int = _SAMPLE_RATE) -> np.ndarray | None:
    """
    Capture audio from the selected mic.
    Fix #2: wrapped in a thread with hard wall-clock timeout.
    """
    result: list[np.ndarray] = []
    error: list[Exception] = []

    def _record():
        try:
            audio = sd.rec(
                int(seconds * fs),
                samplerate=fs,
                channels=1,
                dtype="float32",
                device=_input_device,
                blocksize=1024,       # Fix #2: explicit blocksize avoids buffer drift
            )
            sd.wait()
            result.append(audio.flatten())
        except Exception as exc:
            error.append(exc)

    t = threading.Thread(target=_record, daemon=True)
    t.start()
    t.join(timeout=_RECORD_TIMEOUT)   # Fix #2: hard timeout

    if t.is_alive():
        # Recording is stuck — abort stream and return None
        try:
            sd.stop()
        except Exception:
            pass
        return None

    if error:
        print(f"[STT] record error: {error[0]}")
        return None

    return result[0] if result else None


def is_silent(audio: np.ndarray) -> bool:
    return float(np.mean(np.abs(audio))) < _SILENCE_THRESHOLD


def _is_noise_floor(audio: np.ndarray) -> bool:
    rms = float(np.sqrt(np.mean(audio ** 2)))
    max_val = float(np.max(np.abs(audio)))
    return max_val < 0.01 or rms < _FLOOR_RMS


def _normalize(audio: np.ndarray) -> np.ndarray:
    max_val = float(np.max(np.abs(audio)))
    return audio / max_val if max_val > 0 else audio

# ---------------------------------------------------------------------------
# Transcription
# ---------------------------------------------------------------------------

def transcribe() -> str:
    """
    Record and transcribe.
    Returns "" (silent / noise), "Didn't catch that" (low confidence),
    or the clean transcription text.
    """
    # Fix #18: don't listen while Sherly is speaking
    if is_speaking():
        return ""

    audio = record_audio()
    if audio is None:
        return ""

    if is_silent(audio):
        return ""

    if _is_noise_floor(audio):
        return ""

    audio = _normalize(audio)

    try:
        segments, info = model.transcribe(
            audio,
            language="en",
            beam_size=5,
            vad_filter=True,
            vad_parameters=dict(min_silence_duration_ms=500),
        )
        text = "".join(seg.text for seg in segments).strip()
    except Exception as exc:
        print(f"[STT] transcription error: {exc}")
        return ""

    if not text or len(text) < _MIN_TEXT_CHARS:
        return "Didn't catch that"

    if len(text) > _MAX_TEXT_CHARS:
        return "Didn't catch that"

    avg_logprob = getattr(info, "avg_logprob", None)
    if avg_logprob is not None and avg_logprob < -1.2:
        return "Didn't catch that"

    return text
