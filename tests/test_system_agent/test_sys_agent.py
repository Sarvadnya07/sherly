import pytest
import sys
from unittest.mock import MagicMock

sys.modules['pyautogui'] = MagicMock()

from agents import system_agent

def test_system_agent_imports_safe_exec():
    # If the system agent correctly uses safe_exec instead of run_command, we'll verify it
    assert "safe_exec" in system_agent.__dict__ or "safe_exec" in dir(system_agent)
