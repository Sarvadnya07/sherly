from scipy.signal import butter, lfilter
from faster_whisper import WhisperModel
import numpy as np

# 'Base' handles fan noise without being too heavy on CPU.
model = WhisperModel("base", device="cpu", compute_type="float32")

def highpass_filter(data, cutoff=300, fs=16000, order=5):
    """Remove low-frequency fan hum before Whisper sees the audio."""
    nyq = 0.5 * fs
    normal_cutoff = cutoff / nyq
    b, a = butter(order, normal_cutoff, btype="high", analog=False)
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

        if info.language != "en" and info.language_probability > 0.5:
            return ""

        return text.strip()
    except Exception as exc:
        print(f"STT Error: {exc}")
        return ""
