import os
import pvporcupine
import pyaudio
import struct


class WakeWordDetector:
    """Wake-word detector backed by Picovoice Porcupine.

    Requires the PICOVOICE_ACCESS_KEY environment variable to be set.
    Raises ValueError on construction if the key is absent.
    """

    def __init__(self):
        access_key = os.getenv("PICOVOICE_ACCESS_KEY", "").strip()
        if not access_key:
            raise ValueError(
                "PICOVOICE_ACCESS_KEY is not set. "
                "Set it in your environment or .env file."
            )

        self.porcupine = pvporcupine.create(
            access_key=access_key,
            keywords=["jarvis"],
        )

        self.audio = pyaudio.PyAudio()

        self.stream = self.audio.open(
            rate=self.porcupine.sample_rate,
            channels=1,
            format=pyaudio.paInt16,
            input=True,
            frames_per_buffer=self.porcupine.frame_length,
        )

    # ------------------------------------------------------------------
    # Context manager support
    # ------------------------------------------------------------------

    def __enter__(self):
        return self

    def __exit__(self, *_):
        self.close()

    def close(self) -> None:
        """Release native audio and Porcupine resources."""
        try:
            self.stream.stop_stream()
            self.stream.close()
        except Exception:
            pass
        try:
            self.audio.terminate()
        except Exception:
            pass
        try:
            self.porcupine.delete()
        except Exception:
            pass

    # ------------------------------------------------------------------
    # Detection loop
    # ------------------------------------------------------------------

    def listen(self) -> bool:
        while True:
            pcm = self.stream.read(self.porcupine.frame_length)
            pcm = struct.unpack_from(
                "h" * self.porcupine.frame_length,
                pcm,
            )
            result = self.porcupine.process(pcm)
            if result >= 0:
                print("Wake word detected")
                return True