import os
from pathlib import Path

import requests
from fastapi import Depends, FastAPI, File, Header, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from sherly.services.model_manager import ask_model
from sherly.tools.file_tools import explain_file
from sherly.utils.runtime_utils import log, send_notification

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


def verify_key(x_api_key: str = Header(default="")) -> bool:
    if x_api_key != API_KEY:
        raise HTTPException(status_code=403, detail="Unauthorized")
    return True


def _get_upload_path(filename: str) -> Path:
    # 1. Extract only the filename (strips leading directories)
    safe_filename = Path(filename).name
    
    # 2. Prevent empty or relative navigation names
    if safe_filename in {"", ".", ".."}:
        raise HTTPException(status_code=400, detail="Invalid filename")

    # 3. Resolve the path and ensure it sits within the UPLOAD_DIR
    path = (UPLOAD_DIR / safe_filename).resolve()
    if path.parent != UPLOAD_DIR.resolve():
        raise HTTPException(status_code=400, detail="Invalid filename")
    
    return path


@app.post("/command")
def send_command(cmd: Command, _: bool = Depends(verify_key)):
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
        log(f"Error in send_command: {exc}", level="error")
        # Returning generic error prevents info leakage of the exception trace
        return {"error": "Internal server error"}


@app.post("/upload")
async def upload(
    file: UploadFile = File(...),
    _: bool = Depends(verify_key),
):
    # RESOLVED: Uses the robust validation from the main branch
    path = _get_upload_path(file.filename or "")
    
    content = await file.read()
    with path.open("wb") as f:
        f.write(content)

    result = explain_file(str(path), ask_model)
    send_notification(result)

    return {"message": f"Processed {path.name}"}


app.mount("/", StaticFiles(directory="remote_ui", html=True), name="ui")