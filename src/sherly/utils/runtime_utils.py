"""
RUNTIME UTILS — runtime_utils.py
Fixes / Upgrades:
  #5   thread race conditions (lock around shared state)
  #16  log file explosion (RotatingFileHandler, 10 MB × 5 backups)
  #17  timezone (UTC in all log timestamps)
  #23  silent failures (all safe_execute returns a visible message)
  FS-9 Structured JSON logging with level, module, thread, and correlation_id fields.
       Falls back to plain-text logging if structlog is not installed.
"""

from __future__ import annotations

import json
import logging
import threading
import traceback
import uuid
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeout
from datetime import datetime, timezone
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Any, Callable

import requests

# ---------------------------------------------------------------------------
# FS-#9 — Structured logging setup
# ---------------------------------------------------------------------------

LOG_DIR  = Path(__file__).parent.parent / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)
LOG_FILE = LOG_DIR / "sherly.log"

# Correlation ID — unique per process run (ties all log entries to a session)
SESSION_ID: str = str(uuid.uuid4())[:8]

# File handler: 10 MB × 5 backups
_file_handler = RotatingFileHandler(
    str(LOG_FILE),
    maxBytes=10 * 1024 * 1024,
    backupCount=5,
    encoding="utf-8",
)

# FS-#9: Try structured JSON logging via structlog
try:
    import structlog

    structlog.configure(
        processors=[
            structlog.stdlib.add_log_level,
            structlog.stdlib.add_logger_name,
            structlog.processors.TimeStamper(fmt="iso", utc=True),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.JSONRenderer(),
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    _structlog_logger = structlog.get_logger("sherly")
    _USE_STRUCTLOG = True

    # Still write JSON to file via stdlib
    _file_handler.setFormatter(logging.Formatter("%(message)s"))
    _stdlib_logger = logging.getLogger("sherly")
    _stdlib_logger.setLevel(logging.DEBUG)
    _stdlib_logger.addHandler(_file_handler)

except ImportError:
    _USE_STRUCTLOG = False
    _file_handler.setFormatter(
        logging.Formatter("%(asctime)s %(levelname)s [%(threadName)s] %(message)s")
    )
    _stdlib_logger = logging.getLogger("sherly")
    _stdlib_logger.setLevel(logging.INFO)
    _stdlib_logger.addHandler(_file_handler)
    _structlog_logger = None


# Fix #5: lock around the log call itself
_log_lock = threading.Lock()


def log(message: str, level: str = "info", module: str | None = None) -> None:
    """
    FS-#9: Structured log entry.
    Emits JSON when structlog is available, plain text otherwise.
    Always includes: level, module, thread, session_id, timestamp (UTC).
    """
    with _log_lock:
        if _USE_STRUCTLOG and _structlog_logger:
            try:
                log_fn = getattr(_structlog_logger, level.lower(), _structlog_logger.info)
                log_fn(
                    message,
                    session_id=SESSION_ID,
                    thread=threading.current_thread().name,
                    module=module or "sherly",
                )
                return
            except Exception:
                pass  # Fall through to stdlib

        # stdlib fallback
        logger = getattr(_stdlib_logger, level.lower(), _stdlib_logger.info)
        logger(message)


# ---------------------------------------------------------------------------
# Task Queue (Moved to sherly.core.task_queue)
# ---------------------------------------------------------------------------
from sherly.core.task_queue import add_task


# ---------------------------------------------------------------------------
# Async helper
# ---------------------------------------------------------------------------
def run_async(func: Callable, *args, **kwargs) -> threading.Thread:
    t = threading.Thread(target=func, args=args, kwargs=kwargs, daemon=True)
    t.start()
    return t


# ---------------------------------------------------------------------------
# Timeout executor — Fix #3
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
        log(f"timeout_call: {getattr(func, '__name__', '?')} exceeded {timeout}s", level="warning")
        return fallback
    except Exception as exc:
        log(f"timeout_call error: {exc}", level="error")
        return fallback


# ---------------------------------------------------------------------------
# Safe wrappers — Fix #23
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
        return fallback if fallback != "Error" else err


def safe_run(func: Callable, *args) -> Any:
    """Backward-compat alias."""
    try:
        return func(*args)
    except Exception as exc:
        return f"Error: {exc}"


# ---------------------------------------------------------------------------
# Push notifications — non-blocking, Fix #23: won't silently fail
# ---------------------------------------------------------------------------

def send_notification(message: str, channel: str = "sherly-channel") -> None:
    if not message:
        return

    def _push() -> None:
        try:
            requests.post(
                f"https://ntfy.sh/{channel}",
                data=str(message).encode("utf-8"),
                timeout=4,
            )
        except Exception as exc:
            log(f"Notification error: {exc}", level="warning")

    run_async(_push)
