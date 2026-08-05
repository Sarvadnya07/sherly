import os
import pvporcupine
import pyaudio
import struct

# SECURITY: API keys must be loaded securely via environment variables, never hardcoded.
ACCESS_KEY = os.getenv("PVPORCUPINE_ACCESS_KEY")
if not ACCESS_KEY:
    raise ValueError("PVPORCUPINE_ACCESS_KEY environment variable is missing")


class WakeWordDetector:

    def __init__(self):

        self.porcupine = pvporcupine.create(
            access_key=ACCESS_KEY,
            keywords=["jarvis"]
        )

        self.audio = pyaudio.PyAudio()

        self.stream = self.audio.open(
            rate=self.porcupine.sample_rate,
            channels=1,
            format=pyaudio.paInt16,
            input=True,
            frames_per_buffer=self.porcupine.frame_length
        )

    def listen(self):

        while True:

            pcm = self.stream.read(self.porcupine.frame_length)

            pcm = struct.unpack_from(
                "h" * self.porcupine.frame_length,
                pcm
            )

            result = self.porcupine.process(pcm)

            if result >= 0:
                print("Wake word detected")
                return True