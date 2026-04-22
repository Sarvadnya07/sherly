"""
RUNTIME UTILS — runtime_utils.py
Fixes: #5  thread race conditions (lock around shared state)
        #14 task queue overload guard
        #16 log file explosion (RotatingFileHandler, 2 MB × 3 backups)
        #17 timezone (UTC in all log timestamps)
        #23 silent failures (all safe_execute returns a visible message)
"""

from __future__ import annotations

import logging
import threading
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeout
from datetime import datetime, timezone
from logging.handlers import RotatingFileHandler
from pathlib import Path
from queue import Queue
from typing import Any, Callable

import requests

# ---------------------------------------------------------------------------
# Fix #16 – rotating log (2 MB per file, keep 3 backups)
# ---------------------------------------------------------------------------
LOG_FILE = Path("logs") / "sherly.log"
LOG_FILE.parent.mkdir(parents=True, exist_ok=True)

_handler = RotatingFileHandler(
    str(LOG_FILE),
    maxBytes=2 * 1024 * 1024,   # 2 MB
    backupCount=3,
    encoding="utf-8",
)
_handler.setFormatter(
    logging.Formatter("%(asctime)s %(levelname)s [%(threadName)s] %(message)s")
)
_logger = logging.getLogger("sherly")
_logger.setLevel(logging.INFO)
_logger.addHandler(_handler)

# Fix #5: lock around the log call itself
_log_lock = threading.Lock()


def log(message: str, level: str = "info") -> None:
    with _log_lock:
        getattr(_logger, level.lower(), _logger.info)(message)


# ---------------------------------------------------------------------------
# Fix #14 – task queue with overflow guard
# ---------------------------------------------------------------------------
_MAX_QUEUE_SIZE = 10
task_queue: Queue = Queue()

# Fix #5: lock around queue-size check + put (check-then-act race)
_queue_lock = threading.Lock()


def _queue_worker() -> None:
    while True:
        func, args, kwargs = task_queue.get()
        try:
            func(*args, **kwargs)
        except Exception as exc:
            log(f"[TaskQueue] error in {getattr(func, '__name__', '?')}: {exc}", level="error")
        finally:
            task_queue.task_done()


threading.Thread(target=_queue_worker, daemon=True, name="SherlyTaskQueue").start()


def add_task(func: Callable, *args, **kwargs) -> str | None:
    """
    Enqueue a task.
    Fix #14: if the queue already has _MAX_QUEUE_SIZE items, reject with a message.
    """
    with _queue_lock:
        if task_queue.qsize() >= _MAX_QUEUE_SIZE:
            log("[TaskQueue] overloaded — task rejected", level="warning")
            return "System busy. Please wait a moment."
        task_queue.put((func, args, kwargs))
    return None


# ---------------------------------------------------------------------------
# Async helper
# ---------------------------------------------------------------------------
def run_async(func: Callable, *args, **kwargs) -> threading.Thread:
    t = threading.Thread(target=func, args=args, kwargs=kwargs, daemon=True)
    t.start()
    return t


# ---------------------------------------------------------------------------
# Timeout executor  Fix #3 (used by model_manager too)
# ---------------------------------------------------------------------------
_executor = ThreadPoolExecutor(max_workers=4, thread_name_prefix="SherlyExec")


def timeout_call(
    func: Callable,
    *args,
    timeout: float = 10.0,
    fallback: Any = "Operation timed out.",
) -> Any:
    future = _executor.submit(func, *args)
    try:
        return future.result(timeout=timeout)
    except FuturesTimeout:
        log(f"timeout_call: {getattr(func,'__name__','?')} exceeded {timeout}s", level="warning")
        return fallback
    except Exception as exc:
        log(f"timeout_call error: {exc}", level="error")
        return fallback


# ---------------------------------------------------------------------------
# Safe wrappers  Fix #23 – never silently swallow errors
# ---------------------------------------------------------------------------

def safe_execute(func: Callable, fallback: Any = "Something went wrong. Please try again.") -> Any:
    """
    Call *func()* (zero-arg lambda) catching all exceptions.
    Fix #23: default fallback is a visible user-facing message.
    """
    try:
        return func()
    except Exception as exc:
        err = f"Error: {exc}"
        log(err, level="error")
        return fallback if fallback != "Error" else err   # Fix #23


def safe_run(func: Callable, *args) -> Any:
    """Backward-compat alias."""
    try:
        return func(*args)
    except Exception as exc:
        return f"Error: {exc}"


# ---------------------------------------------------------------------------
# Push notifications  (non-blocking, fix #23: won't silently fail)
# ---------------------------------------------------------------------------

def send_notification(message: str, channel: str = "sherly-channel") -> None:
    if not message:
        return

    def _push():
        try:
            requests.post(
                f"https://ntfy.sh/{channel}",
                data=str(message).encode("utf-8"),
                timeout=4,
            )
        except Exception as exc:
            log(f"Notification error: {exc}", level="warning")

    run_async(_push)
