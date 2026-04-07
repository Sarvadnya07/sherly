import os


def scan_project(path, ask_model):
    if not path:
        path = os.getcwd()

    if not os.path.exists(path):
        return "Folder not found"

    files = []
    for root, dirs, filenames in os.walk(path):
        for filename in filenames:
            if filename.endswith((".py", ".js", ".txt")):
                files.append(os.path.join(root, filename))

    summary = ""
    for target in files[:5]:
        try:
            with open(target, "r", encoding="utf-8") as handle:
                summary += f"\nFILE: {target}\n"
                summary += handle.read()[:500]
        except Exception:
            pass

    prompt = f"""
Analyze this project structure and explain:

{summary}
"""

    return ask_model(prompt)
