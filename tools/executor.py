import subprocess
from safety_guard import check_command


def run_project(command, timeout=15):
    """Run a project command and capture output safely."""
    # 🛡️ Sentinel: Validate command to prevent injection before passing to shell=True
    guard_result = check_command(command)
    if guard_result is not None:
        return ("error", guard_result)

    try:
        result = subprocess.run(
            command,
            shell=True,
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
    except Exception as exc:
        return ("error", str(exc))
