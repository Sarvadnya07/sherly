from fastapi import FastAPI
from pydantic import BaseModel

from command_router import route_command
from runtime_utils import safe_execute, send_notification

app = FastAPI(title="Sherly Local Agent")


class Command(BaseModel):
    text: str


@app.post("/execute")
def execute(cmd: Command):
    try:
        response = route_command(cmd.text)
    except Exception as exc:
        log(f"[RemoteAgent] Execution failed: {exc}", level="error")
        response = "Agent failed to execute command."
    send_notification(response)
    return {"response": response}
