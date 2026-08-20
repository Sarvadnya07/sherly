import os
import secrets
from pathlib import Path

import httpx
from fastapi import FastAPI, Header, HTTPException, Depends
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
    # Restrict to your actual frontend origin(s) in production.
    # For local development, expand this list as needed.
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=False,
    allow_methods=["*"] ,
    allow_headers=["*"],
)

LOCAL_AGENT_URL = os.getenv("SHERLY_LOCAL_AGENT_URL", "http://127.0.0.1:5001/execute")
API_KEY = os.getenv("SHERLY_REMOTE_API_KEY")
UPLOAD_DIR = Path(os.getenv("SHERLY_UPLOAD_DIR", "uploads"))
UPLOAD_DIR.mkdir(exist_ok=True)
UPLOAD_MAX_BYTES = int(os.getenv("SHERLY_UPLOAD_MAX_BYTES", str(10 * 1024 * 1024)))


class Command(BaseModel):
    text: str


def verify_key(x_api_key: str = Header(default="")):
    if not API_KEY or not secrets.compare_digest(x_api_key, API_KEY):
        raise HTTPException(
            status_code=403,
            detail="Unauthorized: Explicit SHERLY_REMOTE_API_KEY environment variable required",
        )
    return True


@app.post("/command")
def send_command(
    cmd: Command,
    _: bool = Depends(verify_key),
):
    try:
        response = httpx.post(
            LOCAL_AGENT_URL,
            json={"text": cmd.text},
            timeout=8,
        )
        response.raise_for_status()
        payload = response.json()
        return {"response": payload.get("response", "")}
    except httpx.HTTPError:
        return {"error": "Remote agent request failed"}
    except ValueError:
        return {"error": "Remote agent returned an invalid response"}


@app.post("/upload")
async def upload(
    file: UploadFile = File(...),
    _: bool = Depends(verify_key),
):
    raw_name = (file.filename or "").strip()
    if not raw_name:
        raise HTTPException(status_code=400, detail="Uploaded file must have a filename")

    safe_filename = Path(raw_name).name
    if not safe_filename:
        raise HTTPException(status_code=400, detail="Invalid filename")

    path = UPLOAD_DIR / safe_filename
    total = 0

    try:
        with path.open("wb") as output:
            while True:
                chunk = await file.read(min(1024 * 1024, UPLOAD_MAX_BYTES - total + 1))
                if not chunk:
                    break
                total += len(chunk)
                if total > UPLOAD_MAX_BYTES:
                    raise HTTPException(status_code=413, detail="Uploaded file exceeds the configured size limit")
                output.write(chunk)

        result = explain_file(str(path), ask_model)
        send_notification(result)
        return {"message": f"Processed {safe_filename}"}
    finally:
        try:
            await file.close()
        except Exception:
            pass


app.mount("/", StaticFiles(directory="remote_ui", html=True), name="ui")
