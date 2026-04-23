import pyautogui
import time
import pyperclip


def get_selected_text():

    pyautogui.hotkey("ctrl", "c")
    time.sleep(0.3)
    text = pyperclip.paste()

    if text:
        return text

    return None

def explain_code(code, ask_llm):

    prompt = f"""
Explain the following code clearly for a developer.

Code:
{code}

Explain the logic in simple terms.
"""

    return ask_llm(prompt)