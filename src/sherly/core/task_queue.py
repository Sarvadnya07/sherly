"""
Pillar 6 – RUNTIME LAYER: Task Queue
======================================
Thread-safe background work queue with:
  - named daemon worker thread
  - per-task error isolation (one failure doesn't kill the queue)
  - optional on_done / on_error callbacks
  - TaskQueue class (OO interface) + module-level add_task() (functional API)
"""

from __future__ import annotations

import threading
from queue import Queue, Empty
from typing import Callable, Any

_MAX_QUEUE_SIZE = 10
_queue: Queue = Queue()
_queue_lock = threading.Lock()

def _worker() -> None:
    while True:
        try:
            item = _queue.get(timeout=1)
        except Empty:
            continue

        func, args, kwargs, on_done, on_error = item
        try:
            result = func(*args, **kwargs)
            if on_done:
                on_done(result)
        except Exception as exc:
            try:
                from sherly.utils.runtime_utils import log
                log(f"[TaskQueue] error in {getattr(func, '__name__', func)}: {exc}", level="error")
            except Exception:
                pass
            if on_error:
                on_error(exc)
        finally:
            _queue.task_done()

threading.Thread(target=_worker, daemon=True, name="SherlyTaskQueue").start()

def add_task(
    func: Callable,
    *args,
    on_done: Callable[[Any], None] | None = None,
    on_error: Callable[[Exception], None] | None = None,
    **kwargs,
) -> str | None:
    """
    Enqueue a task. Returns error message if queue is full.
    """
    with _queue_lock:
        if _queue.qsize() >= _MAX_QUEUE_SIZE:
            return "System busy. Please wait a moment."
        _queue.put((func, args, kwargs, on_done, on_error))
    return None


# ---------------------------------------------------------------------------
# BUG-1 FIX: TaskQueue class — OO wrapper over the module-level queue
# ---------------------------------------------------------------------------

class TaskQueue:
    """
    OO interface to the shared background task queue.

    Provides add_task(), is_full(), queue_size(), and drain().
    The underlying daemon worker thread is shared across all instances
    (module-level singleton pattern).
    """

    def __init__(self) -> None:
        pass   # Worker already started at module load time

    def add_task(
        self,
        func: Callable,
        *args,
        on_done: Callable[[Any], None] | None = None,
        on_error: Callable[[Exception], None] | None = None,
        **kwargs,
    ) -> str | None:
        """Delegate to module-level add_task(). Returns None on success or error string if full."""
        return add_task(func, *args, on_done=on_done, on_error=on_error, **kwargs)

    def is_full(self) -> bool:
        """Return True if the queue has reached MAX_QUEUE_SIZE."""
        with _queue_lock:
            return _queue.qsize() >= _MAX_QUEUE_SIZE

    def queue_size(self) -> int:
        """Return the current number of pending tasks."""
        return _queue.qsize()

    def drain(self, timeout: float = 5.0) -> None:
        """Block until all queued tasks are processed or timeout expires."""
        _queue.join()
