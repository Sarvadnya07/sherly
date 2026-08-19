import platform
import shlex
import subprocess


def run_project(command, timeout=15):
    """Run a project command and capture output safely.

    Uses shell=False to prevent shell metacharacter interpretation.
    The command string is parsed into an argv list via shlex.split().
    """
    try:
        argv = shlex.split(command) if isinstance(command, str) else list(command)
    except ValueError as exc:
        return ("error", f"Command parse error: {exc}")

    try:
        is_posix = platform.system() != "Windows"
        if isinstance(command, str):
            command = shlex.split(command, posix=is_posix)

        result = subprocess.run(
            command,
            shell=False,
            capture_output=True,
            text=True,
            timeout=timeout,
        )

        stdout = (result.stdout or "").strip()
        stderr = (result.stderr or "").strip()

        if result.returncode != 0:
            combined = "\n".join(part for part in [stderr, stdout] if part)
            return ("error", combined or f"Command failed with exit code {result.returncode}.")

        return ("success", stdout or "Project command completed.")

    except subprocess.TimeoutExpired as exc:
        timeout_msg = (exc.stderr or exc.stdout or "").strip()
        return ("error", timeout_msg or f"Command timed out after {timeout} seconds.")
    except FileNotFoundError:
        cmd_name = argv[0] if argv else str(command)
        return ("error", f"Command not found: '{cmd_name}'")
    except Exception as exc:
        return ("error", str(exc))
