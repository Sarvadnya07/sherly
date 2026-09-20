"""
SHERLY LOCAL AGENT — remote_agent/agent.py

FastAPI service bound to localhost that executes natural-language commands
through the canonical command_router on behalf of the remote PWA.

SECURITY BOUNDARY (SEC-004 remediation):
  This service has no authentication of its own and MUST only be reachable
  from 127.0.0.1 on a trusted machine. The remote_api gateway
  (remote_api/server.py) — which requires SHERLY_REMOTE_API_KEY — is the only
  supported way to reach it from another device. Always run this agent with
  HOST/PORT defaults unchanged (loopback).

UNDO BOUNDARY:
  Undo intentionally has NO remote path. Undo state lives inside the running
  backend process and a remote caller cannot prove session ownership of the
  action it would revert. /execute therefore answers any undo request with an
  explicit rejection instead of silently forwarding privileged behavior.
"""

from fastapi import FastAPI
from pydantic import BaseModel

from approval_service import REMOTE_SESSION_ID
from command_router import route_command
from runtime_utils import send_notification, log

# Loopback-only bind contract. Bind failures on non-loopback hosts are a
# deployment error, not a supported configuration.
HOST = "127.0.0.1"
PORT = 5001

app = FastAPI(title="Sherly Local Agent")


class Command(BaseModel):
    text: str


def _is_undo_request(text: str) -> bool:
    low = (text or "").strip().lower()
    return low in {"undo", "undo last", "undo last action"} or low.startswith("undo ")


@app.post("/execute")
def execute(cmd: Command):
    if _is_undo_request(cmd.text):
        log("[RemoteAgent] rejected remote undo request (session ownership cannot be proven)")
        return {
            "response": (
                "Undo is not available over remote access. "
                "Run undo from the local Sherly workspace."
            )
        }
    try:
        response = route_command(cmd.text, session_id=REMOTE_SESSION_ID)
    except Exception as exc:
        log(f"[RemoteAgent] Execution failed: {exc}", level="error")
        response = "Agent failed to execute command."
    send_notification(response)
    return {"response": response}
