import pytest
from sherly.services.action_manager import classify_action

def test_classify_action_dangerous():
    assert classify_action("delete the folder") == "dangerous"
    assert classify_action("rm -rf /") == "dangerous"
    assert classify_action("format C:") == "dangerous"

def test_classify_action_confirm():
    assert classify_action("run script.py") == "confirm"
    assert classify_action("pip install requests") == "confirm"
    assert classify_action("git commit -m 'test'") == "confirm"
    assert classify_action("something completely unknown") == "confirm"

def test_classify_action_safe():
    assert classify_action("show me the files") == "safe"
    assert classify_action("what is my name") == "safe"
    assert classify_action("status check") == "safe"
