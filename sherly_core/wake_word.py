import os
import pvporcupine
import pyaudio
import struct


class WakeWordDetector:

    def __init__(self):

        access_key = os.getenv("PVPORCUPINE_ACCESS_KEY")
        if not access_key:
            raise ValueError("PVPORCUPINE_ACCESS_KEY environment variable is not set. Cannot initialize wake word detector.")

        self.porcupine = pvporcupine.create(
            access_key=access_key,
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