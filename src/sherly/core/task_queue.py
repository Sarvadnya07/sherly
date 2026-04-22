"""
Pillar 6 – RUNTIME LAYER: Task Queue
======================================
Thread-safe background work queue with:
  - named daemon worker thread
  - per-task error isolation (one failure doesn't kill the queue)
  - optional on_done / on_error callbacks
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
