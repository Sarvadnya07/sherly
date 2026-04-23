"""
agent_manager — classifies user intent and routes to the correct agent.
"""
from agents import browser_agent, coder_agent, system_agent

# Valid categories (whitelist — anything else falls back to "general")
_KNOWN_AGENTS = {"coder", "browser", "system", "general"}

# Instant keyword routing — bypasses LLM classification for speed & reliability
_BROWSER_TRIGGERS = [
    "search ", "search for ", "look up ", "find ", "google ",
    "open youtube", "open google", "open browser", "open chrome", "browse ",
    "show me ", "watch ",
]
_CODER_TRIGGERS = [
    "code ", "debug ", "fix this code", "write a ", "explain this code",
    "function ", "class ", "script ", "algorithm ",
    "how to implement", "how do i code",
]
_SYSTEM_TRIGGERS = [
    "open app", "close app", "run command", "type ", "execute ",
    "launch ", "start app", "shutdown", "restart", "lock ",
    "write ", "open ", "pause", "resume", "mute", "volume", 
    "increase ", "decrease ", "next track", "previous track",
    "play pause", "ope "
]

_CLASSIFY_PROMPT = """\
You are a strict request classifier. Respond with EXACTLY ONE word:

  general — greetings, language questions, facts, definitions, small talk, any single word or short phrase with no clear action
  browser — searching the web, looking something up, playing a video, YouTube, Google searches
  coder   — code questions, debugging, writing scripts, programming help
  system  — opening/closing apps, running terminal commands, controlling the PC

Rules:
- A single word like "Japanese", "hello", "python" → always "general"
- "search X", "find X", "look up X", "play X on youtube" → always "browser"
- When in doubt → "general"

Only output the single word. No punctuation, no explanation.

Request: {text}
"""


def _keyword_classify(text: str) -> str | None:
    """Fast local classification using keyword triggers. Returns None if unsure."""
    low = text.lower().strip()
    if any(low.startswith(t) or f" {t}" in low for t in _BROWSER_TRIGGERS):
        return "browser"
    if any(low.startswith(t) or f" {t}" in low for t in _SYSTEM_TRIGGERS):
        return "system"
    if any(low.startswith(t) or f" {t}" in low for t in _CODER_TRIGGERS):
        return "coder"
    # Single-word or very short input → treat as general conversation
    if len(low.split()) <= 2:
        return "general"
    return None


def _classify(text: str, ask_model) -> str:
    """Classify the request: try keyword matching first, then LLM."""
    # 1. Fast keyword check
    keyword_result = _keyword_classify(text)
    if keyword_result:
        return keyword_result

    # 2. LLM fallback for ambiguous longer requests
    raw = ask_model(
        _CLASSIFY_PROMPT.format(text=text),
        store_history=False,
        use_context=False,
    )
    word = raw.strip().lower().split()[0] if raw.strip() else "general"
    word = word.strip(".,!?;:()")
    return word if word in _KNOWN_AGENTS else "general"


def run_agent(text: str, ask_model) -> str:
    """Route the request to the right agent or answer directly."""
    category = _classify(text, ask_model)

    if category == "browser":
        return browser_agent.run(text, ask_model)

    if category == "coder":
        return coder_agent.run(text, ask_model)

    if category == "system":
        return system_agent.run(text, ask_model)

    # "general" → direct, natural LLM answer (no agent wrapping)
    return ask_model(text)
