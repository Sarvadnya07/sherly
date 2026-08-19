"""
CAPABILITIES & TOOL SPECIFICATION — tools/capabilities.py
Defines the canonical ToolSpec, ToolResult, ToolRisk, and structured execution pipeline.
"""

from __future__ import annotations

import time
import logging
from enum import Enum
from typing import Any, Callable, Optional
from pydantic import BaseModel, Field, ConfigDict

logger = logging.getLogger("sherly.capabilities")


class ToolRisk(str, Enum):
    SAFE = "safe"
    CONFIRM = "confirm"
    DANGEROUS = "dangerous"
    BLOCKED = "blocked"


class ToolSpec(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    name: str
    description: str
    parameters_schema: dict[str, Any] = Field(default_factory=dict)
    handler: Any = None  # Callable
    risk: ToolRisk = ToolRisk.SAFE
    permissions: list[str] = Field(default_factory=list)
    requires_approval: bool = False
    reversible: bool = False
    timeout: float = 30.0
    enabled: bool = True


class ToolResult(BaseModel):
    success: bool
    tool: str
    output: str
    error: Optional[dict[str, Any]] = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class ToolRegistry:
    def __init__(self) -> None:
        self._tools: dict[str, ToolSpec] = {}

    def register(self, tool: ToolSpec) -> None:
        if not tool.name or not tool.name.strip():
            raise ValueError("Tool name must not be empty.")
        key = tool.name.strip().lower()
        self._tools[key] = tool
        logger.info(f"Registered tool capability: {tool.name}")

    def get(self, name: str) -> Optional[ToolSpec]:
        return self._tools.get(name.strip().lower())

    def has(self, name: str) -> bool:
        return name.strip().lower() in self._tools

    def list_tools(self, enabled_only: bool = True) -> list[ToolSpec]:
        if enabled_only:
            return [t for t in self._tools.values() if t.enabled]
        return list(self._tools.values())

    def unregister(self, name: str) -> None:
        key = name.strip().lower()
        if key in self._tools:
            del self._tools[key]

    def clear(self) -> None:
        self._tools.clear()

    def execute(self, name: str, arguments: dict[str, Any]) -> ToolResult:
        tool = self.get(name)
        if not tool:
            return ToolResult(
                success=False,
                tool=name,
                output="",
                error={"code": "TOOL_NOT_FOUND", "message": f"Tool '{name}' is not registered."},
            )

        if not tool.enabled:
            return ToolResult(
                success=False,
                tool=name,
                output="",
                error={"code": "TOOL_DISABLED", "message": f"Tool '{name}' is disabled."},
            )

        start_time = time.time()
        try:
            handler = tool.handler
            if not callable(handler):
                return ToolResult(
                    success=False,
                    tool=name,
                    output="",
                    error={"code": "INVALID_HANDLER", "message": f"Tool '{name}' handler is not callable."},
                )

            # Invoke handler with kwargs or positional
            if isinstance(arguments, dict):
                res = handler(**arguments)
            else:
                res = handler(arguments)

            duration_ms = int((time.time() - start_time) * 1000)
            return ToolResult(
                success=True,
                tool=name,
                output=str(res) if res is not None else "",
                metadata={"duration_ms": duration_ms},
            )
        except Exception as exc:
            duration_ms = int((time.time() - start_time) * 1000)
            logger.error(f"Execution error in tool '{name}': {exc}")
            return ToolResult(
                success=False,
                tool=name,
                output="",
                error={"code": "EXECUTION_ERROR", "message": str(exc)},
                metadata={"duration_ms": duration_ms},
            )


# Global canonical registry instance
registry = ToolRegistry()
