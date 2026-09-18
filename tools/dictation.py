from speech_to_text import transcribe


def start_dictation():
    # One-shot dictation keeps the assistant responsive in ultra-light mode.
    text = transcribe()
    if text:
        import pyautogui

        pyautogui.write(text + " ")
    return text
