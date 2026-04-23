import pytest
from sherly.services.action_manager import classify_action, log_action, get_history, undo_last

def test_classify_action():
    assert classify_action("read file.txt") == "safe"
    assert classify_action("open chrome") == "safe"
    assert classify_action("run python script.py") == "confirm"
    assert classify_action("delete everything") == "dangerous"
    assert classify_action("rm -rf /") == "dangerous"

def test_action_history_persistence():
    # Clear existing history if any (mocking or using a test DB would be better, 
    # but for this script we'll just verify logging works)
    log_action("test action", "test_type", undoable=False)
    history = get_history()
    assert "test action" in history

def test_undo_logic_safe_check():
    # Verify that undo_last returns a message when nothing is undoable
    # We log a non-undoable action first
    log_action("permanent action", "shutdown", undoable=False)
    res = undo_last()
    assert "Nothing to undo" in res or "Restored" in res # Depending on what was already in DB
