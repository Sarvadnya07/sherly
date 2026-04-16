import subprocess


def run_command(command):
    """Run a shell command and return the captured output."""

    if not command:
        return "Please specify a command to run."

    try:
        completed = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            check=False,
            timeout=30,
        )
        output = completed.stdout.strip() or completed.stderr.strip()
        if not output:
            return "Command executed with no output."
        return output
    except subprocess.TimeoutExpired:
        return "Command timed out."
    except Exception as exc:
        return f"Command error: {exc}"


ALLOWED_PREFIXES = ("python", "pip", "git")


def safe_exec(command):
    command = command.strip()
    if not any(command.startswith(prefix) for prefix in ALLOWED_PREFIXES):
        return "Blocked for safety"
    return run_command(command)
