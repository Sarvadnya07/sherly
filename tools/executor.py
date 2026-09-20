import platform
import shlex
import subprocess

from safety_guard import classify_command, RiskLevel
from tools.terminal_tools import ALLOWED_PREFIXES

_TIMEOUT_SECONDS = 30


def run_project(command, timeout=_TIMEOUT_SECONDS):
    """Run a project command with the same security contract as safe_exec().

    Gate order (identical to tools.terminal_tools.safe_exec):
      1. shell-chaining operator rejection
      2. executable allowlist (parsed argv[0], not raw string prefix)
      3. safety_guard risk classification (DANGEROUS blocked, CONFIRM rejected)

    Uses shell=False; the command string is parsed into argv via shlex.split().
    Inputs here are project-detection constants (not user text), but the
    execution contract must not be path-dependent.
    """
    if isinstance(command, str):
        if not command.strip():
            return ("error", "No command provided.")
        if any(op in command for op in ("&", ";", "|", "\n")):
            return ("error", "Blocked: command chaining operators are not permitted.")

        is_posix = platform.system() != "Windows"
        try:
            argv = shlex.split(command, posix=is_posix)
        except ValueError as exc:
            return ("error", f"Command parse error: {exc}")

        # Allowlist on the parsed executable token (prevents prefix collisions
        # such as 'pythonista' matching the 'python' prefix).
        if not argv or not any(
            argv[0].lower() == p or argv[0].lower().startswith(p + " ")
            for p in ALLOWED_PREFIXES
        ):
            return ("error", f"Blocked: '{argv[0] if argv else command}' is not in the allowed command list.")

        level = classify_command(command)
        if level == RiskLevel.DANGEROUS:
            return ("error", "Blocked: command classified as dangerous by safety policy.")
        if level == RiskLevel.CONFIRM:
            return ("error", "Blocked: command requires confirmation and cannot be auto-run.")
    else:
        argv = list(command)
        if not argv:
            return ("error", "No command provided.")

    try:
        result = subprocess.run(
            argv,
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
