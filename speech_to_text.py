from faster_whisper import WhisperModel
import sounddevice as sd
import numpy as np

model = WhisperModel(
    "base",
    device="cpu",
    compute_type="int8"
)


def record_audio(seconds=5):
    print("Listening...")
    audio = sd.rec(
        int(seconds * 16000),
        samplerate=16000,
        channels=1,
        dtype="float32",
    )
    sd.wait()
    return audio.flatten().astype(np.float32)



def transcribe():
    try:
        audio = record_audio()

        segments, _ = model.transcribe(audio)

        text = ""
        for segment in segments:
            text += segment.text

        return text.strip()
    except Exception as e:
        print("STT Error:", e)
        return ""
