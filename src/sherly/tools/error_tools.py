import pyperclip


def analyze_error(ask_model):
    """Use the clipboard error text to ask the model for an explanation."""

    error_text = pyperclip.paste().strip()

    if not error_text:
        return "Copy the error text first, then try again."

    prompt = f"""
Explain the error below and suggest steps to fix it.

Error:
{error_text}
"""

    return ask_model(prompt)
