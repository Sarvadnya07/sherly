"""
OBSERVABILITY ENGINE — sherly_core/observability.py
Implements structured JSON logging, correlation IDs, structural + regex secret redaction,
and deterministic execution timeline tracing.
"""

from __future__ import annotations

import json
import logging
import re
import threading
import time
import uuid
from datetime import datetime, timezone
from typing import Any

# ---------------------------------------------------------------------------
# 1. Structural & Pattern Secret Redaction
# ---------------------------------------------------------------------------

_SENSITIVE_KEYS = {
    "api_key", "apikey", "access_token", "token", "authorization",
    "password", "secret", "private_key", "client_secret", "key",
}

_SECRET_PATTERNS = [
    re.compile(r"sk-[a-zA-Z0-9]{20,}", re.IGNORECASE),
    re.compile(r"Bearer\s+[a-zA-Z0-9_\-\.]{20,}", re.IGNORECASE),
    re.compile(r"AIza[0-9A-Za-z-_]{35}", re.IGNORECASE),
    re.compile(r"gsk_[a-zA-Z0-9]{20,}", re.IGNORECASE),
]


def redact_secrets(data: Any) -> Any:
    """
    Recursively sanitize dictionaries, lists, and strings by:
    1. Replacing values of sensitive keys with '[REDACTED]'
    2. Redacting matching secret patterns from string values
    """
    if isinstance(data, dict):
        sanitized = {}
        for k, v in data.items():
            if str(k).lower() in _SENSITIVE_KEYS:
                sanitized[k] = "[REDACTED]"
            else:
                sanitized[k] = redact_secrets(v)
        return sanitized
    elif isinstance(data, list):
        return [redact_secrets(item) for item in data]
    elif isinstance(data, str):
        cleaned = data
        for pattern in _SECRET_PATTERNS:
            cleaned = pattern.sub("[REDACTED]", cleaned)
        return cleaned
    return data


# ---------------------------------------------------------------------------
# 2. Contextual Correlation Tracking (Thread-Local)
# ---------------------------------------------------------------------------

_context = threading.local()


def set_correlation_context(
    trace_id: str | None = None,
    request_id: str | None = None,
    task_id: str | None = None,
    action_id: str | None = None,
    voice_session_id: str | None = None,
) -> None:
    """Set correlation IDs for the active thread."""
    _context.trace_id = trace_id or getattr(_context, "trace_id", str(uuid.uuid4()))
    _context.request_id = request_id or getattr(_context, "request_id", str(uuid.uuid4())[:8])
    _context.task_id = task_id or getattr(_context, "task_id", None)
    _context.action_id = action_id or getattr(_context, "action_id", None)
    _context.voice_session_id = voice_session_id or getattr(_context, "voice_session_id", None)


def get_correlation_context() -> dict[str, str | None]:
    """Retrieve correlation IDs for the active thread."""
    return {
        "trace_id": getattr(_context, "trace_id", None),
        "request_id": getattr(_context, "request_id", None),
        "task_id": getattr(_context, "task_id", None),
        "action_id": getattr(_context, "action_id", None),
        "voice_session_id": getattr(_context, "voice_session_id", None),
    }


def clear_correlation_context() -> None:
    """Reset correlation IDs for the active thread."""
    _context.trace_id = None
    _context.request_id = None
    _context.task_id = None
    _context.action_id = None
    _context.voice_session_id = None


# ---------------------------------------------------------------------------
# 3. Structured JSON Logging Formatter
# ---------------------------------------------------------------------------

class StructuredJsonFormatter(logging.Formatter):
    """Formats log records as clean, redacted JSON lines."""

    def format(self, record: logging.LogRecord) -> str:
        ctx = get_correlation_context()
        log_payload = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": redact_secrets(record.getMessage()),
            "trace_id": ctx.get("trace_id"),
            "request_id": ctx.get("request_id"),
            "task_id": ctx.get("task_id"),
            "action_id": ctx.get("action_id"),
        }
        if ctx.get("voice_session_id"):
            log_payload["voice_session_id"] = ctx.get("voice_session_id")

        if record.exc_info:
            log_payload["exception"] = self.formatException(record.exc_info)

        return json.dumps(redact_secrets(log_payload))


# ---------------------------------------------------------------------------
# 4. Diagnostic Execution Timeline Tracker
# ---------------------------------------------------------------------------

class ExecutionTimeline:
    """Records observable lifecycle checkpoints for a request."""

    def __init__(self, trace_id: str, request_id: str) -> None:
        self.trace_id = trace_id
        self.request_id = request_id
        self.start_time = time.time()
        self.events: list[dict[str, Any]] = []
        self._lock = threading.Lock()

    def record_event(self, event_name: str, metadata: dict[str, Any] | None = None) -> None:
        with self._lock:
            elapsed_ms = (time.time() - self.start_time) * 1000
            entry = {
                "event": event_name,
                "elapsed_ms": round(elapsed_ms, 2),
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
            if metadata:
                entry["metadata"] = redact_secrets(metadata)
            self.events.append(entry)

    def get_summary(self) -> dict[str, Any]:
        with self._lock:
            total_duration_ms = (time.time() - self.start_time) * 1000
            return {
                "trace_id": self.trace_id,
                "request_id": self.request_id,
                "total_duration_ms": round(total_duration_ms, 2),
                "events_count": len(self.events),
                "events": list(self.events),
            }


_timelines: dict[str, ExecutionTimeline] = {}
_timeline_lock = threading.Lock()


def get_or_create_timeline(trace_id: str, request_id: str) -> ExecutionTimeline:
    with _timeline_lock:
        if request_id not in _timelines:
            _timelines[request_id] = ExecutionTimeline(trace_id, request_id)
            if len(_timelines) > 100:
                _timelines.pop(next(iter(_timelines)))
        return _timelines[request_id]
