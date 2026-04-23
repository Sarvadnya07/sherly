"""
INPUT VALIDATOR — input_validator.py
Fixes: #6  duplicate command execution (stateful last-command guard)
        #8  prompt injection (keyword blacklist before any LLM call)
        #1  debouncing (timing guard, already here — improved)
        #25 user trust (always log what passed through)
"""

from __future__ import annotations

import re
import time
import threading

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

MIN_WORD_COUNT = 1
DEBOUNCE_SECONDS = 1.5   # Fix #6: slightly stricter debounce

SINGLE_WORD_ALLOW = {
    "hi", "hello", "hey", "thanks", "help", "status",
    "run", "stop", "yes", "no", "y", "n", "confirm", "cancel",
}

NOISE_PHRASES = {
    "the", "a", "an", "um", "uh", "hmm", "oh", "ah",
    "you", "huh", "like", "so", "okay", "ok",
}

HALLUCINATION_BLACKLIST = {
    "thank you for watching",
    "please subscribe",
    "subtitles by",
    "transcribed by",
    "amara.org",
    "www.",
    "http",
    ".com",
}

# ---------------------------------------------------------------------------
# Fix #8 – Prompt injection blacklist
# ---------------------------------------------------------------------------
# These phrases attempt to override Sherly's system prompt or safety rules.
INJECTION_PATTERNS: list[str] = [
    r"ignore\s+(all\s+)?(previous\s+)?(instructions?|rules?|prompts?)",
    r"forget\s+(all\s+)?(previous\s+)?(instructions?|context)",
    r"you\s+are\s+now\s+",          # "you are now DAN / evil AI"
    r"act\s+as\s+(if\s+)?",
    r"pretend\s+(you\s+are|to\s+be)",
    r"jailbreak",
    r"do\s+anything\s+now",
    r"disregard\s+your\s+",
    r"override\s+(safety|rules?|guidelines?)",
    r"system\s*prompt",
    r"as\s+an?\s+(ai\s+with\s+no\s+restrictions?|unfiltered|uncensored)",
]

# ---------------------------------------------------------------------------
# Thread-safe state  Fix #5/#6
# ---------------------------------------------------------------------------
_state_lock = threading.Lock()
_last_command_time: float = 0.0
_last_command_text: str = ""

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _strip_punctuation(text: str) -> str:
    return re.sub(r"[^\w\s]", "", text).strip()


def _is_hallucination(text: str) -> bool:
    low = text.lower()
    return any(phrase in low for phrase in HALLUCINATION_BLACKLIST)


def _is_injection(text: str) -> bool:
    """Fix #8: detect prompt injection attempts."""
    low = text.lower()
    return any(re.search(p, low) for p in INJECTION_PATTERNS)


def _is_pure_noise(text: str) -> bool:
    words = _strip_punctuation(text).lower().split()
    if not words:
        return True
    meaningful = [w for w in words if w not in NOISE_PHRASES and not w.isdigit()]
    return len(meaningful) == 0


def _is_too_short(text: str) -> bool:
    words = text.strip().split()
    if len(words) < MIN_WORD_COUNT:
        return True
    if len(words) == 1 and words[0].lower() not in SINGLE_WORD_ALLOW:
        return True
    return False


def _is_duplicate(text: str) -> bool:
    """Fix #6: exact duplicate of the immediately previous command."""
    return text.strip().lower() == _last_command_text.lower()


def _is_debounced() -> bool:
    """True when command arrives too quickly after the last one."""
    return (time.time() - _last_command_time) < DEBOUNCE_SECONDS


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def is_valid_input(text: str) -> tuple[bool, str]:
    """
    Returns (True, cleaned_text) or (False, reason_string).

    Fix #8: injection attempts are blocked here — before any LLM call.
    Fix #6: duplicates are rejected here — before any execution.
    """
    if not text or not text.strip():
        return False, "empty"

    text = text.strip()

    # Fix #8 — prompt injection guard (highest priority, before all other checks)
    if _is_injection(text):
        return False, "⛔ Blocked: That input looks like a prompt injection attempt."

    if _is_hallucination(text):
        return False, "Didn't catch that"

    if _is_pure_noise(text):
        return False, "Didn't catch that"

    if _is_too_short(text):
        return False, "Didn't catch that"

    with _state_lock:
        if _is_debounced():
            return False, "Too fast — please wait a moment."
        if _is_duplicate(text):
            return False, "Already processed that command."   # Fix #6

    return True, text


def record_command(text: str) -> None:
    """Call immediately after a command passes validation. Thread-safe via lock."""
    global _last_command_time, _last_command_text
    with _state_lock:
        _last_command_time = time.time()
        _last_command_text = text.strip()
