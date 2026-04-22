import os
import subprocess
import webbrowser


def run_system_command(text):

    text = text.lower()

    if "open chrome" in text:
        webbrowser.open("https://google.com")
        return "Opening Chrome"

    if "open youtube" in text:
        webbrowser.open("https://youtube.com")
        return "Opening YouTube"

    if "open vscode" in text:
        subprocess.Popen("code")
        return "Opening VS Code"

    if "open downloads" in text:
        os.startfile("C:\\Users\\ASUS\\Downloads")
        return "Opening Downloads"

    if "shutdown computer" in text:
        os.system("shutdown /s /t 1")
        return "Shutting down computer"

    return None