"""
COMMAND ROUTER — command_router.py
Fixes wired in here:
  #9  command misinterpretation  (deterministic COMMAND_MAP)
  #21 OS-specific failures       (platform.system() guard)
  #24 too much AI dependence     (rule-based first, LLM last resort only)
  #25 user trust                 (show action before execution, confirm risky)
  All previous pillars (1,2,4,5) remain active.
"""

from __future__ import annotations

import json
import os
import platform
import subprocess
from datetime import datetime, timezone

import pyperclip

from action_manager import (
    approve_action, cancel_action, classify_action,
    get_history, list_pending, log_action, request_approval, undo_last,
)
from agent_manager import run_agent
from config_manager import set_current_model
from input_validator import is_valid_input, record_command
from model_manager import ask_model
from plugin_manager import get_enabled_plugin_names, run_plugin
from runtime_utils import safe_execute, timeout_call, log
from safety_guard import check_command, handle_confirmation_reply
from text_to_speech import speak
from tool_registry import clear_tools, register_tool, run_tool
from tools.dictation import start_dictation
from tools.error_tools import analyze_error
from tools.file_tools import explain_file
from tools.project_tools import scan_project
from tools.screen_tools import analyze_screen
from tools.terminal_tools import safe_exec, run_command
from tools.task_engine import execute_task
from tools.fix_project import apply_last_fix, fix_project
from web_search import search_web
from memory_brain import recall, remember
from conversation_memory import add_to_memory, build_prompt


# ---------------------------------------------------------------------------
# Runtime state
# ---------------------------------------------------------------------------

MODE = "fast"   # fast | deep | dev
LAST_INTERACTION: dict[str, str] = {"user": "", "assistant": ""}
FEEDBACK_FILE = "feedback_log.jsonl"
SHERLY_PHASE = os.getenv("SHERLY_PHASE", "A").strip().upper()

_PHASE_ORDER = {"A": 1, "B": 2, "C": 3}

_stored_phase = recall("phase").strip().upper()
if _stored_phase in _PHASE_ORDER:
    SHERLY_PHASE = _stored_phase


# ---------------------------------------------------------------------------
# Fix #9 – deterministic command map (no LLM for known shortcuts)
# ---------------------------------------------------------------------------

def _build_command_map() -> dict[str, str]:
    """Build OS-appropriate command map. Fix #21: platform branching."""
    _os = platform.system()

    if _os == "Windows":
        return {
            "open chrome":   r"C:\Program Files\Google\Chrome\Application\chrome.exe",
            "open vscode":   "code",
            "open notepad":  "notepad",
            "open explorer": "explorer",
            "open terminal": "start cmd",
            "open settings": "start ms-settings:",
            "open task manager": "taskmgr",
        }
    elif _os == "Darwin":
        return {
            "open chrome":   "open -a 'Google Chrome'",
            "open vscode":   "code",
            "open terminal": "open -a Terminal",
            "open finder":   "open .",
        }
    else:  # Linux
        return {
            "open chrome":   "google-chrome",
            "open vscode":   "code",
            "open terminal": "x-terminal-emulator",
            "open files":    "xdg-open .",
        }


COMMAND_MAP: dict[str, str] = _build_command_map()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _llm(prompt: str, store_history: bool = False, use_context: bool = False) -> str:
    return safe_execute(
        lambda: ask_model(prompt, store_history=store_history, use_context=use_context),
        "I hit an internal error while generating a response.",
    )


def _phase_at_least(target: str) -> bool:
    return _PHASE_ORDER.get(SHERLY_PHASE, 1) >= _PHASE_ORDER.get(target, 1)


def _set_phase(low: str) -> str | None:
    global SHERLY_PHASE
    for label in ("a", "b", "c"):
        if f"phase {label}" in low or f"set phase {label}" in low:
            SHERLY_PHASE = label.upper()
            remember("phase", label.upper())
            return f"Phase set to {label.upper()}."
    if "show phase" in low or "phase status" in low:
        return f"Current phase: {SHERLY_PHASE}"
    return None


def _style_instruction() -> str:
    if MODE == "deep":
        return "Answer in 4-6 concise sentences. Be structured and practical."
    if MODE == "dev":
        return "Answer technically with precise steps, commands, or code-level guidance."
    return "Answer in 1-2 short sentences. Be natural, not robotic."


def _looks_like_error(output: str) -> bool:
    low = (output or "").lower()
    markers = ["error", "traceback", "exception", "failed", "not found", "timed out", "permission denied"]
    return any(m in low for m in markers)


def _log_feedback(user_text: str, assistant_text: str, rating: str = "unrated") -> None:
    entry = {
        "time": datetime.now(timezone.utc).isoformat(),   # Fix #17
        "user": user_text,
        "assistant": assistant_text,
        "rating": rating,
    }
    try:
        with open(FEEDBACK_FILE, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    except Exception:
        pass


def _finalize_response(user_text: str, response: str) -> str:
    response = (response or "Something went wrong. Please try again.")[:500]   # Fix #23
    add_to_memory(user_text, response)
    if _phase_at_least("C"):
        LAST_INTERACTION["user"] = user_text
        LAST_INTERACTION["assistant"] = response
        _log_feedback(user_text, response)
        return f"{response}\n\nWas this helpful? (y/n)"
    return response


def _record_rating(rating: str) -> str:
    if not _phase_at_least("C"):
        return "Feedback learning is enabled in Phase C."
    user_text = LAST_INTERACTION.get("user", "")
    assistant_text = LAST_INTERACTION.get("assistant", "")
    if not user_text or not assistant_text:
        return "There is no recent answer to rate yet."
    _log_feedback(user_text, assistant_text, rating=rating)
    return "Feedback saved."


def _explain_clipboard() -> str:
    code = pyperclip.paste()
    if not code:
        return "Nothing found on clipboard."
    return ask_model(f"Explain this code clearly:\n\n{code[:3000]}")


def _needs_web_search(text: str) -> bool:
    keywords = [
        "latest", "news", "today", "current", "recent",
        "price", "weather", "score", "who won", "live",
    ]
    return any(w in text for w in keywords)


def _run_system_command(low: str) -> str | None:
    """
    Fix #9: check deterministic COMMAND_MAP first.
    Fix #21: commands are already OS-appropriate from _build_command_map().
    Fix #25: log the action being taken for user trust / auditability.
    """
    for trigger, cmd in COMMAND_MAP.items():
        if trigger in low:
            log(f"[Router] system shortcut: '{trigger}' → '{cmd}'")
            try:
                if platform.system() == "Windows":
                    os.startfile(cmd) if not cmd.startswith(("start ", "code")) else subprocess.Popen(cmd, shell=True)
                else:
                    subprocess.Popen(cmd, shell=True)
                return f"Opening {trigger.replace('open ', '')}."
            except FileNotFoundError:
                return f"Could not find '{trigger}'. Is it installed?"
            except Exception as exc:
                return f"Failed to open: {exc}"

    if "lock computer" in low or "lock screen" in low:
        if platform.system() == "Windows":
            os.system("rundll32.exe user32.dll,LockWorkStation")
            return "Locking your computer."
        return "Lock screen is only supported on Windows."

    return None


def _extract_after(raw: str, keyword: str) -> str:
    idx = raw.lower().find(keyword)
    if idx == -1:
        return ""
    return raw[idx + len(keyword):].strip(" \"'")


def _refresh_plugin_tools() -> None:
    clear_tools()
    for name in get_enabled_plugin_names():
        register_tool(name, lambda q, n=name: run_plugin(n, q))


def _learn_user_preferences(raw: str, low: str) -> None:
    if "vscode" in low or "vs code" in low:
        remember("editor", "vscode")
    if "python" in low:
        remember("language", "python")
    if "sherly" in low or "this project" in low:
        remember("project", "sherly")


def _build_contextual_prompt(user_input: str) -> str:
    history = build_prompt(user_input)
    clarify = "If unsure, ask one short clarification question.\n" if _phase_at_least("B") else ""
    return f"{_style_instruction()}\n{clarify}\n{history}"


def think(prompt: str, ask_model_func) -> str:
    planning_prompt = f"""
Understand and plan this request.

User: {prompt}

Return strictly in this format:
Intent: <one line>
Steps:
1. <step>
2. <step>
3. <step>
"""
    return safe_execute(
        lambda: ask_model_func(planning_prompt, store_history=False, use_context=False),
        "Intent: general question\nSteps:\n1. Understand the request\n2. Answer directly",
    )


def _self_heal_command_error(command: str, output: str) -> str:
    prompt = f"""
A command failed. Suggest a fix.

Command:
{command}

Output/Error:
{output}

Return:
1) likely cause (1 line)
2) fixed command (1 line)
"""
    return _llm(prompt, store_history=False, use_context=False)


def _run_project_action() -> str:
    preferred_lang = recall("language").lower()
    if "python" in preferred_lang or preferred_lang == "i don't know that yet.":
        output = run_command("python main.py")
        if _phase_at_least("C") and _looks_like_error(output):
            fix = _self_heal_command_error("python main.py", output)
            return f"Project run failed.\n\n{output}\n\nSuggested fix:\n{fix}"
        return output
    return "I need your preferred project run command. You can say: remember run command is <command>."


def _set_mode(low: str) -> str | None:
    global MODE
    for m_name in ("deep", "dev", "fast"):
        if f"{m_name} mode" in low or f"mode {m_name}" in low:
            MODE = m_name
            remember("mode", m_name)
            return f"Mode set to {m_name}."
    return None


# ---------------------------------------------------------------------------
# Main router
# ---------------------------------------------------------------------------

def route_command(text: str) -> str:
    # ── Pillar 1: INPUT VALIDATION + Fix #8 injection guard ─────────────────
    valid, cleaned = is_valid_input(text)
    if not valid:
        return cleaned

    record_command(cleaned)
    raw = cleaned
    low = raw.lower().replace(",", "").replace(".", "").replace("?", "").replace("sherly", "").strip()

    # ── Pillar 5: safety_guard CONFIRMATION REPLY ─────────────────────────
    confirm_reply = handle_confirmation_reply(low)
    if confirm_reply is not None:
        if confirm_reply.startswith("__CONFIRMED__:"):
            confirmed_cmd = confirm_reply[len("__CONFIRMED__:"):]
            log(f"[Router] confirmed execution: {confirmed_cmd}")
            output = safe_execute(lambda: safe_exec(confirmed_cmd), "Failed to run the command.")
            return _finalize_response(raw, output)
        return confirm_reply

    # ── System 1: APPROVAL QUEUE — approve <id> ──────────────────────────
    if low.startswith("approve"):
        action_id = raw.split(None, 1)[1].strip() if len(raw.split()) > 1 else ""
        if not action_id:
            return _finalize_response(raw, "Please provide an action ID. Example: approve abc12345")

        try:
            from tools.preview import preview_store, apply_preview
            if action_id in preview_store:
                result = safe_execute(lambda: apply_preview(action_id), "Failed to apply preview.")
                
                # Auto-rerun loop logic
                try:
                    from tools.fix_project import LAST_FIX_CONTEXT, apply_last_fix
                    from tools.executor import run_project
                    cmd = LAST_FIX_CONTEXT.get("command")
                    if cmd:
                        status, output = safe_execute(lambda: run_project(cmd), ("error", "Failed to run command"))
                        if status == "success":
                            result += f"\n\n✅ Project re-run successful! System restored."
                            LAST_FIX_CONTEXT["error"] = None
                        else:
                            LAST_FIX_CONTEXT["error"] = output
                            result += f"\n\n❌ Error persisted during auto re-run:\n{output[:300]}\n\nGenerating subsequent fix attempt..."
                            retry_preview = safe_execute(lambda: apply_last_fix(ask_model), "Failed to generate secondary fix.")
                            result += f"\n\n{retry_preview}"
                except Exception as exc:
                    log(f"Auto-fix loop failure: {exc}")

                return _finalize_response(raw, result)
        except Exception:
            pass

        result = safe_execute(
            lambda: approve_action(action_id, safe_exec),
            "Failed to execute approved action."
        )
        return _finalize_response(raw, result)

    # ── System 1: APPROVAL QUEUE — cancel <id> ───────────────────────────
    if low.startswith("cancel"):
        action_id = raw.split(None, 1)[1].strip() if len(raw.split()) > 1 else ""
        if action_id:
            result = safe_execute(lambda: cancel_action(action_id), "Failed to cancel.")
            return _finalize_response(raw, result)

    # ── System 1: list pending ────────────────────────────────────────────
    if "pending actions" in low or "pending" in low and "action" in low:
        return _finalize_response(raw, list_pending())

    # ── System 2: UNDO ────────────────────────────────────────────────────
    if low in {"undo", "undo last"} or low.startswith("undo last"):
        result = safe_execute(undo_last, "Nothing to undo.")
        return _finalize_response(raw, result)

    # ── System 2: ACTION HISTORY ──────────────────────────────────────────
    if "show history" in low or "action history" in low or "recent actions" in low:
        return _finalize_response(raw, get_history())

    if _phase_at_least("C") and low in {"y", "yes"}:
        return _record_rating("y")
    if _phase_at_least("C") and low in {"n", "no"}:
        return _record_rating("n")

    phase_result = _set_phase(low)
    if phase_result:
        return _finalize_response(raw, phase_result)

    if _phase_at_least("B") and len(raw.split()) < 2 and low not in SINGLE_WORD_ALLOW:
        return "Can you clarify what you mean?"

    if _phase_at_least("C"):
        _learn_user_preferences(raw, low)

    if _phase_at_least("B"):
        quick_replies = {
            "hi": "Hey.", "hello": "Hello.",
            "thanks": "You're welcome.", "thank you": "You're welcome.",
        }
        if low in quick_replies:
            return _finalize_response(raw, quick_replies[low])

    mode_result = _set_mode(low)
    if mode_result:
        return _finalize_response(raw, mode_result)

    # --- Model switching ---
    for keyword, model_name in [
        ("use openai", "openai"), ("switch to openai", "openai"),
        ("use gemini", "gemini"), ("switch to gemini", "gemini"),
        ("use groq", "groq"), ("switch to groq", "groq"),
        ("use local", "local"), ("switch to local", "local"),
    ]:
        if keyword in low:
            return _finalize_response(raw, set_current_model(model_name))

    # --- Dictation ---
    if "start dictation" in low:
        response = safe_execute(
            lambda: "Dictation captured." if start_dictation() else "No speech captured.",
            "Failed to start dictation.",
        )
        return _finalize_response(raw, response)

    # --- Project execution ---
    if "run project" in low or "start project" in low:
        return _finalize_response(raw, _run_project_action())

    # --- Fix / apply fix ---
    if "fix my project" in low:
        speak("Running your project")
        result = safe_execute(lambda: fix_project(ask_model), "Failed to run project fix workflow.")
        return _finalize_response(raw, result)

    if "apply fix" in low:
        speak("Applying fix")
        result = safe_execute(lambda: apply_last_fix(ask_model), "Failed to apply project fix.")
        speak("Re-running project")
        return _finalize_response(raw, result)

    # --- Terminal commands — System 1 approval gate + Pillar 4+5 ---
    if "run command" in low or "execute" in low:
        cmd = _extract_after(raw, "run command") or _extract_after(raw, "execute")
        if not cmd:
            return _finalize_response(raw, "Please specify the command to run.")

        # System 1: check if this needs approval before executing
        action_level = classify_action(cmd)
        if action_level == "dangerous":
            log_action(cmd, "dangerous_blocked", undoable=False)
            return _finalize_response(raw, "⛔ Blocked: That command is too dangerous to execute.")
        if action_level == "confirm":
            prompt = safe_execute(lambda: request_approval(cmd), "Failed to queue approval.")
            return _finalize_response(raw, prompt)

        # SAFE — run immediately through whitelist + safety guard
        log(f"[Router] safe terminal execution: {cmd}")
        output = safe_execute(lambda: safe_exec(cmd), "Failed to run the command.")
        log_action(cmd, "terminal_safe", undoable=False)
        if _phase_at_least("C") and _looks_like_error(output):
            fix = _self_heal_command_error(cmd, output)
            return _finalize_response(raw, f"{output}\n\nSuggested fix:\n{fix}")
        return _finalize_response(raw, output)

    # --- Code / error tools ---
    if "explain error" in low or "analyze error" in low:
        response = safe_execute(lambda: analyze_error(ask_model), "Failed to analyze the error.")
        return _finalize_response(raw, response)

    if "explain this code" in low or "explain code" in low:
        response = safe_execute(_explain_clipboard, "Failed to explain clipboard content.")
        return _finalize_response(raw, response)

    # --- File tools ---
    if "open file" in low or "read file" in low:
        path = _extract_after(raw, "open file") or _extract_after(raw, "read file")
        if not path:
            return _finalize_response(raw, "Please specify a file path.")
        response = safe_execute(lambda: explain_file(path, ask_model), "Failed to open that file.")
        return _finalize_response(raw, response)

    if "scan project" in low or "analyze project" in low:
        path = _extract_after(raw, "scan project") or _extract_after(raw, "analyze project")
        response = safe_execute(lambda: scan_project(path, ask_model), "Failed to scan project.")
        return _finalize_response(raw, response)

    # --- Screen ---
    if "what is on my screen" in low or "analyze screen" in low:
        response = safe_execute(analyze_screen, "Failed to analyze the screen.")
        return _finalize_response(raw, response)

    # --- System shortcuts Fix #9 + #21 ---
    system_result = safe_execute(lambda: _run_system_command(low), "")
    if system_result:
        return _finalize_response(raw, system_result)

    # --- Plugins ---
    _refresh_plugin_tools()
    plugin_result = safe_execute(lambda: run_tool(low, raw), "")
    if plugin_result:
        return _finalize_response(raw, plugin_result)

    # --- Memory ---
    if "remember" in low:
        parts = raw.replace("remember", "", 1).split("is", 1)
        if len(parts) == 2:
            return _finalize_response(raw, remember(parts[0].strip(), parts[1].strip()))
        return _finalize_response(raw, "Please phrase it as: 'remember [key] is [value]'")

    if low.startswith("what is"):
        key = raw.replace("what is", "", 1).strip()
        stored = recall(key)
        if stored != "I don't know that yet.":
            return _finalize_response(raw, stored)

    # --- Web search ---
    if _needs_web_search(low):
        speak("Searching the web")
        results = safe_execute(lambda: search_web(raw), [])
        if results:
            context = "\n".join(f"{r.get('title','')}: {r.get('body','')}" for r in results[:3])
            response = _llm(
                f"{_style_instruction()}\nUse only this information:\n\n{context}\n\nQuestion: {raw}",
                store_history=False,
                use_context=False,
            )
            return _finalize_response(raw, response)
        return _finalize_response(raw, "Network unavailable or no results found.")   # Fix #13

    # --- Fix #24: structured planner before raw LLM ---
    if _phase_at_least("B"):
        plan = think(raw, ask_model)
        if any(trigger in low for trigger in ["do this", "step by step", "execute plan", "automate", "workflow"]):
            task_result = safe_execute(lambda: execute_task(plan, ask_model), "Failed to execute planned steps.")
            return _finalize_response(raw, task_result)

    # --- LAST RESORT: LLM (Fix #24 — only reaches here if nothing else matched) ---
    contextual_prompt = _build_contextual_prompt(raw)
    agent_result = safe_execute(
        lambda: run_agent(contextual_prompt, ask_model),
        "Something went wrong. Please try again.",   # Fix #23
    )
    return _finalize_response(raw, agent_result)


# Fix #19 – future multi-user support hook (placeholder)
SINGLE_WORD_ALLOW = {
    "hi", "hello", "hey", "thanks", "help", "status",
    "run", "stop", "yes", "no", "y", "n", "confirm", "cancel",
}
