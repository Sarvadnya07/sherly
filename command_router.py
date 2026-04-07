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


def ask_llm(prompt):
    return safe_execute(
        lambda: ask_model(
            f"You are Sherly, a desktop AI assistant. Max 2 sentences.\nUser: {prompt}"
        ),
        "I hit an internal error while generating a response.",
    )


def explain_clipboard(ask_model):
    code = pyperclip.paste()

    if not code:
        return "No code copied"

    prompt = f"""
Explain this code clearly:

{code[:2000]}
"""

    return ask_model(prompt)


def needs_web_search(text):
    keywords = ["latest", "news", "today", "current", "recent", "price", "weather", "score", "who won"]
    return any(word in text for word in keywords)


def run_system_command(text):
    if "open github" in text or "github" in text:
        webbrowser.open("https://github.com")
        return "Opening GitHub"

    if "open chatgpt" in text:
        webbrowser.open("https://chat.openai.com")
        return "Opening ChatGPT"

    if "google" in text:
        webbrowser.open("https://google.com")
        return "Opening Google"

    if "youtube" in text:
        webbrowser.open("https://youtube.com")
        return "Opening YouTube"

    if "chrome" in text:
        try:
            subprocess.Popen("C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe")
            return "Opening Chrome"
        except FileNotFoundError:
            return "Chrome path not found."

    if "lock computer" in text:
        os.system("rundll32.exe user32.dll,LockWorkStation")
        return "Locking your computer"

    return None


def _extract_path(raw_text, keyword):
    index = raw_text.lower().find(keyword)
    if index == -1:
        return None
    return raw_text[index + len(keyword):].strip(" \"'")


def _extract_command_tail(raw_text, keyword):
    index = raw_text.lower().find(keyword)
    if index == -1:
        return ""
    return raw_text[index + len(keyword):].strip()


def _refresh_plugin_tools():
    clear_tools()
    for plugin_name in get_enabled_plugin_names():
        register_tool(plugin_name, lambda query, plugin_name=plugin_name: run_plugin(plugin_name, query))


def route_command(text):
    raw_text = text.strip()
    cleaned_text = raw_text.lower().replace(",", "").replace(".", "").replace("?", "").strip()
    cleaned_text = cleaned_text.replace("sherly", "").strip()

    print("DEBUG ROUTER:", cleaned_text)

    if "use openai" in cleaned_text or "switch to openai" in cleaned_text:
        return set_current_model("openai")

    if "use gemini" in cleaned_text or "switch to gemini" in cleaned_text:
        return set_current_model("gemini")

    if "use groq" in cleaned_text or "switch to groq" in cleaned_text:
        return set_current_model("groq")

    if "use local" in cleaned_text or "switch to local" in cleaned_text:
        return set_current_model("local")

    if "start dictation" in cleaned_text:
        return safe_execute(lambda: "Dictation captured." if start_dictation() else "No speech captured.", "Failed to start dictation.")

    if "run command" in cleaned_text or "execute" in cleaned_text:
        cmd = _extract_path(raw_text, "run command") or _extract_path(raw_text, "execute")
        if not cmd:
            return "Please specify the command to run."
        return safe_execute(lambda: run_command(cmd), "Failed to run command.")

    if "explain error" in cleaned_text or "analyze error" in cleaned_text:
        return safe_execute(lambda: analyze_error(ask_model), "Failed to analyze the error.")

    if "explain this code" in cleaned_text:
        return safe_execute(lambda: explain_clipboard(ask_model), "Failed to explain clipboard content.")

    if "open file" in cleaned_text or "read file" in cleaned_text:
        path = _extract_path(raw_text, "open file") or _extract_path(raw_text, "read file")
        if not path:
            return "Please specify a file path."
        return safe_execute(lambda: explain_file(path, ask_model), "Failed to open file.")

    if "scan project" in cleaned_text or "analyze project" in cleaned_text:
        path = _extract_path(raw_text, "scan project") or _extract_path(raw_text, "analyze project")
        return safe_execute(lambda: scan_project(path, ask_model), "Failed to scan project.")

    if "what is on my screen" in cleaned_text:
        return safe_execute(analyze_screen, "Failed to analyze the screen.")

    if "open app" in cleaned_text:
        app = _extract_command_tail(raw_text, "open app")
        if not app:
            return "Please specify which app to open."
        return safe_execute(lambda: open_app(app), "Failed to open app.")

    tokens = cleaned_text.split()
    if tokens and tokens[0] == "type":
        content = _extract_command_tail(raw_text, "type")
        if not content:
            return "Please tell me what to type."
        return safe_execute(lambda: type_text(content), "Failed to type text.")

    if "do task" in cleaned_text or "perform task" in cleaned_text:
        return safe_execute(lambda: execute_task(raw_text, ask_model), "Failed to execute task.")

    system_action = safe_execute(lambda: run_system_command(cleaned_text), "")
    if system_action:
        return system_action

    _refresh_plugin_tools()
    plugin_result = safe_execute(lambda: run_tool(cleaned_text, raw_text), "")
    if plugin_result:
        return plugin_result

    if "remember" in cleaned_text:
        parts = raw_text.replace("remember", "", 1).split("is", 1)
        if len(parts) == 2:
            return remember(parts[0].strip(), parts[1].strip())
        return "Please provide a key and value to remember."

    if cleaned_text.startswith("what is"):
        return recall(raw_text.replace("what is", "", 1).strip())

    if needs_web_search(cleaned_text):
        speak("Searching the web")
        results = search_web(raw_text)
        if not results:
            return "I couldn't find anything online."

        context = "\n".join([f"{r['title']} - {r['body']}" for r in results[:3]])
        prompt = f"""
Answer briefly (2–3 lines max).

Context:
{context}

Question:
{raw_text}
"""
        return ask_llm(prompt)

    return run_agent(raw_text, ask_model)
