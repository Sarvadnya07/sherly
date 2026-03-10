from scipy.signal import butter, lfilter
from faster_whisper import WhisperModel
import numpy as np
from typing import Any

# 'Base' handles fan noise without being too heavy on CPU.
model = WhisperModel("base", device="cpu", compute_type="float32")

def highpass_filter(data: Any, cutoff: int = 300, fs: int = 16000, order: int = 5) -> Any:
    """Remove low-frequency fan hum before Whisper sees the audio."""
    nyq = 0.5 * fs
    normal_cutoff = cutoff / nyq
    b, a = butter(order, normal_cutoff, btype="high", analog=False)  # type: ignore
    return lfilter(b, a, data)

def transcribe(audio_data):
    """
    Transcribes raw numpy audio data from sounddevice with a VAD filter.
    """
    try:
        audio_data = np.array(audio_data, dtype=np.float32)

        audio_data = highpass_filter(audio_data)
        audio_data = audio_data.astype(np.float32)

        if np.max(np.abs(audio_data)) > 1.0:
            audio_data = audio_data / np.max(np.abs(audio_data))

        segments, info = model.transcribe(
            audio_data,
            language="en",
            beam_size=5,
            condition_on_previous_text=False,
            vad_filter=True,
            vad_parameters=dict(min_silence_duration_ms=500),
        )

        text = "".join(segment.text for segment in segments)

        return text.strip()
    except Exception as exc:
        print(f"STT Error: {exc}")
        return ""
