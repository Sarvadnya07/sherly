import pyautogui
import time


def open_app(name):

    pyautogui.press("win")
    time.sleep(1)

    pyautogui.write(name)
    time.sleep(1)

    pyautogui.press("enter")

    return f"Opening {name}"


def type_text(text):
    pyautogui.write(text)
    return "Typed text"


def click(x, y):
    pyautogui.click(x, y)
    return "Clicked"
