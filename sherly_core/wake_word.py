import pvporcupine
import pyaudio
import struct

ACCESS_KEY = "Zz/U5F+h4KHgbupOmaDU8qGYLnK8HWU20+8s8IJCrGwrnaRav9Qsqg=="


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