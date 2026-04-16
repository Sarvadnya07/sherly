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

_queue: Queue = Queue()
queue = _queue   # backward-compat alias


# ---------------------------------------------------------------------------
# Worker
# ---------------------------------------------------------------------------

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
                from runtime_utils import log
                log(f"[TaskQueue] error in {getattr(func, '__name__', func)}: {exc}", level="error")
            except Exception:
                pass
            if on_error:
                on_error(exc)
        finally:
            _queue.task_done()


threading.Thread(target=_worker, daemon=True, name="SherlyTaskQueue").start()


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def add_task(
    func: Callable,
    *args,
    on_done: Callable[[Any], None] | None = None,
    on_error: Callable[[Exception], None] | None = None,
    **kwargs,
) -> None:
    """
    Enqueue *func* to run on the background worker thread.

    Parameters
    ----------
    func     : callable to execute
    *args    : positional arguments for func
    on_done  : optional callback(result) called after successful execution
    on_error : optional callback(exc) called on exception
    **kwargs : keyword arguments for func
    """
    _queue.put((func, args, kwargs, on_done, on_error))
