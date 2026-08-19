"""
TOOL SYSTEM TESTS — tests/test_tool_system.py
Verifies ToolSpec, ToolRegistry, built-in tools, policy engine,
and argument-aware security.
"""

from __future__ import annotations

import pytest
from tools.capabilities import ToolSpec, ToolRisk, ToolRegistry
from tools.policy_engine import parse_tool_call, evaluate_tool_policy, execute_capability
import tools.builtins  # ensure builtins are registered


def test_tool_registry_registration():
    reg = ToolRegistry()
    spec = ToolSpec(
        name="test.echo",
        description="Echo input text",
        parameters_schema={"msg": "str"},
        handler=lambda msg: f"Echo: {msg}",
        risk=ToolRisk.SAFE,
    )
    reg.register(spec)
    assert reg.has("test.echo")
    assert reg.get("test.echo") is not None

    res = reg.execute("test.echo", {"msg": "hello world"})
    assert res.success is True
    assert res.output == "Echo: hello world"

    reg.unregister("test.echo")
    assert not reg.has("test.echo")


def test_tool_registry_unknown_tool():
    reg = ToolRegistry()
    res = reg.execute("non_existent_tool", {})
    assert res.success is False
    assert res.error["code"] == "TOOL_NOT_FOUND"


def test_tool_registry_disabled_tool():
    reg = ToolRegistry()
    spec = ToolSpec(
        name="test.disabled",
        description="Disabled tool",
        handler=lambda: "ok",
        enabled=False,
    )
    reg.register(spec)
    res = reg.execute("test.disabled", {})
    assert res.success is False
    assert res.error["code"] == "TOOL_DISABLED"


def test_parse_tool_call_json():
    raw_json = '{"tool": "filesystem.read", "arguments": {"path": "main.py"}}'
    parsed = parse_tool_call(raw_json)
    assert parsed is not None
    assert parsed["tool"] == "filesystem.read"
    assert parsed["arguments"]["path"] == "main.py"

    fenced_json = '```json\n{"tool": "web.search", "arguments": {"query": "python news"}}\n```'
    parsed2 = parse_tool_call(fenced_json)
    assert parsed2 is not None
    assert parsed2["tool"] == "web.search"
    assert parsed2["arguments"]["query"] == "python news"

    assert parse_tool_call("Just normal conversation text") is None


def test_policy_engine_argument_security():
    # Sensitive file blocked
    risk = evaluate_tool_policy("filesystem.read", {"path": ".env"})
    assert risk == ToolRisk.BLOCKED

    # Safe file read
    risk_safe = evaluate_tool_policy("filesystem.read", {"path": "README.md"})
    assert risk_safe == ToolRisk.SAFE

    # Dangerous terminal command
    risk_dang = evaluate_tool_policy("terminal.execute", {"command": "format C:"})
    assert risk_dang == ToolRisk.DANGEROUS

    # Confirm terminal command
    risk_conf = evaluate_tool_policy("terminal.execute", {"command": "git reset --hard"})
    assert risk_conf == ToolRisk.CONFIRM


def test_execute_capability_safe_execution():
    res = execute_capability("filesystem.scan", {"path": "."})
    assert res.success is True
    assert "Directory structure" in res.output or "files" in res.output or len(res.output) > 0


def test_execute_capability_blocked_execution():
    res = execute_capability("filesystem.read", {"path": "secret/.env"})
    assert res.success is False
    assert res.error["code"] == "POLICY_BLOCKED"
