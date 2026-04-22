import pytest
import time
from sherly.utils.runtime_utils import safe_execute, timeout_call, add_task, task_queue, _MAX_QUEUE_SIZE

def test_safe_execute():
    def success():
        return "success"
        
    def fail():
        raise ValueError("test error")
        
    assert safe_execute(success) == "success"
    assert safe_execute(fail, fallback="custom fallback") == "custom fallback"

def test_timeout_call():
    def quick():
        return "quick"
        
    def slow():
        time.sleep(1)
        return "slow"
        
    assert timeout_call(quick, timeout=0.5) == "quick"
    assert timeout_call(slow, timeout=0.1, fallback="timeout fallback") == "timeout fallback"

def test_add_task_overflow():
    # Empty queue first
    while not task_queue.empty():
        task_queue.get()
        task_queue.task_done()
        
    def dummy():
        pass
        
    for _ in range(_MAX_QUEUE_SIZE):
        assert add_task(dummy) is None
        
    assert "System busy" in add_task(dummy)
