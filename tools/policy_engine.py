"""
POLICY ENGINE & STRUCTURED TOOL EXECUTION — tools/policy_engine.py
Enforces argument-level security, risk classification, approval gates,
and structured tool dispatch.
"""

from __future__ import annotations

import json
import re
import logging
from typing import Any, Optional

from tools.capabilities import ToolSpec, ToolResult, ToolRisk, registry
from safety_guard import classify_command, RiskLevel
from action_manager import request_approval, classify_action

logger = logging.getLogger("sherly.policy")


def parse_tool_call(text: str) -> Optional[dict[str, Any]]:
    """
    Parse a structured tool call from LLM output.
    Supports strict JSON blocks: ```json { "type": "tool_call", "tool": "...", "arguments": {...} } ```
    or raw JSON objects.
    """
    if not text or not text.strip():
        return None

    # Check for fenced code block containing JSON
    json_match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
    candidate = json_match.group(1) if json_match else text.strip()

    try:
        data = json.loads(candidate)
        if isinstance(data, dict) and "tool" in data:
            return {
                "tool": str(data.get("tool", "")).strip().lower(),
                "arguments": data.get("arguments", {}) if isinstance(data.get("arguments"), dict) else {},
            }
    except Exception:
        pass

    return None


def evaluate_tool_policy(tool_name: str, arguments: dict[str, Any]) -> ToolRisk:
    """
    Evaluate policy for a tool invocation based on tool metadata and actual arguments.
    """
    tool: Optional[ToolSpec] = registry.get(tool_name)
    if not tool:
        return ToolRisk.BLOCKED

    # Argument-aware checks for terminal execution
    if tool_name == "terminal.execute":
        cmd = arguments.get("command", "")
        # Inspect raw command
        risk = classify_command(cmd)
        if risk == RiskLevel.DANGEROUS:
            return ToolRisk.DANGEROUS
        elif risk == RiskLevel.CONFIRM:
            return ToolRisk.CONFIRM
        return ToolRisk.SAFE

    # Argument-aware checks for filesystem deletion / modification
    if tool_name.startswith("filesystem."):
        path = str(arguments.get("path", ""))
        if any(sensitive in path.lower() for sensitive in (".env", "id_rsa", "credentials", "secrets")):
            return ToolRisk.BLOCKED

    return tool.risk


def execute_capability(
    tool_name: str,
    arguments: dict[str, Any],
    user_approved: bool = False,
) -> ToolResult:
    """
    Execute a tool call through the canonical policy and safety pipeline.
    """
    tool = registry.get(tool_name)
    if not tool:
        return ToolResult(
            success=False,
            tool=tool_name,
            output="",
            error={"code": "UNKNOWN_TOOL", "message": f"Tool '{tool_name}' is not recognized."},
        )

    policy_risk = evaluate_tool_policy(tool_name, arguments)

    if policy_risk == ToolRisk.BLOCKED:
        return ToolResult(
            success=False,
            tool=tool_name,
            output="",
            error={"code": "POLICY_BLOCKED", "message": "Execution blocked by security policy."},
        )

    if policy_risk in (ToolRisk.CONFIRM, ToolRisk.DANGEROUS) and not user_approved:
        # Enqueue in action_manager for confirmation
        cmd_repr = f"{tool_name}({json.dumps(arguments)})"
        prompt = request_approval(cmd_repr)
        return ToolResult(
            success=False,
            tool=tool_name,
            output=prompt,
            error={"code": "APPROVAL_REQUIRED", "message": "Action requires confirmation."},
            metadata={"approval_required": True, "prompt": prompt},
        )

    # Safe or approved: dispatch to registry executor
    return registry.execute(tool_name, arguments)
