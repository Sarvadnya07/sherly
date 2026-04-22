from fastapi import FastAPI
from pydantic import BaseModel

from command_router import route_command
from runtime_utils import safe_execute, send_notification

app = FastAPI(title="Sherly Local Agent")


class Command(BaseModel):
    text: str


@app.post("/execute")
def execute(cmd: Command):
    response = safe_execute(
        lambda: route_command(cmd.text),
        "Agent failed to execute command.",
    )
    send_notification(response)
    return {"response": response}
