import logging
from datetime import datetime
from pathlib import Path
from queue import Queue

import requests

task_queue = Queue()

LOG_FILE = Path("logs") / "sherly.log"
LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
logging.basicConfig(
    filename=str(LOG_FILE),
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
)


def log(message):
    logging.info(message)


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
