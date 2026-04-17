import os
from pathlib import Path


import requests
from fastapi import FastAPI, Header, Query, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi import UploadFile, File
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from tools.file_tools import explain_file
from model_manager import ask_model
from runtime_utils import send_notification

app = FastAPI(title="Sherly Remote API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

LOCAL_AGENT_URL = "http://127.0.0.1:5001/execute"
API_KEY = os.getenv("SHERLY_REMOTE_API_KEY", "sherly123")
UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)


class Command(BaseModel):
    text: str


def verify_key(x_api_key: str = Header(default="")):
    if x_api_key != API_KEY:
        raise HTTPException(status_code=403, detail="Unauthorized")
    return True


@app.post("/command")
def send_command(
    cmd: Command,
    key: str = Query(default=""),
    x_api_key: str = Header(default=""),
    _: bool = Depends(verify_key),
):
    provided_key = x_api_key or key
    if provided_key != API_KEY:
        return {"error": "Unauthorized"}

    try:
        response = requests.post(
            LOCAL_AGENT_URL,
            json={"text": cmd.text},
            timeout=8,
        )
        response.raise_for_status()
        payload = response.json()
        return {"response": payload.get("response", "")}
    except Exception as exc:
        return {"error": str(exc)}


@app.post("/upload")
async def upload(
    file: UploadFile = File(...),
    _: bool = Depends(verify_key),
):
    safe_filename = os.path.basename(file.filename)
    path = UPLOAD_DIR / safe_filename
    content = await file.read()
    with path.open("wb") as f:
        f.write(content)

    result = explain_file(str(path), ask_model)
    send_notification(result)

    return {"message": f"Processed {file.filename}"}


app.mount("/", StaticFiles(directory="remote_ui", html=True), name="ui")
