"""
AGENT TOOL LOOP — tools/agent_tool_loop.py
Implements the closed-loop LLM tool-calling agent:
Prompt -> Model -> Tool Call -> Policy & Execution -> Observation -> Final Model Synthesis.
"""

from __future__ import annotations

import json
import logging
import sys
from collections.abc import Callable
from pathlib import Path

_ROOT = str(Path(__file__).resolve().parent.parent)
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from tools.capabilities import ToolRisk, registry
from tools.policy_engine import evaluate_tool_policy, execute_capability, parse_tool_call

logger = logging.getLogger("sherly.agent_tool_loop")


def build_tool_system_prompt() -> str:
    """
    Format available registered tools as a schema specification for the LLM.
    """
    tools = registry.list_tools(enabled_only=True)
    tool_descriptions = []
    for t in tools:
        schema_json = json.dumps(t.parameters_schema) if t.parameters_schema else "{}"
        tool_descriptions.append(
            f"- `{t.name}`: {t.description}\n  Parameters: {schema_json}"
        )

    tools_block = "\n".join(tool_descriptions)

    return (
        "You are Sherly, an intelligent AI developer copilot with system tool capabilities.\n\n"
        "AVAILABLE TOOLS:\n"
        f"{tools_block}\n\n"
        "TOOL CALLING RULES:\n"
        "1. If the user asks you to execute an action (run a command, read or inspect a file, scan a folder, search the web, open a browser), you MUST output ONLY a JSON tool_call block.\n"
        "2. Paths for filesystem tools MUST be relative to the workspace root (e.g. 'main.py', 'pyproject.toml', 'backend/main.py').\n"
        "3. Do NOT write conversational explanations before or after the JSON block.\n"
        "4. JSON Format:\n"
        "```json\n"
        "{\n"
        '  "type": "tool_call",\n'
        '  "tool": "<tool_name>",\n'
        '  "arguments": { ... }\n'
        "}\n"
        "```\n"
        "5. If the user asks a pure general greeting or conceptual question, answer directly in markdown.\n"
    )


def run_tool_agent_loop(
    user_prompt: str,
    ask_model_fn: Callable[[str], str],
    max_turns: int = 2,
) -> str:
    """
    Execute an agentic interaction turn:
    1. Send prompt with tool definitions.
    2. Check for tool call in model response.
    3. Execute tool if requested and safe.
    4. Feed tool result back to model for final answer synthesis.
    """
    system_tools_spec = build_tool_system_prompt()
    augmented_prompt = f"{system_tools_spec}\nUser Request: {user_prompt}"

    model_response = ask_model_fn(augmented_prompt)
    tool_call = parse_tool_call(model_response)

    if not tool_call:
        # Model chose to respond directly without tool invocation
        return model_response

    tool_name = tool_call.get("tool", "")
    arguments = tool_call.get("arguments", {})

    logger.info(f"[AgentToolLoop] Model requested tool: {tool_name} with arguments {arguments}")

    # Evaluate policy & execute
    policy_risk = evaluate_tool_policy(tool_name, arguments)

    if policy_risk == ToolRisk.BLOCKED:
        return "⛔ Blocked: That operation is restricted by Sherly security policy."

    if policy_risk in (ToolRisk.CONFIRM, ToolRisk.DANGEROUS):
        tool_result = execute_capability(tool_name, arguments, user_approved=False)
        return tool_result.output or "Action requires confirmation before execution."

    # Execute safe tool
    tool_result = execute_capability(tool_name, arguments, user_approved=True)

    if not tool_result.success:
        err_msg = tool_result.error.get("message", "Tool execution failed") if tool_result.error else "Failed"
        return f"Error running capability `{tool_name}`: {err_msg}"

    # Return observation back to LLM for final synthesis
    synthesis_prompt = (
        f"You previously requested the tool `{tool_name}` with arguments `{json.dumps(arguments)}`.\n"
        f"Observation / Tool Output:\n"
        f"```\n{tool_result.output}\n```\n\n"
        f"Now provide a direct, concise, and clear answer to the user's original request:\n"
        f"\"{user_prompt}\""
    )

    final_response = ask_model_fn(synthesis_prompt)
    return final_response
