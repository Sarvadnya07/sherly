from faster_whisper import WhisperModel
import sounddevice as sd
import numpy as np

# Ultra-light STT profile to reduce RAM and startup cost.
model = WhisperModel("tiny", device="cpu", compute_type="int8")

def record_audio(seconds=4, fs=16000):
    """Records audio from the default microphone."""
    audio = sd.rec(
        int(seconds * fs),
        samplerate=fs,
        channels=1,
        dtype="float32"
    )
    sd.wait()
    return audio.flatten()

def is_silent(audio, threshold=0.005):
    """Return True when the captured audio is effectively silence."""
    volume = float(np.mean(np.abs(audio)))
    return volume < threshold

def transcribe():
    """Converts recorded audio to text using faster-whisper with noise filtering."""
    try:
        audio = record_audio()

        if is_silent(audio):
            return ""

        rms = np.sqrt(np.mean(audio**2))
        max_val = np.max(np.abs(audio))

        # Noise Threshold: Only process if signal is above floor noise
        if max_val < 0.01 or rms < 0.001:
            return ""

        # Normalize only if we have a real signal
        audio = audio / max_val if max_val > 0 else audio

        # Transcribe with VAD (Voice Activity Detection) parameters
        segments, _ = model.transcribe(
            audio,
            language="en",
            beam_size=5,
            vad_filter=True,
            vad_parameters=dict(min_silence_duration_ms=500)
        )

        text = "".join(segment.text for segment in segments)
        text = text.strip()
        if not text or len(text) < 3:
            return "Didn't catch that"
        return text

    except Exception as e:
        print(f"STT Error: {e}")
        return ""
