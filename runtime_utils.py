from datetime import datetime
from pathlib import Path
from queue import Queue
import requests

task_queue = Queue()

LOG_FILE = Path("logs") / "sherly.log"


def log(message):
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with LOG_FILE.open("a", encoding="utf-8") as handle:
        handle.write(f"[{timestamp}] {message}\n")


def safe_execute(func, fallback="Error"):
    try:
        return func()
    except Exception as exc:
        error = f"Error: {exc}"
        log(error)
        return fallback if fallback != "Error" else error


def send_notification(message, channel="sherly-channel"):
    if not message:
        return
    try:
        requests.post(
            f"https://ntfy.sh/{channel}",
            data=str(message).encode("utf-8"),
            timeout=4,
        )
    except Exception as exc:
        log(f"Notification error: {exc}")


def safe_run(func, *args):
    try:
        return func(*args)
    except Exception as exc:
        return f"Error: {exc}"
