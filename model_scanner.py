import subprocess


def get_local_models():
    try:
        result = subprocess.run(
            ["ollama", "list"],
            capture_output=True,
            text=True
        )

        lines = result.stdout.split("\n")[1:]
        models = []

        for line in lines:
            if line.strip():
                models.append(line.split()[0])

        return models

    except:
        return []