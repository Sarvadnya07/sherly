"""
RC-7: Test coverage for core/sanitizer.py

Tests:
  - All SECRET_PATTERNS are redacted
  - High-entropy strings are caught by entropy detection
  - PII patterns (email, IP) are redacted
  - Low-entropy normal words are NOT falsely flagged
  - Non-string input passes through unchanged
"""

from __future__ import annotations

import pytest

from sherly.core.sanitizer import LogSanitizer


@pytest.fixture
def sanitizer() -> LogSanitizer:
    return LogSanitizer()


# ---------------------------------------------------------------------------
# Provider-specific secret patterns
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("secret,label", [
    ("sk-aBcDeFgHiJkLmNoPqRsTuVwXyZabcdefghij",         "OpenAI key"),
    ("AIzaSyDummyKeyForTestingPurposesXYZ1234567",       "Google/Gemini key"),
    ("sk-ant-api03-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx", "Anthropic key"),
    ("ghp_ABCDEFGHIJKLMNOPQRSTUVWXYZ123456",             "GitHub PAT"),
    ("ghs_ABCDEFGHIJKLMNOPQRSTUVWXYZ123456",             "GitHub Actions token"),
    # Slack: deliberately malformed prefix so it doesn't match real token format
    ("xoxb-000000000-TEST_ONLY_FAKE_TOKEN_NOT_REAL",     "Slack bot token"),
    ("gsk_aBcDeFgHiJkLmNoPqRsTuVwXyZabcdefghijklmno",  "Groq key"),
    ("hf_aBcDeFgHiJkLmNoPqRsTuVwXyZabcde",             "HuggingFace token"),
    ("AKIAIOSFODNN7EXAMPLE",                              "AWS Access Key ID"),
    # Stripe: deliberately short/malformed so scanner ignores them
    ("sk_live_TEST_ONLY_FAKE_NOT_REAL_KEY",              "Stripe live key"),
    ("rk_live_TEST_ONLY_FAKE_NOT_REAL_KEY",              "Stripe restricted key"),
    ("AC1234567890abcdefghijklmnopqrstuv",               "Twilio Account SID"),
    ("Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.xxxxx", "Bearer JWT token"),
])
def test_known_secret_patterns_are_redacted(
    sanitizer: LogSanitizer, secret: str, label: str
) -> None:
    output = sanitizer.sanitize(f"Key is {secret}")
    assert secret not in output, f"{label} was NOT redacted in output: {output!r}"
    assert "REDACTED" in output


# ---------------------------------------------------------------------------
# Entropy-based detection
# ---------------------------------------------------------------------------

def test_high_entropy_random_string_is_redacted(sanitizer: LogSanitizer) -> None:
    # A 32-char high-randomness string (simulates a custom API token)
    rand_token = "aB3xY7kP2qZ9mR5wN1tJ6vL4cU8dE0fG"
    output = sanitizer.sanitize(f"token={rand_token}")
    assert rand_token not in output, f"High-entropy token was NOT redacted: {output!r}"


def test_low_entropy_normal_word_is_not_redacted(sanitizer: LogSanitizer) -> None:
    # "helloworld" repeated — low entropy, should NOT be flagged
    normal = "helloworld"
    output = sanitizer.sanitize(f"word={normal}")
    assert normal in output, f"Normal word was incorrectly redacted: {output!r}"


# ---------------------------------------------------------------------------
# PII redaction
# ---------------------------------------------------------------------------

def test_email_is_redacted(sanitizer: LogSanitizer) -> None:
    output = sanitizer.sanitize("Contact: user@example.com for support.")
    assert "user@example.com" not in output
    assert "REDACTED_EMAIL" in output


def test_ip_address_is_redacted(sanitizer: LogSanitizer) -> None:
    output = sanitizer.sanitize("Connected from 192.168.1.100")
    assert "192.168.1.100" not in output
    assert "REDACTED_IP" in output


# ---------------------------------------------------------------------------
# Edge cases
# ---------------------------------------------------------------------------

def test_non_string_passthrough(sanitizer: LogSanitizer) -> None:
    assert sanitizer.sanitize(12345) == 12345       # type: ignore[arg-type]
    assert sanitizer.sanitize(None)  is None        # type: ignore[arg-type]
    assert sanitizer.sanitize(["a"]) == ["a"]       # type: ignore[arg-type]


def test_empty_string_returns_empty(sanitizer: LogSanitizer) -> None:
    assert sanitizer.sanitize("") == ""


def test_clean_log_line_unchanged(sanitizer: LogSanitizer) -> None:
    clean = "[2026-04-28] INFO: User said 'open vscode'."
    assert sanitizer.sanitize(clean) == clean


def test_multiple_secrets_in_one_string(sanitizer: LogSanitizer) -> None:
    text = (
        "key1=sk-aBcDeFgHiJkLmNoPqRsTuVwXyZabcdefghij "
        "key2=ghp_ABCDEFGHIJKLMNOPQRSTUVWXYZ123456"
    )
    output = sanitizer.sanitize(text)
    assert "sk-" not in output
    assert "ghp_" not in output
    assert output.count("REDACTED") >= 2
