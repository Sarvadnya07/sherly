import mss
from PIL import Image
import subprocess


def capture_screen() -> str:
    with mss.mss() as sct:
        # Safely fall back to monitors[0] on headless or single-monitor systems
        monitor = sct.monitors[1] if len(sct.monitors) > 1 else sct.monitors[0]
        screenshot = sct.grab(monitor)

        img = Image.frombytes(
            "RGB",
            screenshot.size,
            screenshot.rgb,
        )

        img.save("screen.png")

        return "screen.png"


def analyze_screen() -> str:
    try:
        img_path = capture_screen()
        result = subprocess.run(
            ["ollama", "run", "llava", img_path],
            input="Explain what is on the screen.",
            capture_output=True,
            text=True,
            timeout=30,
        )
        if result.returncode != 0:
            return f"Screen analysis failed: {(result.stderr or '').strip()}"
        return result.stdout or result.stderr or "No screen output generated."
    except subprocess.TimeoutExpired:
        return "Screen analysis timed out after 30 seconds."
    except Exception as exc:
        return f"Screen analysis error: {exc}"

