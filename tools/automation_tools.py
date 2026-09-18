import time

def _pyautogui():
    import pyautogui
    return pyautogui


def open_app(name):

    pyautogui = _pyautogui()
    pyautogui.press("win")
    time.sleep(0.5)

    pyautogui.write(name)
    time.sleep(0.5)

    pyautogui.press("enter")
    time.sleep(2.5) # Wait for the application to actually open and gain focus

    return f"Opening {name}"


def type_text(text):
    pyautogui = _pyautogui()
    pyautogui.write(text)
    return "Typed text"


def click(x, y):
    pyautogui = _pyautogui()
    pyautogui.click(x, y)
    return "Clicked"
