import os
import subprocess
import webbrowser

import pyperclip

from agent_manager import run_agent
from config_manager import set_current_model
from model_manager import ask_model
from plugin_manager import get_enabled_plugin_names, run_plugin
from runtime_utils import safe_execute
from text_to_speech import speak
from tool_registry import clear_tools, register_tool, run_tool
from tools.dictation import start_dictation
from tools.error_tools import analyze_error
from tools.file_tools import explain_file
from tools.project_tools import scan_project
from tools.screen_tools import analyze_screen
from tools.automation_tools import open_app, type_text
from tools.terminal_tools import run_command
from tools.task_engine import execute_task
from web_search import search_web
from memory_brain import recall, remember


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _llm(prompt: str) -> str:
    """Direct LLM call for already-composed prompts."""
    return safe_execute(
        lambda: ask_model(prompt),
        "I hit an internal error while generating a response.",
    )


def _explain_clipboard() -> str:
    code = pyperclip.paste()
    if not code:
        return "Nothing found on clipboard."
    return ask_model(f"Explain this code clearly:\n\n{code[:3000]}")


def _needs_web_search(text: str) -> bool:
    keywords = ["latest", "news", "today", "current", "recent",
                "price", "weather", "score", "who won", "live"]
    return any(w in text for w in keywords)


def _run_system_command(text: str):
    """Fast keyword-based system actions. Returns a string or None."""
    if "chrome" in text:
        try:
            subprocess.Popen(r"C:\Program Files\Google\Chrome\Application\chrome.exe")
            return "Opening Chrome"
        except FileNotFoundError:
            return "Chrome not found at default path."
    if "lock computer" in text or "lock screen" in text:
        os.system("rundll32.exe user32.dll,LockWorkStation")
        return "Locking your computer"
    return None


def _extract_after(raw: str, keyword: str) -> str:
    """Return everything after *keyword* (case-insensitive) in *raw*."""
    idx = raw.lower().find(keyword)
    if idx == -1:
        return ""
    return raw[idx + len(keyword):].strip(" \"'")


def _refresh_plugin_tools():
    clear_tools()
    for name in get_enabled_plugin_names():
        register_tool(name, lambda q, n=name: run_plugin(n, q))


# ---------------------------------------------------------------------------
# Main router
# ---------------------------------------------------------------------------

def route_command(text: str) -> str:
    raw = text.strip()
    low = raw.lower().replace(",", "").replace(".", "").replace("?", "").replace("sherly", "").strip()

    # --- Model switching ---
    if "use openai" in low or "switch to openai" in low:
        return set_current_model("openai")
    if "use gemini" in low or "switch to gemini" in low:
        return set_current_model("gemini")
    if "use groq" in low or "switch to groq" in low:
        return set_current_model("groq")
    if "use local" in low or "switch to local" in low:
        return set_current_model("local")

    # --- Dictation ---
    if "start dictation" in low:
        return safe_execute(
            lambda: "Dictation captured." if start_dictation() else "No speech captured.",
            "Failed to start dictation.",
        )

    # --- Terminal commands ---
    if "run command" in low or "execute" in low:
        cmd = _extract_after(raw, "run command") or _extract_after(raw, "execute")
        if not cmd:
            return "Please specify the command to run."
        return safe_execute(lambda: run_command(cmd), "Failed to run the command.")

    # --- Code / error tools ---
    if "explain error" in low or "analyze error" in low:
        return safe_execute(lambda: analyze_error(ask_model), "Failed to analyze the error.")

    if "explain this code" in low or "explain code" in low:
        return safe_execute(_explain_clipboard, "Failed to explain clipboard content.")

    # --- File tools ---
    if "open file" in low or "read file" in low:
        path = _extract_after(raw, "open file") or _extract_after(raw, "read file")
        if not path:
            return "Please specify a file path."
        return safe_execute(lambda: explain_file(path, ask_model), "Failed to open that file.")

    if "scan project" in low or "analyze project" in low:
        path = _extract_after(raw, "scan project") or _extract_after(raw, "analyze project")
        return safe_execute(lambda: scan_project(path, ask_model), "Failed to scan project.")

    # --- Screen ---
    if "what is on my screen" in low or "analyze screen" in low:
        return safe_execute(analyze_screen, "Failed to analyze the screen.")

    # --- System shortcuts (websites / lock) ---
    system_result = safe_execute(lambda: _run_system_command(low), "")
    if system_result:
        return system_result

    # --- Plugins ---
    _refresh_plugin_tools()
    plugin_result = safe_execute(lambda: run_tool(low, raw), "")
    if plugin_result:
        return plugin_result

    # --- Personal memory store/recall ---
    if "remember" in low:
        parts = raw.replace("remember", "", 1).split("is", 1)
        if len(parts) == 2:
            return remember(parts[0].strip(), parts[1].strip())
        return "Please phrase it as: 'remember [key] is [value]'"

    if low.startswith("what is"):
        key = raw.replace("what is", "", 1).strip()
        stored = recall(key)
        if stored != "I don't know that yet.":
            return stored
        # fall through to LLM / web

    # --- Web search for live data ---
    if _needs_web_search(low):
        speak("Searching the web")
        results = safe_execute(lambda: search_web(raw), "")
        if results:
            context = "\n".join(f"{r[0]}: {r[1]}" for r in results[:3])
            return _llm(
                f"Answer in 2-3 sentences using only this information:\n\n{context}\n\nQuestion: {raw}"
            )
        return "I couldn't find anything online for that."

    # --- Default: AI agent with intent routing ---
    return run_agent(raw, ask_model)
