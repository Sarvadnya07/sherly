"""
ACTIONS, APPROVALS & PREVIEWS ROUTES — backend/api/routes/actions.py
Connects React UI to action_manager, approval queue, preview diff system, and undo stack.
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from backend.api.schemas.contracts import PendingApproval, PreviewChange
from backend.api.websocket.ws_manager import manager
import action_manager
from tools.preview import preview_store, apply_preview
from tools.terminal_tools import safe_exec

router = APIRouter(prefix="/api/actions", tags=["actions"])


@router.get("/approvals")
def get_pending_approvals():
    pending = action_manager._pending_actions
    res = []
    for aid, entry in pending.items():
        res.append(
            PendingApproval(
                action_id=aid,
                command=entry.get("cmd", ""),
                level=entry.get("level", "confirm"),
                timestamp=entry.get("ts", 0.0),
            )
        )
    return res


@router.post("/approvals/{action_id}/approve")
async def approve_action(action_id: str):
    res = action_manager.approve_action(action_id, safe_exec)
    await manager.broadcast_event("action_update", {"action_id": action_id, "status": "approved"})
    return {"message": res}


@router.post("/approvals/{action_id}/reject")
async def reject_action(action_id: str):
    res = action_manager.cancel_action(action_id)
    await manager.broadcast_event("action_update", {"action_id": action_id, "status": "rejected"})
    return {"message": res}


@router.get("/history")
def get_action_history():
    history = action_manager.get_history()
    return {"history": history}


@router.post("/undo")
def undo_last_action():
    res = action_manager.undo_last()
    return {"message": res}


@router.get("/previews/{action_id}")
def get_preview(action_id: str):
    changes = preview_store.get(action_id)
    if not changes:
        raise HTTPException(status_code=404, detail="Preview not found")
    res = []
    for c in changes:
        res.append(
            PreviewChange(
                action_id=action_id,
                file_path=c.get("file", ""),
                old_code=c.get("old", ""),
                new_code=c.get("new", ""),
                reason=c.get("reason"),
            )
        )
    return res


@router.post("/previews/{action_id}/apply")
async def apply_code_preview(action_id: str):
    res = apply_preview(action_id)
    await manager.broadcast_event("action_update", {"action_id": action_id, "status": "preview_applied"})
    return {"message": res}


@router.post("/previews/{action_id}/reject")
async def reject_code_preview(action_id: str):
    if action_id in preview_store:
        del preview_store[action_id]
    await manager.broadcast_event("action_update", {"action_id": action_id, "status": "preview_rejected"})
    return {"message": "Preview rejected"}
