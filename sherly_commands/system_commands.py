import os
import platform
import subprocess
import webbrowser
from pathlib import Path


def run_system_command(text):
    text = text.lower().strip()

    if "open chrome" in text:
        webbrowser.open("https://google.com")
        return "Opening Chrome"

    if "open youtube" in text:
        webbrowser.open("https://youtube.com")
        return "Opening YouTube"

    if "open vscode" in text:
        try:
            subprocess.Popen(["code"], shell=False)
            return "Opening VS Code"
        except FileNotFoundError:
            return "VS Code command 'code' was not found."

    if "open downloads" in text:
        downloads = Path.home() / "Downloads"
        if platform.system() == "Windows":
            os.startfile(downloads)  # type: ignore[attr-defined]
        elif platform.system() == "Darwin":
            subprocess.Popen(["open", str(downloads)], shell=False)
        else:
            subprocess.Popen(["xdg-open", str(downloads)], shell=False)
        return "Opening Downloads"

    if "shutdown computer" in text:
        if platform.system() == "Windows":
            subprocess.run(["shutdown", "/s", "/t", "1"], check=False, shell=False)
            return "Shutting down computer"
        return "Shutdown is only implemented for Windows."

    return None
