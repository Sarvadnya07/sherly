import os


def detect_project():
    """Detect project type and run command from current working directory."""
    cwd = os.getcwd()

    if os.path.exists(os.path.join(cwd, "main.py")):
        return ("python", "python main.py", os.path.join(cwd, "main.py"))

    if os.path.exists(os.path.join(cwd, "package.json")):
        target = None
        for candidate in ("index.js", "app.js", "server.js"):
            path = os.path.join(cwd, candidate)
            if os.path.exists(path):
                target = path
                break
        return ("node", "npm start", target)

    if os.path.exists(os.path.join(cwd, "manage.py")):
        return ("django", "python manage.py runserver", os.path.join(cwd, "manage.py"))

    return (None, None, None)
