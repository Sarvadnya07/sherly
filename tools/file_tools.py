import os


def read_file(path):

    if not os.path.exists(path):
        return None

    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    except:
        return "Unsupported file format"


def explain_file(path, ask_model):

    content = read_file(path)

    if not content:
        return "File not found"

    if content == "Unsupported file format":
        return content

    prompt = f"""
Explain this file clearly.

File content:
{content[:2000]}
"""

    return ask_model(prompt)
