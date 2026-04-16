import json
import time
import functools

import requests
from tenacity import retry, stop_after_attempt, wait_fixed

try:
    from pybreaker import CircuitBreaker
except ImportError:
    class CircuitBreaker:
        def __init__(self, fail_max=3, reset_timeout=30):
            self.fail_max = fail_max
            self.reset_timeout = reset_timeout
            self.failures = 0
            self.state = "closed"
            self.opened_at = 0

        def _allow_call(self):
            if self.state == "open":
                if time.time() - self.opened_at > self.reset_timeout:
                    self.state = "half_open"
                else:
                    raise RuntimeError("Circuit open")

        def __call__(self, func):
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                self._allow_call()
                try:
                    result = func(*args, **kwargs)
                except Exception:
                    self.failures += 1
                    if self.failures >= self.fail_max:
                        self.state = "open"
                        self.opened_at = time.time()
                    raise
                else:
                    self.failures = 0
                    self.state = "closed"
                    return result
            return wrapper

from config_manager import get_api_key, get_current_model
from memory import add_memory, get_context
from memory_brain import load_memory
from runtime_utils import log
from web_search import search_web

ACTIVE_MODEL = None
last_used = time.time()

MAX_OUTPUT_TOKENS = 500
MAX_OUTPUT_CHARS = 2000
IDLE_UNLOAD_SECONDS = 300
_breaker = CircuitBreaker(fail_max=3, reset_timeout=30)

SYSTEM_PROMPT = (
    "You are Sherly, a friendly desktop AI assistant.\n"
    "Rules:\n"
    "- Answer naturally and directly.\n"
    "- Keep responses to 1-2 sentences unless more detail is genuinely needed.\n"
    "- For greetings, just greet back warmly.\n"
    "- Never explain your own internal classification or reasoning.\n"
    "- Do not hallucinate facts.\n"
)


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _get_background_info() -> str:
    """Return JSON-formatted user memory or empty string."""
    try:
        memory = load_memory()
        if not memory:
            return ""
        return "User background:\n" + json.dumps(memory, indent=2, ensure_ascii=False)
    except Exception:
        return ""


def _get_history_messages(limit: int = 5) -> list:
    """Return the last *limit* exchanges as role-tagged message dicts."""
    try:
        context = get_context(limit=limit)
    except Exception:
        return []
    if not context:
        return []

    messages = []
    for line in context.split("\n"):
        if line.startswith("User: "):
            messages.append({"role": "user", "content": line[6:]})
        elif line.startswith("Assistant: "):
            messages.append({"role": "assistant", "content": line[11:]})
    return messages


def _limit_response(text: str) -> str:
    return (text or "")[:MAX_OUTPUT_CHARS]


def _extract_web_fallback(query: str) -> str:
    try:
        results = search_web(query)
        if not results:
            return ""
        top = results[0]
        return f"{top.get('title', '')}. {top.get('body', '')}".strip()
    except Exception:
        return ""


def _build_system(use_context: bool) -> str:
    """Compose system string with optional background knowledge."""
    system = SYSTEM_PROMPT
    if use_context:
        bg = _get_background_info()
        if bg:
            system += f"\n{bg}\n"
    return system


# ---------------------------------------------------------------------------
# Provider functions
# ---------------------------------------------------------------------------

def ask_openai(user_prompt: str, api_key: str, use_context: bool = True) -> str:
    if not api_key or api_key == "YOUR_OPENAI_KEY":
        return "OpenAI API key is missing. Please set it in config.json."

    messages = [{"role": "system", "content": _build_system(use_context)}]
    if use_context:
        messages.extend(_get_history_messages())
    messages.append({"role": "user", "content": user_prompt})

    r = requests.post(
        "https://api.openai.com/v1/chat/completions",
        headers={"Authorization": f"Bearer {api_key}"},
        json={"model": "gpt-4o-mini", "messages": messages, "max_tokens": MAX_OUTPUT_TOKENS},
        timeout=30,
    )
    r.raise_for_status()
    return r.json()["choices"][0]["message"]["content"]


def ask_gemini(user_prompt: str, api_key: str, use_context: bool = True) -> str:
    if not api_key or api_key == "YOUR_GEMINI_KEY":
        return "Gemini API key is missing. Please set it in config.json."

    system = _build_system(use_context)
    contents = []

    if use_context:
        for h in _get_history_messages():
            role = "user" if h["role"] == "user" else "model"
            contents.append({"role": role, "parts": [{"text": h["content"]}]})

    # Prepend system instructions to the first/only user turn
    contents.append({"role": "user", "parts": [{"text": f"{system}\n\n{user_prompt}"}]})

    r = requests.post(
        f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}",
        json={"contents": contents, "generationConfig": {"maxOutputTokens": MAX_OUTPUT_TOKENS}},
        timeout=30,
    )
    r.raise_for_status()
    return r.json()["candidates"][0]["content"]["parts"][0]["text"]


def ask_groq(user_prompt: str, api_key: str, use_context: bool = True) -> str:
    if not api_key or api_key == "YOUR_GROQ_KEY":
        return "Groq API key is missing. Please set it in config.json."

    messages = [{"role": "system", "content": _build_system(use_context)}]
    if use_context:
        messages.extend(_get_history_messages())
    messages.append({"role": "user", "content": user_prompt})

    r = requests.post(
        "https://api.groq.com/openai/v1/chat/completions",
        headers={"Authorization": f"Bearer {api_key}"},
        json={"model": "llama3-70b-8192", "messages": messages, "max_tokens": MAX_OUTPUT_TOKENS},
        timeout=30,
    )
    r.raise_for_status()
    return r.json()["choices"][0]["message"]["content"]


# ---------------------------------------------------------------------------
# Local (Ollama) model
# ---------------------------------------------------------------------------

def unload_model():
    global ACTIVE_MODEL
    if not ACTIVE_MODEL:
        return
    try:
        requests.post(
            "http://localhost:11434/api/generate",
            json={"model": ACTIVE_MODEL, "keep_alive": 0},
            timeout=3,
        )
        log(f"Unloaded model: {ACTIVE_MODEL}")
    except Exception as exc:
        log(f"Unload warning ({ACTIVE_MODEL}): {exc}")
    finally:
        ACTIVE_MODEL = None


def _unload_if_idle():
    if ACTIVE_MODEL and time.time() - last_used > IDLE_UNLOAD_SECONDS:
        unload_model()


@retry(stop=stop_after_attempt(3), wait=wait_fixed(1))
def _local_call(prompt: str, target_model: str) -> str:
    r = requests.post(
        "http://localhost:11434/api/generate",
        json={"model": target_model, "prompt": prompt, "stream": False,
              "options": {"num_predict": MAX_OUTPUT_TOKENS}},
        timeout=30,
    )
    r.raise_for_status()
    return r.json()["response"]


@_breaker
def run_model(user_prompt: str, model_name: str, use_context: bool = True) -> str:
    target_model = "phi3" if model_name == "local" else model_name
    system = _build_system(use_context)
    prompt = system + "\n\n"

    if use_context:
        for h in _get_history_messages():
            prompt += f"{h['role'].capitalize()}: {h['content']}\n"

    prompt += f"User: {user_prompt}\nAssistant:"
    return _local_call(prompt, target_model)


def ask_local(user_prompt: str, model_name: str, use_context: bool = True) -> str:
    return run_model(user_prompt, model_name, use_context=use_context)


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------

def ask_model(user_prompt: str, store_history: bool = True, use_context: bool = True) -> str:
    global ACTIVE_MODEL, last_used

    _unload_if_idle()

    model = get_current_model()
    if model == "local":
        model = "phi3"

    if model not in {"openai", "gemini", "groq"} and ACTIVE_MODEL != model:
        unload_model()
        ACTIVE_MODEL = model
        log(f"Active local model set: {ACTIVE_MODEL}")

    try:
        if model == "openai":
            answer = ask_openai(user_prompt, get_api_key("openai"), use_context=use_context)
        elif model == "gemini":
            answer = ask_gemini(user_prompt, get_api_key("gemini"), use_context=use_context)
        elif model == "groq":
            answer = ask_groq(user_prompt, get_api_key("groq"), use_context=use_context)
        else:
            answer = ask_local(user_prompt, model, use_context=use_context)

        last_used = time.time()
        clipped = _limit_response(answer)
        if store_history:
            add_memory(user_prompt, clipped)
        return clipped

    except Exception as exc:
        log(f"Model error: {exc}")
        fallback = _extract_web_fallback(user_prompt)
        if fallback:
            return _limit_response(fallback)
        return "Sorry, I ran into an error. Please try again."


def ensure_model_running(model_name: str = "phi3"):
    log(f"Skipping eager preload for {model_name} in ultra-light mode.")
