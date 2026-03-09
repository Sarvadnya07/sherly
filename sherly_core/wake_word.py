import pvporcupine
import pyaudio

class SherlyWakeListener:

    def __init__(self):

        self.porcupine = pvporcupine.create(
            keywords=["jarvis"]
        )

        self.pa = pyaudio.PyAudio()

        self.stream = self.pa.open(
            rate=self.porcupine.sample_rate,
            channels=1,
            format=pyaudio.paInt16,
            input=True,
            frames_per_buffer=self.porcupine.frame_length
        )

    def listen(self):

        while True:

            pcm = self.stream.read(self.porcupine.frame_length)
            pcm = memoryview(pcm).cast("h")

            result = self.porcupine.process(pcm)

            if result >= 0:
                print("Sherly Wake Word Detected")
                return True