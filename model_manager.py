import time

import requests

from config_manager import get_api_key, get_current_model
from memory import add_memory, get_context
from memory_brain import load_memory
from runtime_utils import log
from web_search import search_web

ACTIVE_MODEL = None
last_used = time.time()

MAX_OUTPUT_TOKENS = 100
MAX_OUTPUT_CHARS = 250
IDLE_UNLOAD_SECONDS = 60
DEV_MODE = True

BASE_INSTRUCTIONS = """You are Sherly, a precise AI assistant.

Rules:
- If you are unsure, say "I don't know".
- Do not guess or hallucinate.
- Answer only based on reliable information.
- Keep answers short and accurate.
- Answer briefly in 1–2 lines.
"""


def build_prompt(user_input):
    memory = load_memory()
    return f"""
User info:
{memory}

User request:
{user_input}

Respond clearly and briefly.
"""


def _compose_prompt(user_prompt):
    context = get_context()
    prompt_history = f"{context}\n" if context else ""
    base = build_prompt(user_prompt)
    prompt_body = f"{prompt_history}{base}\nAssistant:"
    prompt = f"{BASE_INSTRUCTIONS}\n{prompt_body}"
    if DEV_MODE:
        prompt += "\nExplain like a developer. Include logic."
    return prompt


def _limit_response(text):
    return (text or "")[:MAX_OUTPUT_CHARS]


def _extract_web_fallback(query):
    results = search_web(query)
    if not results:
        return ""
    top = results[0]
    title = top.get("title", "").strip()
    body = top.get("body", "").strip()
    return f"{title}. {body}".strip()


def ask_openai(user_prompt, api_key):
    if not api_key:
        raise ValueError("Missing OpenAI API key")

    prompt = _compose_prompt(user_prompt)
    response = requests.post(
        "https://api.openai.com/v1/chat/completions",
        headers={"Authorization": f"Bearer {api_key}"},
        json={
            "model": "gpt-4o-mini",
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": MAX_OUTPUT_TOKENS,
        },
        timeout=30,
    )
    response.raise_for_status()
    return response.json()["choices"][0]["message"]["content"]


def ask_gemini(user_prompt, api_key):
    if not api_key:
        raise ValueError("Missing Gemini API key")

    prompt = _compose_prompt(user_prompt)
    url = f"https://generativelanguage.googleapis.com/v1/models/gemini-pro:generateContent?key={api_key}"
    response = requests.post(
        url,
        json={
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {"maxOutputTokens": MAX_OUTPUT_TOKENS},
        },
        timeout=30,
    )
    response.raise_for_status()
    return response.json()["candidates"][0]["content"]["parts"][0]["text"]


def ask_groq(user_prompt, api_key):
    if not api_key:
        raise ValueError("Missing Groq API key")

    prompt = _compose_prompt(user_prompt)
    response = requests.post(
        "https://api.groq.com/openai/v1/chat/completions",
        headers={"Authorization": f"Bearer {api_key}"},
        json={
            "model": "llama3-70b-8192",
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": MAX_OUTPUT_TOKENS,
        },
        timeout=30,
    )
    response.raise_for_status()
    return response.json()["choices"][0]["message"]["content"]


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


def run_model(user_prompt, model_name):
    target_model = "phi3" if model_name == "local" else model_name
    prompt = _compose_prompt(user_prompt)
    response = requests.post(
        "http://localhost:11434/api/generate",
        json={
            "model": target_model,
            "prompt": prompt,
            "stream": False,
            "options": {"num_predict": MAX_OUTPUT_TOKENS},
        },
        timeout=45,
    )
    response.raise_for_status()
    return response.json()["response"]


def ask_local(user_prompt, model_name):
    return run_model(user_prompt, model_name)


def ask_model(user_prompt):
    global ACTIVE_MODEL
    global last_used

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
            answer = ask_openai(user_prompt, get_api_key("openai"))
        elif model == "gemini":
            answer = ask_gemini(user_prompt, get_api_key("gemini"))
        elif model == "groq":
            answer = ask_groq(user_prompt, get_api_key("groq"))
        else:
            answer = ask_local(user_prompt, model)
        last_used = time.time()
        clipped = _limit_response(answer)
        add_memory(user_prompt, clipped)
        return clipped
    except Exception as exc:
        log(f"Model error: {exc}")
        web_fallback = _extract_web_fallback(user_prompt)
        if web_fallback:
            return _limit_response(f"Model failed, trying lightweight response... {web_fallback}")
        return "Model failed, trying lightweight response..."


def ensure_model_running(model_name="phi3"):
    # Kept for compatibility with existing imports; no eager preload in ultra-light mode.
    log(f"Skipping eager preload for model {model_name} in ultra-light mode.")
