import pyautogui

def click(x, y):

    pyautogui.click(x, y)

def type_text(text):

    pyautogui.write(text)

def scroll_down():

    pyautogui.scroll(-500)