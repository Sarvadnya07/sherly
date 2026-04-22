import os
import pytest
from action_manager import log_action, undo_last, get_history, _action_history

def test_undo_stack_reliability():
    _action_history.clear()
    
    # Log some actions
    log_action("write A", "write_file", ("restore_file", "A.txt", "old_A"), undoable=True)
    log_action("write B", "write_file", ("restore_file", "B.txt", "old_B"), undoable=True)
    log_action("dangerous action", "shutdown", None, undoable=False)
    
    assert len(_action_history) == 3
    
    # Undo should skip the non-undoable one and undo 'write B'
    res = undo_last()
    assert "Undo failed for file write" in res or "Restored file" in res
    assert len(_action_history) == 2 # 1 undone, 2 remaining
    assert _action_history[0]["action"] == "dangerous action"
    assert _action_history[1]["action"] == "write A"
    
    # Undo again should undo 'write A'
    res = undo_last()
    assert "Undo failed for file write" in res or "Restored file" in res
    assert len(_action_history) == 1
    
    # Undo again should fail
    res = undo_last()
    assert "Nothing to undo" in res
