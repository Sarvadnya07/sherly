"""
BUILT-IN TOOLS REGISTRATION — tools/builtins.py
Registers the default capability surface into the canonical ToolRegistry.
"""

from __future__ import annotations

import os
from pathlib import Path
import webbrowser
from typing import Optional
from tools.capabilities import ToolSpec, ToolRisk, registry
from tools.terminal_tools import safe_exec
from tools.file_tools import read_file
from tools.screen_tools import analyze_screen
from web_search import search_web


def _read_file_handler(path: str) -> str:
    cleaned = path.replace("/path/to/current/directory/", "").replace("/path/to/project/", "").replace("/path/to/", "").strip()
    content = read_file(path) or read_file(cleaned) or read_file(Path(cleaned).name)
    if content is None:
        return f"File not found: {path}"
    return content


def _scan_project_handler(path: Optional[str] = None) -> str:
    target_dir = Path(path or ".").resolve()
    if not target_dir.exists() or not target_dir.is_dir():
        return f"Directory not found: {target_dir}"
    
    entries = []
    for root, dirs, files in os.walk(target_dir):
        dirs[:] = [d for d in dirs if not d.startswith(".") and d not in ("node_modules", "venv", "__pycache__", "dist")]
        rel = Path(root).relative_to(target_dir)
        indent = "  " * len(rel.parts)
        entries.append(f"{indent}📁 {Path(root).name}/")
        for f in files[:20]:
            entries.append(f"{indent}  📄 {f}")
        if len(files) > 20:
            entries.append(f"{indent}  ... and {len(files) - 20} more files")
        if len(entries) > 100:
            entries.append("... [tree truncated]")
            break
    return "\n".join(entries)


def _terminal_execute_handler(command: str) -> str:
    return safe_exec(command)


def _web_search_handler(query: str, max_results: int = 5) -> str:
    results = search_web(query, max_results=max_results)
    if not results:
        return f"No search results found for '{query}'."
    formatted = []
    for r in results:
        formatted.append(f"• {r.get('title', 'Untitled')}: {r.get('body', '')}\n  URL: {r.get('href', '')}")
    return "\n\n".join(formatted)


def _browser_open_handler(url: str) -> str:
    webbrowser.open(url)
    return f"Opened {url} in browser."


def _screen_capture_handler() -> str:
    return analyze_screen()


def register_builtin_tools() -> None:
    """Register core capability tools."""
    # 1. Filesystem tools
    registry.register(
        ToolSpec(
            name="filesystem.read",
            description="Read and inspect source code or text files within the project workspace.",
            parameters_schema={"type": "object", "properties": {"path": {"type": "string"}}, "required": ["path"]},
            handler=_read_file_handler,
            risk=ToolRisk.SAFE,
            permissions=["filesystem.read"],
            requires_approval=False,
            reversible=False,
        )
    )

    registry.register(
        ToolSpec(
            name="filesystem.scan",
            description="Scan workspace project directory structure and files.",
            parameters_schema={"type": "object", "properties": {"path": {"type": "string"}}},
            handler=_scan_project_handler,
            risk=ToolRisk.SAFE,
            permissions=["filesystem.read"],
            requires_approval=False,
            reversible=False,
        )
    )

    # 2. Terminal execution
    registry.register(
        ToolSpec(
            name="terminal.execute",
            description="Execute allowed developer CLI commands (git, npm, python, pytest, etc.).",
            parameters_schema={"type": "object", "properties": {"command": {"type": "string"}}, "required": ["command"]},
            handler=_terminal_execute_handler,
            risk=ToolRisk.CONFIRM,
            permissions=["terminal.execute"],
            requires_approval=True,
            reversible=False,
        )
    )

    # 3. Web search
    registry.register(
        ToolSpec(
            name="web.search",
            description="Perform a real-time web search for current documentation, news, or technical questions.",
            parameters_schema={"type": "object", "properties": {"query": {"type": "string"}}, "required": ["query"]},
            handler=_web_search_handler,
            risk=ToolRisk.SAFE,
            permissions=["network.search"],
            requires_approval=False,
            reversible=False,
        )
    )

    # 4. Browser navigation
    registry.register(
        ToolSpec(
            name="browser.open",
            description="Open a specified web URL in the user's default browser.",
            parameters_schema={"type": "object", "properties": {"url": {"type": "string"}}, "required": ["url"]},
            handler=_browser_open_handler,
            risk=ToolRisk.SAFE,
            permissions=["browser.open"],
            requires_approval=False,
            reversible=False,
        )
    )

    # 5. Screen analysis
    registry.register(
        ToolSpec(
            name="screen.capture",
            description="Capture current active screen for visual debugging or analysis.",
            parameters_schema={"type": "object", "properties": {}},
            handler=_screen_capture_handler,
            risk=ToolRisk.SAFE,
            permissions=["screen.capture"],
            requires_approval=False,
            reversible=False,
        )
    )


# Auto-register builtins on module import
register_builtin_tools()
