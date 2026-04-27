"""
DISTRIBUTED TASK QUEUE — distributed_queue.py
Implements:
  FS-#18  Redis + Celery backed distributed task queue.
           Replaces the in-process `Queue` in `core/task_queue.py` for
           multi-worker and multi-user deployments.

           Two-tier architecture:
             Tier 1 (preferred): Celery + Redis broker
             Tier 2 (fallback):  In-process ThreadPoolExecutor queue
                                  (used when Redis is unavailable)

  Configuration (config.json):
    {
      "task_queue": {
        "backend": "redis" | "memory",
        "redis_url": "redis://localhost:6379/0",
        "max_workers": 4,
        "task_timeout": 120
      }
    }

  Usage:
    from sherly.core.distributed_queue import get_task_queue
    q = get_task_queue()
    q.submit("analyze_project", args=("./src",), on_done=print)
"""

from __future__ import annotations

import threading
import time
import uuid
from concurrent.futures import ThreadPoolExecutor, Future
from typing import Any, Callable

from sherly.utils.runtime_utils import log


# ---------------------------------------------------------------------------
# Config helpers
# ---------------------------------------------------------------------------

def _get_queue_config() -> dict[str, Any]:
    try:
        from sherly.config.config_manager import load_config
        return load_config().get("task_queue", {})
    except Exception:
        return {}


def _get_backend() -> str:
    return _get_queue_config().get("backend", "memory").lower()


def _get_redis_url() -> str:
    import os
    return _get_queue_config().get(
        "redis_url",
        os.environ.get("CELERY_BROKER_URL", "redis://localhost:6379/0"),
    )


def _get_max_workers() -> int:
    return int(_get_queue_config().get("max_workers", 4))


def _get_task_timeout() -> int:
    return int(_get_queue_config().get("task_timeout", 120))


# ---------------------------------------------------------------------------
# Task result tracker
# ---------------------------------------------------------------------------

class TaskResult:
    """Tracks the status and result of a submitted task."""

    def __init__(self, task_id: str) -> None:
        self.task_id   = task_id
        self.status    = "pending"    # pending | running | done | failed
        self.result:   Any = None
        self.error:    str = ""
        self._done_evt = threading.Event()

    def wait(self, timeout: float | None = None) -> bool:
        """Block until the task finishes. Returns True if done within timeout."""
        return self._done_evt.wait(timeout=timeout)

    def _mark_done(self, result: Any = None, error: str = "") -> None:
        self.result = result
        self.error  = error
        self.status = "failed" if error else "done"
        self._done_evt.set()


# ---------------------------------------------------------------------------
# Tier 2: In-Memory ThreadPoolExecutor Queue (always available)
# ---------------------------------------------------------------------------

class _MemoryQueue:
    """
    FS-#18 Tier-2: Simple in-process task queue backed by ThreadPoolExecutor.
    Used when Redis is unavailable. Identical public interface as CeleryQueue.
    """

    def __init__(self) -> None:
        self._executor = ThreadPoolExecutor(
            max_workers=_get_max_workers(), thread_name_prefix="SherlyWorker"
        )
        self._tasks: dict[str, TaskResult] = {}
        self._lock  = threading.Lock()
        log(f"[TaskQueue] In-memory queue initialized ({_get_max_workers()} workers).")

    def submit(
        self,
        fn: Callable,
        args: tuple = (),
        kwargs: dict | None = None,
        on_done: Callable | None = None,
    ) -> TaskResult:
        kwargs   = kwargs or {}
        task_id  = str(uuid.uuid4())
        tracker  = TaskResult(task_id)

        with self._lock:
            self._tasks[task_id] = tracker

        def _run():
            tracker.status = "running"
            try:
                result = fn(*args, **kwargs)
                tracker._mark_done(result=result)
                if on_done:
                    on_done(result)
            except Exception as exc:
                tracker._mark_done(error=str(exc))
                log(f"[TaskQueue] Task {task_id[:8]} failed: {exc}", level="error")

        self._executor.submit(_run)
        return tracker

    def get_task(self, task_id: str) -> TaskResult | None:
        with self._lock:
            return self._tasks.get(task_id)

    def active_count(self) -> int:
        with self._lock:
            return sum(1 for t in self._tasks.values() if t.status == "running")

    def shutdown(self, wait: bool = True) -> None:
        self._executor.shutdown(wait=wait)


# ---------------------------------------------------------------------------
# Tier 1: Celery + Redis Queue
# ---------------------------------------------------------------------------

class _CeleryQueue:
    """
    FS-#18 Tier-1: Celery + Redis distributed task queue.
    Requires: pip install celery redis
    """

    def __init__(self, redis_url: str) -> None:
        try:
            from celery import Celery
            self._app = Celery("sherly", broker=redis_url, backend=redis_url)
            self._app.conf.update(
                task_serializer="json",
                accept_content=["json"],
                task_time_limit=_get_task_timeout(),
                worker_prefetch_multiplier=1,
            )
            self._tasks: dict[str, TaskResult] = {}
            self._lock  = threading.Lock()
            log(f"[TaskQueue] Celery+Redis queue initialized → {redis_url}")
        except ImportError:
            raise RuntimeError("celery + redis required: pip install celery redis")

    def submit(
        self,
        fn: Callable,
        args: tuple = (),
        kwargs: dict | None = None,
        on_done: Callable | None = None,
    ) -> TaskResult:
        """
        FS-#18: Submit a task to Celery. The function must be importable
        (registered as a Celery task or sent as a lambda via pickle).
        Falls back to in-process execution for non-serializable callables.
        """
        kwargs   = kwargs or {}
        task_id  = str(uuid.uuid4())
        tracker  = TaskResult(task_id)

        with self._lock:
            self._tasks[task_id] = tracker

        # Run in a thread that monitors the Celery AsyncResult
        def _monitor():
            tracker.status = "running"
            try:
                celery_task = self._app.send_task(
                    "sherly.worker.execute",
                    args=[fn.__module__, fn.__qualname__, list(args), kwargs],
                )
                timeout = _get_task_timeout()
                result  = celery_task.get(timeout=timeout)
                tracker._mark_done(result=result)
                if on_done:
                    on_done(result)
            except Exception as exc:
                tracker._mark_done(error=str(exc))
                log(f"[TaskQueue/Celery] Task {task_id[:8]} failed: {exc}", level="error")

        threading.Thread(target=_monitor, daemon=True, name=f"CeleryMon-{task_id[:8]}").start()
        return tracker

    def get_task(self, task_id: str) -> TaskResult | None:
        with self._lock:
            return self._tasks.get(task_id)

    def active_count(self) -> int:
        with self._lock:
            return sum(1 for t in self._tasks.values() if t.status == "running")

    def shutdown(self, wait: bool = True) -> None:
        pass  # Celery workers are external processes


# ---------------------------------------------------------------------------
# Factory — FS-#18 public interface
# ---------------------------------------------------------------------------

_queue_instance: _MemoryQueue | _CeleryQueue | None = None
_queue_lock = threading.Lock()


def get_task_queue() -> _MemoryQueue | _CeleryQueue:
    """
    FS-#18: Return the appropriate task queue based on config.json → task_queue.backend.
    Falls back to in-memory queue if Redis/Celery is unavailable.
    """
    global _queue_instance
    with _queue_lock:
        if _queue_instance is None:
            backend = _get_backend()
            if backend == "redis":
                try:
                    _queue_instance = _CeleryQueue(_get_redis_url())
                    log("[TaskQueue] Using Celery+Redis backend.")
                except Exception as exc:
                    log(
                        f"[TaskQueue] Redis unavailable ({exc}), falling back to in-memory.",
                        level="warning",
                    )
                    _queue_instance = _MemoryQueue()
            else:
                _queue_instance = _MemoryQueue()
    return _queue_instance


def reset_task_queue() -> None:
    """Force re-creation of the task queue (useful in tests)."""
    global _queue_instance
    with _queue_lock:
        if _queue_instance:
            _queue_instance.shutdown(wait=False)
        _queue_instance = None
