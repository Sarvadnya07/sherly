# Project Improvement Audit — Sherly AI

*Generated from full codebase analysis. All issues are reproducible and traceable to specific files.*

---

## REQUIRED CHANGES

These are bugs, architectural gaps, or security issues that block production reliability.

---

### RC-1 · Config Manager Reads Disk on Every Call

**File**: `src/sherly/config/config_manager.py`
**Severity**: High (Performance)

Every getter function (`get_current_model`, `get_api_key`, `get_auto_mode`, `get_plugin_enabled`) calls `load_config()` which opens and reads `config.json` from disk. In a single user interaction, this can be called 5–10 times. Under voice-triggered commands, this becomes a steady-state I/O bottleneck.

**Fix**: Introduce a module-level cache:
```python
_config_cache: dict | None = None
_cache_dirty: bool = False

def load_config() -> dict:
    global _config_cache
    if _config_cache is None:
        # ... read from disk
        _config_cache = raw
    return _config_cache

def save_config(config):
    global _config_cache
    _config_cache = config
    with CONFIG_FILE.open("w", ...) as f:
        json.dump(config, f, indent=4)
```

---

### RC-2 · Biometric Approval is a Simulation

**File**: `src/sherly/core/biometrics.py`
**Severity**: High (Security Feature Integrity)

`biometrics.py` does not call any real OS-level authentication API. It is a simulation/POC that always succeeds after a brief sleep. This means the advertised "Windows Hello biometric approval for DANGEROUS commands" is not actually enforced — any text confirmation bypass is sufficient.

**Fix**: Implement `UserConsentVerifier` from the WinRT API via `winsdk` or `pywin32`:
```python
import asyncio
from winsdk.windows.security.credentials.ui import UserConsentVerifier

async def request_biometric_verification(message: str) -> bool:
    result = await UserConsentVerifier.request_verification_async(message)
    return result == UserConsentVerifierResult.VERIFIED
```
Gracefully fall back to a PIN dialog on unsupported hardware. Update `safety_guard.py` to gate `DANGEROUS` classification on the async result.

---

### RC-3 · SQLite Without Write Queue Causes Lock Errors Under Load

**File**: `src/sherly/services/memory.py`, `src/sherly/services/action_manager.py`
**Severity**: High (Reliability)

SQLite in WAL mode can handle concurrent reads, but concurrent writes will raise `sqlite3.OperationalError: database is locked`. The `_save_history()` function in `action_manager.py` is called from the worker thread while the main thread may simultaneously query the DB. No write serialization is enforced.

**Fix**: Wrap all SQLite write operations in a dedicated write lock:
```python
_db_write_lock = threading.Lock()

def _save_history(entry):
    with _db_write_lock:
        conn.execute("INSERT INTO action_history ...", (...))
        conn.commit()
```
Long-term: migrate to SQLAlchemy with connection pooling.

---

### RC-4 · Circular Import Risk Between Router and Services

**File**: `src/sherly/services/command_router.py`
**Severity**: Medium (Reliability / Startup)

`command_router.py` imports from 15+ modules at the top level, several of which themselves import from `model_manager`, which imports from `memory`, which imports from `config_manager`. Python's module initialization order can cause `ImportError` or partial initialization bugs, especially when `route_command()` is first called during module-level code in another file.

**Fix**:
1. Audit the import graph using `pydeps` or `importlab`.
2. Convert heavy imports (especially `from sherly.services.model_manager import ask_model`) to lazy imports inside the functions that need them.
3. Move all module-level side-effect code (like the `_stored_phase = recall(...)` call at line 58) into an `initialize()` function called explicitly from `main.py`.

---

### RC-5 · LLM Intent Firewall Fails Open

**File**: `src/sherly/core/input_validator.py` (line 100)
**Severity**: Medium (Security)

The `_llm_intent_firewall()` function catches all exceptions and returns `False` (i.e., "not malicious"), meaning any error in the LLM call — model timeout, network error, malformed response — causes the firewall to silently pass the input. This is intentional per the comment ("fail open to prevent breaking the assistant"), but it means a targeted DoS against the LLM endpoint defeats the semantic firewall entirely.

**Fix**: Add a secondary regex-only firewall that runs if the LLM firewall errors. The regex blacklist already exists as `INJECTION_PATTERNS` — expand it with 5–10 additional patterns covering known jailbreak templates, and ensure it is always applied regardless of LLM availability. Remove the "fail open" behavior for the LLM check specifically.

---

### RC-6 · `FEEDBACK_FILE` Written to Process CWD

**File**: `src/sherly/services/command_router.py` (line 53)
**Severity**: Medium (Correctness)

`FEEDBACK_FILE = "feedback_log.jsonl"` is a bare filename. It resolves to the **current working directory at runtime**, which varies depending on how Sherly is launched (`python src/sherly/main.py` from project root vs. a desktop shortcut). The Phase C feedback loop will silently write to different locations on different launches.

**Fix**: Resolve the path relative to the module file:
```python
import pathlib
FEEDBACK_FILE = pathlib.Path(__file__).parent.parent / "logs" / "feedback_log.jsonl"
FEEDBACK_FILE.parent.mkdir(parents=True, exist_ok=True)
```

---

### RC-7 · No Test Coverage for Core Security Modules

**File**: `tests/`
**Severity**: Medium (Reliability)

The `tests/` directory covers `action_manager`, `input_validator`, `runtime_utils`, and `model_manager` failures. The following modules have **zero test coverage** despite being security-critical:

- `core/safety_guard.py` — command classifier
- `core/sandbox.py` — subprocess isolation
- `core/sanitizer.py` — secret redaction
- `core/p2p_sync.py` — encrypted sync

**Fix**: Add `test_safety_guard.py` with parametrized tests for all `_DANGEROUS_PATTERNS` and `_CONFIRM_PATTERNS`. Add `test_sanitizer.py` with entropy-edge-case inputs. Target minimum 60% line coverage on all `core/` modules.

---

### RC-8 · `stream_model()` Not Wired to UI

**File**: `src/sherly/services/model_manager.py` (line 287), `src/sherly/ui/window.py`
**Severity**: Medium (UX / Feature Completeness)

`stream_model()` is a fully functional generator that yields token chunks from Ollama's streaming API. However, the UI (`window.py`) only calls `ask_model()` (blocking, full response) and renders the entire reply at once. The streaming infrastructure is dead code in production.

**Fix**: Emit a Qt signal (e.g., `token_received = Signal(str)`) from the worker thread. Connect it to a `QTextEdit.insertPlainText()` slot. Replace the blocking `ask_model()` call in the UI worker with `stream_model()` + signal emission per chunk.

---

### RC-9 · Ghost Mode Port Not Configurable

**File**: `src/sherly/core/ghost_mode.py`
**Severity**: Low (Operability)

The Ghost Mode socket server is hardcoded to port `5555`. If another service is bound to that port, Sherly silently fails to start in Ghost Mode with no actionable error message.

**Fix**: Read the port from `config.json` (`ghost_mode_port`, default `5555`). Wrap the `bind()` call in a try/except and surface a clear error: "Ghost Mode failed: port 5555 is in use. Set `ghost_mode_port` in config.json to use a different port."

---

## OPTIONAL ENHANCEMENTS

Nice-to-have improvements that increase polish, usability, or future flexibility.

---

### OE-1 · Add `--headless` CLI Flag to `main.py`

Currently Ghost Mode requires running a separate script. Add an argparse `--headless` flag to `main.py` that skips Qt initialization and starts only the socket server. This simplifies Docker deployments and CI-driven automation.

---

### OE-2 · Pre-Commit Hook Configuration

Add a `.pre-commit-config.yaml`:
```yaml
repos:
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.4.0
    hooks: [{id: ruff, args: [--fix]}]
  - repo: https://github.com/PyCQA/bandit
    rev: 1.7.8
    hooks: [{id: bandit, args: [-r, src/]}]
```
Prevents style violations and high-severity security findings (hardcoded secrets, `shell=True` usage) from entering `main`.

---

### OE-3 · Conversation History Side Panel

Add a collapsible `QDockWidget` to `window.py` that renders the rolling conversation history from `conversation_memory.py`. Include timestamps and per-entry action badges (↩ undoable, 🔒 locked, ✅ executed). Useful for reviewing what Sherly actually did during a long session.

---

### OE-4 · Plugin Marketplace Stub

Add a `GET https://sherly-plugins.example.com/registry.json` fetch in `plugin_manager.py` (opt-in, disabled by default) that returns a list of community plugins with names, descriptions, and install commands. This lays the groundwork for a future plugin ecosystem without requiring it now.

---

### OE-5 · `ruff` Linting in CI

The CI pipeline (`main.yml`) only runs `pytest`. Add a `lint` job:
```yaml
- name: Lint with ruff
  run: |
    pip install ruff
    ruff check src/ tests/
```
This surfaces style and complexity issues before they reach review, reducing PR cycle time.

---

### OE-6 · Dependabot for `pip`

Add `.github/dependabot.yml`:
```yaml
version: 2
updates:
  - package-ecosystem: pip
    directory: "/"
    schedule:
      interval: weekly
    open-pull-requests-limit: 5
```
Keeps dependencies up to date without manual auditing, and auto-creates PRs for security patches.

---

### OE-7 · Accessibility Theme

Add an `--accessibility` launch flag that applies a high-contrast QSS stylesheet (white background, black text, ≥4.5:1 contrast ratio). Store the preference in `config.json` under `"theme": "accessibility"`. Required for enterprise or regulated-environment adoption.

---

### OE-8 · Expand `.env.example`

The current `.env.example` documents only 2 of the 7+ environment variables Sherly reads. Add:

```ini
OPENAI_API_KEY=sk-...
GEMINI_API_KEY=AIzaSy...
GROQ_API_KEY=gsk_...
SHERLY_PHASE=A                    # A, B, or C
OLLAMA_BASE_URL=http://localhost:11434
CHROMA_HOST=localhost
CHROMA_PORT=8000
```

---

### OE-9 · Incremental RAG Indexing

Cache file `mtime` values in a SQLite table after `index_project()` completes. On subsequent calls, only re-index files whose `mtime` has changed. Reduces re-indexing time from O(project_size) to O(changed_files) — typically a 90%+ reduction for projects already indexed.

---

### OE-10 · Pyinstaller Release Workflow

Add `.github/workflows/release.yml` triggered on `v*.*.*` tags:
1. Runs `pytest` (fail fast).
2. Builds a `pyinstaller --onefile` executable.
3. Attaches Windows `.exe` and macOS `.app` to the GitHub Release.

Eliminates the "install Python first" onboarding friction for non-developer users.

---

*Last updated: April 2026. Reassess priorities monthly against Phase C feedback data.*
