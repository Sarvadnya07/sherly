"""
FILES & WORKSPACE ROUTES — backend/api/routes/files.py
Handles file tree scanning, file reading/writing, and terminal execution.
"""

from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, HTTPException

import action_manager
from backend.api.schemas.contracts import (
    FileNode,
    FileReadResponse,
    FileWriteRequest,
    TerminalRunRequest,
    TerminalRunResponse,
)
from tools.terminal_tools import safe_exec

router = APIRouter(prefix="/api/files", tags=["files"])


@router.get("/tree", response_model=FileNode)
def get_file_tree():
    root_path = Path.cwd().resolve()
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
            except Exception as exc:
                try:
                    from runtime_utils import log

                    log(f"[FilesRoute] directory scan error for {path}: {exc}", level="warning")
                except Exception:
                    pass
        return FileNode(
            name=path.name,
            path=str(path.relative_to(root_path)),
            is_dir=path.is_dir(),
            children=children if path.is_dir() else None,
        )

    return scan_dir(root_path)


_MAX_READ_BYTES = 5 * 1024 * 1024  # 5 MB


def _get_safe_target(rel_path: str) -> Path:
    workspace_root = Path.cwd().resolve()
    normalized_rel_path = rel_path.replace("\\", "/")
    target = (workspace_root / normalized_rel_path).resolve()
    # Use is_relative_to() to prevent prefix-matching bypass (e.g. /workspace_root_secret)
    try:
        target.relative_to(workspace_root)
    except ValueError as exc:
        raise HTTPException(status_code=403, detail="Access denied: Path outside workspace boundary") from exc
    return target


@router.get("/read", response_model=FileReadResponse)
def read_file(path: str):
    target = _get_safe_target(path)
    if not target.exists() or not target.is_file():
        raise HTTPException(status_code=404, detail="File not found")
    try:
        if target.stat().st_size > _MAX_READ_BYTES:
            raise HTTPException(status_code=413, detail="File too large to read via API (limit 5 MB)")
        content = target.read_text(encoding="utf-8", errors="replace")
        return FileReadResponse(path=path, content=content)
    except HTTPException:
        raise
    except Exception as exc:
        from runtime_utils import log
        log(f"[FilesRoute] Failed to read file {path}: {exc}", level="error")
        raise HTTPException(status_code=500, detail="Failed to read file.") from exc


@router.post("/write")
def write_file(req: FileWriteRequest):
    target = _get_safe_target(req.path)
    # Conflict check: refuse to silently clobber an externally-modified file.
    if target.exists() and target.is_file():
        try:
            current = target.read_text(encoding="utf-8", errors="replace")
        except Exception as exc:
            from runtime_utils import log
            log(f"[FilesRoute] Failed to read file before write {req.path}: {exc}", level="error")
            raise HTTPException(status_code=500, detail="Unable to verify current file state.") from exc
        if req.expected_content is not None and current != req.expected_content:
            raise HTTPException(status_code=409, detail="Conflict: file was modified since it was loaded. Reload and retry.")
    try:
        target.parent.mkdir(parents=True, exist_ok=True)
        # Route through the canonical undo/backup pipeline so direct editor
        # writes are recoverable exactly like chat-driven patches.
        msg = action_manager.write_file_safe(str(target), req.content)
        if msg.startswith("Write failed"):
            raise RuntimeError(msg)
        return {"message": f"Successfully wrote {req.path}"}
    except HTTPException:
        raise
    except Exception as exc:
        from runtime_utils import log
        log(f"[FilesRoute] Failed to write file {req.path}: {exc}", level="error")
        raise HTTPException(status_code=500, detail="Failed to write file.") from exc


@router.post("/terminal/run", response_model=TerminalRunResponse)
def run_terminal_command(req: TerminalRunRequest):
    try:
        output = safe_exec(req.command)
        exit_code = 1 if output.startswith("⛔ Blocked:") or output.startswith("Command error:") or output.startswith("⚠️") else 0
        return TerminalRunResponse(
            output=output,
            exit_code=exit_code,
        )
    except Exception as exc:
        return TerminalRunResponse(output=f"[Error executing command: {exc}]", exit_code=1)
