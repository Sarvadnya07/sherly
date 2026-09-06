"""
CANONICAL TOOL REGISTRY — tool_registry.py
Re-exports the canonical ToolRegistry, ToolSpec, ToolResult, and provides backward-compatible adapters.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from tools.capabilities import ToolRisk, ToolSpec, registry


def register_tool(name: str, function: Callable) -> None:
    """Backward-compatible tool registration adapter."""
    spec = ToolSpec(
        name=name,
        description=f"Plugin tool: {name}",
        parameters_schema={"text": "str"},
        handler=function,
        risk=ToolRisk.SAFE,
        enabled=True,
    )
    registry.register(spec)


def run_tool(text: str, payload: Any = None) -> str | None:
    """Backward-compatible substring tool dispatch."""
    normalized = text.lower()
    for tool in registry.list_tools():
        if tool.name.lower() in normalized:
            res = registry.execute(tool.name, {"query": payload if payload is not None else text})
            if res.success:
                return res.output
            return res.error.get("message") if res.error else "Tool execution failed."
    return None


def clear_tools() -> None:
    """Backward-compatible clear tools adapter."""
    registry.clear()
