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
from collections.abc import Callable
from queue import Empty, Queue
from typing import Any

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
            except Exception as log_exc:
                try:
                    from runtime_utils import log

                    log(f"[TaskQueue] error logging failure: {log_exc}", level="warning")
                except Exception:
                    # best-effort fallback if logging is not available
                    print(f"[TaskQueue] logging failure: {log_exc}")
            if on_error:
                on_error(exc)
        finally:
            _queue.task_done()


threading.Thread(target=_worker, daemon=True, name="SherlyTaskQueue").start()


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

_MAX_QUEUE_SIZE = 50


def add_task(
    func: Callable,
    *args,
    on_done: Callable[[Any], None] | None = None,
    on_error: Callable[[Exception], None] | None = None,
    **kwargs,
) -> str | None:
    """
    Enqueue *func* to run on the background worker thread.

    Parameters
    ----------
    func     : callable to execute
    *args    : positional arguments for func
    on_done  : optional callback(result) called after successful execution
    on_error : optional callback(exc) called on exception
    **kwargs : keyword arguments for func

    Returns
    -------
    str | None : Warning string if queue is full/overloaded, None otherwise.
    """
    if _queue.qsize() >= _MAX_QUEUE_SIZE:
        return f"⚠️ Task queue full ({_queue.qsize()} items). Task rejected to prevent memory overload."

    _queue.put((func, args, kwargs, on_done, on_error))
    return None
