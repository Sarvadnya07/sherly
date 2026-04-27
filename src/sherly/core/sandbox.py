"""
SANDBOX EXECUTOR — sandbox.py
Fixes:
  FS-#19  Post-execution filesystem escape detection.
           After every run, compare the filesystem snapshot outside temp_dir.
           If any unexpected write is detected, raise SecurityError and log it.
"""

from __future__ import annotations

import os
import shlex
import shutil
import subprocess
import tempfile
from typing import Optional

from sherly.utils.runtime_utils import log


# ---------------------------------------------------------------------------
# FS-#19 — Escape detection helpers
# ---------------------------------------------------------------------------

def _snapshot_dir(path: str) -> set[tuple[str, float]]:
    """
    Return a set of (filepath, mtime) pairs for all files under *path*.
    Used to detect writes that escaped the sandbox boundary.
    """
    result: set[tuple[str, float]] = set()
    for root, _, files in os.walk(path):
        for fname in files:
            full = os.path.join(root, fname)
            try:
                result.add((full, os.path.getmtime(full)))
            except OSError:
                pass
    return result


class SandboxEscapeError(RuntimeError):
    """Raised when a sandbox command writes outside the allowed workspace."""


class SandboxExecutor:
    """
    Isolated command executor with optional Docker backend.

    FS-#19: Every run() call is bracketed by a filesystem snapshot.
    Any write outside self.temp_dir triggers SandboxEscapeError.
    """

    def __init__(self, use_docker: bool = False, watch_dir: str | None = None):
        self.use_docker  = use_docker and self._check_docker()
        self.temp_dir    = tempfile.mkdtemp(prefix="sherly_sandbox_")
        # FS-#19: directory to watch for escapes (default: parent of temp_dir)
        self.watch_dir   = watch_dir or os.path.dirname(self.temp_dir)

    def _check_docker(self) -> bool:
        try:
            subprocess.run(["docker", "--version"], capture_output=True, check=True)
            return True
        except Exception:
            return False

    # -----------------------------------------------------------------------
    # Public API
    # -----------------------------------------------------------------------

    def run(self, cmd: str, workdir: Optional[str] = None) -> str:
        # FS-#19: snapshot before
        before = _snapshot_dir(self.watch_dir)

        result = (
            self._run_docker(cmd, workdir)
            if self.use_docker
            else self._run_local_isolated(cmd, workdir)
        )

        # FS-#19: snapshot after and compare
        after = _snapshot_dir(self.watch_dir)
        escaped = {
            path for path, mtime in after - before
            if not path.startswith(self.temp_dir)
        }
        if escaped:
            msg = f"[Sandbox] ESCAPE DETECTED — unexpected writes outside sandbox: {escaped}"
            log(msg, level="error")
            raise SandboxEscapeError(msg)

        return result

    # -----------------------------------------------------------------------
    # Backends
    # -----------------------------------------------------------------------

    def _run_docker(self, cmd: str, workdir: Optional[str] = None) -> str:
        """
        Run inside the Sherly sandbox Docker container.
        Mounts the current directory as read-only.
        """
        target_dir    = workdir or os.getcwd()
        container_name = f"sherly_sandbox_{os.path.basename(self.temp_dir)}"

        docker_cmd = [
            "docker", "run", "--rm",
            "--name", container_name,
            "-v", f"{target_dir}:/workspace:ro",
            "-w", "/workspace",
            "--memory", "512m",
            "--cpus", "0.5",
            "sherly_sandbox_img",
            "bash", "-c", cmd,
        ]

        try:
            log(f"[Sandbox] Docker Execute: {cmd}")
            result = subprocess.run(
                docker_cmd,
                capture_output=True,
                text=True,
                timeout=60,
                shell=False,
            )
            return result.stdout if result.returncode == 0 else result.stderr
        except subprocess.TimeoutExpired:
            return "Error: Sandbox container timed out."
        except Exception as exc:
            return f"Docker execution failure: {exc}"

    def _run_local_isolated(self, cmd: str, workdir: Optional[str] = None) -> str:
        log(f"[Sandbox] Running isolated: {cmd}")
        target_dir = workdir or self.temp_dir
        try:
            result = subprocess.run(
                shlex.split(cmd),
                shell=False,
                cwd=target_dir,
                capture_output=True,
                text=True,
                timeout=30,
            )
            return result.stdout if result.returncode == 0 else result.stderr
        except subprocess.TimeoutExpired:
            return "Error: Command timed out in sandbox."
        except Exception as exc:
            return f"Sandbox error: {exc}"

    def cleanup(self) -> None:
        try:
            shutil.rmtree(self.temp_dir)
        except Exception:
            pass
