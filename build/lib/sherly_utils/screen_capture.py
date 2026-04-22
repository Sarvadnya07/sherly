import mss
import numpy as np
from PIL import Image

def capture_screen():

    with mss.mss() as sct:

        monitor = sct.monitors[1]
        screenshot = sct.grab(monitor)

        img = Image.frombytes(
            "RGB",
            screenshot.size,
            screenshot.rgb
        )

        return img