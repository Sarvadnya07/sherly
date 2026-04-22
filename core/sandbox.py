import os
import subprocess
import shutil
import tempfile
import shlex
from typing import Optional, List
from runtime_utils import log

class SandboxExecutor:
    def __init__(self, use_docker: bool = False):
        self.use_docker = use_docker and self._check_docker()
        self.temp_dir = tempfile.mkdtemp(prefix="sherly_sandbox_")

    def _check_docker(self) -> bool:
        try:
            subprocess.run(["docker", "--version"], capture_output=True, check=True)
            return True
        except Exception:
            return False

    def run(self, cmd: str, workdir: Optional[str] = None) -> str:
        if self.use_docker:
            return self._run_docker(cmd, workdir)
        else:
            return self._run_local_isolated(cmd, workdir)

    def _run_docker(self, cmd: str, workdir: Optional[str] = None) -> str:
        """
        Run command inside the Sherly sandbox container.
        Mounts the current directory as read-only.
        """
        target_dir = workdir or os.getcwd()
        container_name = f"sherly_sandbox_{os.path.basename(self.temp_dir)}"
        
        # docker run --rm -v {host_dir}:/workspace:ro -w /workspace sherly_sandbox_img {cmd}
        docker_cmd = [
            "docker", "run", "--rm",
            "--name", container_name,
            "-v", f"{target_dir}:/workspace:ro",
            "-w", "/workspace",
            "--memory", "512m",
            "--cpus", "0.5",
            "sherly_sandbox_img",
            "bash", "-c", cmd
        ]
        
        try:
            log(f"[Sandbox] Docker Execute: {cmd}")
            result = subprocess.run(
                docker_cmd,
                capture_output=True,
                text=True,
                timeout=60,
                shell=False
            )
            return result.stdout if result.returncode == 0 else result.stderr
        except subprocess.TimeoutExpired:
            return "Error: Sandbox container timed out."
        except Exception as e:
            return f"Docker execution failure: {e}"

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
                timeout=30
            )
            return result.stdout if result.returncode == 0 else result.stderr
        except subprocess.TimeoutExpired:
            return "Error: Command timed out in sandbox."
        except Exception as e:
            return f"Sandbox error: {e}"

    def cleanup(self):
        try:
            shutil.rmtree(self.temp_dir)
        except Exception:
            pass
