"""
FILES & WORKSPACE ROUTES — backend/api/routes/files.py
Handles file tree scanning, file reading/writing, and terminal execution.
"""

from __future__ import annotations

import sys
import subprocess
from pathlib import Path
from fastapi import APIRouter, HTTPException

from backend.api.schemas.contracts import (
    FileNode, FileReadResponse, FileWriteRequest, TerminalRunRequest, TerminalRunResponse
)

router = APIRouter(prefix="/api/files", tags=["files"])


@router.get("/tree", response_model=FileNode)
def get_file_tree():
    root_path = Path.cwd()
    exclude = {".git", ".pytest_cache", "__pycache__", ".ruff_cache", "venv", ".venv", "node_modules", "dist"}

    def scan_dir(path: Path, max_depth: int = 3) -> FileNode:
        children = []
        if max_depth > 0 and path.is_dir():
            try:
                entries = sorted(list(path.iterdir()), key=lambda p: (not p.is_dir(), p.name.lower()))
                for entry in entries:
                    if entry.name in exclude or entry.name.startswith("."):
                        continue
                    children.append(scan_dir(entry, max_depth - 1))
            except Exception:
                pass
        return FileNode(
            name=path.name,
            path=str(path.relative_to(root_path)),
            is_dir=path.is_dir(),
            children=children if path.is_dir() else None,
        )

    return scan_dir(root_path)


@router.get("/read", response_model=FileReadResponse)
def read_file(path: str):
    target = Path.cwd() / path
    if not target.exists() or not target.is_file():
        raise HTTPException(status_code=404, detail="File not found")
    try:
        content = target.read_text(encoding="utf-8", errors="replace")
        return FileReadResponse(path=path, content=content)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/write")
def write_file(req: FileWriteRequest):
    target = Path.cwd() / req.path
    try:
        target.write_text(req.content, encoding="utf-8")
        return {"message": f"Successfully wrote {req.path}"}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/terminal/run", response_model=TerminalRunResponse)
def run_terminal_command(req: TerminalRunRequest):
    try:
        cmd = ["cmd.exe", "/c", req.command] if sys.platform == "win32" else ["bash", "-c", req.command]
        res = subprocess.run(cmd, capture_output=True, text=True, timeout=15, cwd=str(Path.cwd()))
        return TerminalRunResponse(
            output=res.stdout + ("\n" + res.stderr if res.stderr else ""),
            exit_code=res.returncode,
        )
    except subprocess.TimeoutExpired:
        return TerminalRunResponse(output="[Command timed out after 15 seconds]", exit_code=124)
    except Exception as exc:
        return TerminalRunResponse(output=f"[Error executing command: {exc}]", exit_code=1)
