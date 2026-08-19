"""
INTEGRATION TESTS — tests/test_agent_tool_loop.py
Verifies end-to-end LLM tool calling loop, observation feedback,
and policy enforcement.
"""

from __future__ import annotations

import pytest
from tools.agent_tool_loop import build_tool_system_prompt, run_tool_agent_loop


def test_build_tool_system_prompt():
    prompt = build_tool_system_prompt()
    assert "filesystem.read" in prompt
    assert "terminal.execute" in prompt
    assert "web.search" in prompt
    assert "tool_call" in prompt


def test_agent_tool_loop_direct_answer():
    def mock_direct_model(prompt: str) -> str:
        return "Hello! I am Sherly, your AI assistant."

    res = run_tool_agent_loop("Hi there", mock_direct_model)
    assert res == "Hello! I am Sherly, your AI assistant."


def test_agent_tool_loop_with_tool_call():
    turn = 0

    def mock_tool_model(prompt: str) -> str:
        nonlocal turn
        turn += 1
        if turn == 1:
            # First turn: model requests a tool
            return '```json\n{"type": "tool_call", "tool": "filesystem.scan", "arguments": {"path": "."}}\n```'
        else:
            # Second turn: model receives observation and synthesizes final answer
            assert "Observation / Tool Output" in prompt
            return "Based on the workspace scan, this is a Python project containing backend, frontend, and tools."

    res = run_tool_agent_loop("What is this project about?", mock_tool_model)
    assert "Python project" in res


def test_agent_tool_loop_blocked_policy():
    def mock_malicious_model(prompt: str) -> str:
        return '```json\n{"type": "tool_call", "tool": "filesystem.read", "arguments": {"path": ".env"}}\n```'

    res = run_tool_agent_loop("Read my secrets", mock_malicious_model)
    assert "⛔ Blocked" in res or "restricted" in res


def test_agent_tool_loop_confirmation_required():
    def mock_terminal_model(prompt: str) -> str:
        return '```json\n{"type": "tool_call", "tool": "terminal.execute", "arguments": {"command": "git reset --hard"}}\n```'

    res = run_tool_agent_loop("Reset repository", mock_terminal_model)
    assert "Approve" in res or "requires confirmation" in res or "approve" in res.lower()
