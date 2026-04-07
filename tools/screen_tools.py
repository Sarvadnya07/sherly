import mss
from PIL import Image
import subprocess


def capture_screen():

    with mss.mss() as sct:
        monitor = sct.monitors[1]
        screenshot = sct.grab(monitor)

        img = Image.frombytes(
            "RGB",
            screenshot.size,
            screenshot.rgb
        )

        img.save("screen.png")

        return "screen.png"


def analyze_screen():

    capture_screen()

    result = subprocess.run(
        ["ollama", "run", "llava"],
        input="Explain what is on the screen.",
        capture_output=True,
        text=True
    )

    return result.stdout
