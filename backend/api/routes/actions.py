"""
ACTIONS, APPROVALS & PREVIEWS ROUTES — backend/api/routes/actions.py
Connects React UI to action_manager, approval queue, preview diff system, and undo stack.
"""

from __future__ import annotations

import os
import secrets

from fastapi import APIRouter, HTTPException, Request

import action_manager
import approval_service
from approval_service import ApprovalError
from backend.api.schemas.contracts import PendingApproval, PreviewChange
from backend.api.websocket.ws_manager import manager
from tools.preview import apply_preview, discard_preview, get_preview
from tools.terminal_tools import safe_exec

router = APIRouter(prefix="/api/actions", tags=["actions"])


def _session_id(request: Request) -> str:
    """Resolve the client identity for approval ownership.

    Prefer an authenticated identity (X-API-Key == the remote gateway key) so
    remote clients get their own scoped identity. Fall back to the client's
    stable header session if provided; otherwise the shared local-desktop
    session. Ownership is enforced server-side; clients cannot escalate by
    spoofing headers because the remote key cannot be guessed.
    """
    remote_key = os.getenv("SHERLY_REMOTE_API_KEY")
    if remote_key and request.headers.get("x-api-key") and secrets.compare_digest(
        request.headers.get("x-api-key", ""), remote_key,
    ):
        return approval_service.REMOTE_SESSION_ID
    client_session = request.headers.get("x-session-id")
    if client_session and len(client_session) <= 128:
        return client_session
    return approval_service.DEFAULT_SESSION_ID


@router.get("/approvals")
def get_pending_approvals(request: Request):
    session_id = _session_id(request)
    pending = action_manager.list_pending_entries(session_id=session_id)
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
async def approve_action(action_id: str, request: Request):
    session_id = _session_id(request)
    try:
        res = action_manager.approve_action(action_id, safe_exec, session_id=session_id)
    except ApprovalError as exc:
        raise HTTPException(status_code=409, detail=exc.public_message) from exc
    except Exception as exc:
        from runtime_utils import log
        log(f"[ActionsRoute] Approve action error: {exc}", level="error")
        raise HTTPException(status_code=500, detail="Failed to approve action.") from exc
    await manager.broadcast_event("action_update", {"action_id": action_id, "status": "approved"})
    return {"message": res}


@router.post("/approvals/{action_id}/reject")
async def reject_action(action_id: str, request: Request):
    session_id = _session_id(request)
    try:
        res = action_manager.cancel_action(action_id, session_id=session_id)
    except ApprovalError as exc:
        raise HTTPException(status_code=409, detail=exc.public_message) from exc
    except Exception as exc:
        from runtime_utils import log
        log(f"[ActionsRoute] Cancel action error: {exc}", level="error")
        raise HTTPException(status_code=500, detail="Failed to cancel action.") from exc
    await manager.broadcast_event("action_update", {"action_id": action_id, "status": "rejected"})
    return {"message": res}


@router.get("/history")
def get_action_history():
    try:
        history = action_manager.get_history()
        return {"history": history}
    except Exception as exc:
        from runtime_utils import log
        log(f"[ActionsRoute] Get history error: {exc}", level="error")
        raise HTTPException(status_code=500, detail="Failed to retrieve action history.") from exc


@router.post("/undo")
def undo_last_action():
    try:
        res = action_manager.undo_last()
    except Exception as exc:
        from runtime_utils import log
        log(f"[ActionsRoute] Undo error: {exc}", level="error")
        raise HTTPException(status_code=500, detail="Failed to undo action.") from exc
    return {"message": res}


@router.get("/previews/{action_id}")
def get_preview_route(action_id: str, request: Request):
    session_id = _session_id(request)
    changes = get_preview(action_id, session_id=session_id)
    if not changes:
        # Same response for unknown AND foreign previews: no existence oracle.
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
async def apply_code_preview(action_id: str, request: Request):
    session_id = _session_id(request)
    try:
        res = apply_preview(action_id, session_id=session_id)
    except Exception as exc:
        from runtime_utils import log
        log(f"[ActionsRoute] Apply preview error: {exc}", level="error")
        raise HTTPException(status_code=500, detail="Failed to apply preview.") from exc
    if res == "Invalid preview ID":
        raise HTTPException(status_code=404, detail="Preview not found")
    await manager.broadcast_event("action_update", {"action_id": action_id, "status": "preview_applied"})
    return {"message": res}


@router.post("/previews/{action_id}/reject")
async def reject_code_preview(action_id: str, request: Request):
    discard_preview(action_id, session_id=_session_id(request))
    # Deliberately identical response whether or not the preview existed or
    # belonged to this session: rejection must not be an existence oracle.
    await manager.broadcast_event("action_update", {"action_id": action_id, "status": "preview_rejected"})
    return {"message": "Preview rejected"}
