"""
Tests for core/distributed_queue.py — Distributed Task Queue (FS-#18)
"""

from __future__ import annotations

import time

import pytest

from sherly.core.distributed_queue import (
    TaskResult,
    _MemoryQueue,
    get_task_queue,
    reset_task_queue,
)


# ---------------------------------------------------------------------------
# TaskResult
# ---------------------------------------------------------------------------

def test_task_result_initial_state() -> None:
    t = TaskResult("abc")
    assert t.task_id  == "abc"
    assert t.status   == "pending"
    assert t.result   is None
    assert t.error    == ""


def test_task_result_mark_done() -> None:
    t = TaskResult("xyz")
    t._mark_done(result=42)
    assert t.status == "done"
    assert t.result == 42
    assert t.error  == ""


def test_task_result_mark_failed() -> None:
    t = TaskResult("err")
    t._mark_done(error="something went wrong")
    assert t.status == "failed"
    assert t.error  == "something went wrong"


def test_task_result_wait_returns_true_after_done() -> None:
    t = TaskResult("wait_test")

    def _complete_later():
        time.sleep(0.05)
        t._mark_done(result="ok")

    import threading
    threading.Thread(target=_complete_later, daemon=True).start()
    assert t.wait(timeout=2.0)


def test_task_result_wait_timeout() -> None:
    t = TaskResult("timeout_test")
    # Never completed — should time out
    completed = t.wait(timeout=0.05)
    assert not completed


# ---------------------------------------------------------------------------
# _MemoryQueue — core operations
# ---------------------------------------------------------------------------

@pytest.fixture
def queue() -> _MemoryQueue:
    q = _MemoryQueue()
    yield q
    q.shutdown(wait=False)


def test_memory_queue_submit_returns_tracker(queue: _MemoryQueue) -> None:
    tracker = queue.submit(fn=lambda: "hello")
    assert isinstance(tracker, TaskResult)


def test_memory_queue_task_completes(queue: _MemoryQueue) -> None:
    tracker = queue.submit(fn=lambda: 99)
    tracker.wait(timeout=5.0)
    assert tracker.status == "done"
    assert tracker.result == 99


def test_memory_queue_task_with_args(queue: _MemoryQueue) -> None:
    tracker = queue.submit(fn=lambda x, y: x + y, args=(3, 4))
    tracker.wait(timeout=5.0)
    assert tracker.result == 7


def test_memory_queue_on_done_callback(queue: _MemoryQueue) -> None:
    collected = []
    tracker   = queue.submit(fn=lambda: "callback_result", on_done=collected.append)
    tracker.wait(timeout=5.0)
    assert collected == ["callback_result"]


def test_memory_queue_failed_task(queue: _MemoryQueue) -> None:
    def _fail():
        raise ValueError("intentional failure")

    tracker = queue.submit(fn=_fail)
    tracker.wait(timeout=5.0)
    assert tracker.status == "failed"
    assert "intentional failure" in tracker.error


def test_memory_queue_get_task_by_id(queue: _MemoryQueue) -> None:
    tracker = queue.submit(fn=lambda: True)
    found   = queue.get_task(tracker.task_id)
    assert found is tracker


def test_memory_queue_unknown_task_returns_none(queue: _MemoryQueue) -> None:
    assert queue.get_task("nonexistent-id") is None


def test_memory_queue_concurrent_tasks(queue: _MemoryQueue) -> None:
    def slow_task():
        time.sleep(0.01)
        return True

    trackers = [queue.submit(fn=slow_task) for _ in range(5)]
    for t in trackers:
        t.wait(timeout=10.0)
    statuses = [t.status for t in trackers]
    assert all(s == "done" for s in statuses)


# ---------------------------------------------------------------------------
# Factory
# ---------------------------------------------------------------------------

def test_get_task_queue_returns_memory_by_default() -> None:
    reset_task_queue()
    q = get_task_queue()
    assert isinstance(q, _MemoryQueue)
    reset_task_queue()


def test_get_task_queue_is_singleton() -> None:
    reset_task_queue()
    a = get_task_queue()
    b = get_task_queue()
    assert a is b
    reset_task_queue()


def test_reset_task_queue_creates_new_instance() -> None:
    reset_task_queue()
    a = get_task_queue()
    reset_task_queue()
    b = get_task_queue()
    assert a is not b
    reset_task_queue()
