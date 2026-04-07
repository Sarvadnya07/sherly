import pyautogui
from speech_to_text import transcribe


def start_dictation():
    # One-shot dictation keeps the assistant responsive in ultra-light mode.
    text = transcribe()
    if text:
        pyautogui.write(text + " ")
    return text
