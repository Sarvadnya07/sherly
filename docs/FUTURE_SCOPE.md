# Future Scope & Strategic Roadmap — Sherly AI

This document defines the concrete, prioritized development path for Sherly AI beyond its current v1.0 foundation. Items marked **[INFRA]** have partial infrastructure in place. Items marked **[NET NEW]** require greenfield work.

---

## Short-Term Improvements (0–3 Months)

### 1. Async I/O for LLM Calls `[NET NEW]`
**Problem**: The current `model_manager.py` uses synchronous `requests` wrapped in `ThreadPoolExecutor`. Under load, this creates thread contention and can delay the task queue.
**Fix**: Migrate to `httpx.AsyncClient` and expose an `async ask_model()`. Update `command_router.py` to run in an `asyncio` event loop. Expected latency improvement: ~20–30% under concurrent load.

### 2. Config Class with In-Memory Caching `[NET NEW]`
**Problem**: `config_manager.py` reads `config.json` from disk on every call (`load_config()` is called at the top of every getter). This is a silent performance bottleneck.
**Fix**: Introduce a singleton `Config` class using `functools.lru_cache` or a simple module-level cache with a dirty flag. Invalidate on `save_config()`.

### 3. Dependency Lockfile via `pip-compile` `[NET NEW]`
**Problem**: `requirements.txt` is hand-maintained and can diverge from `pyproject.toml`. The CI installs from `pyproject.toml` directly, which can produce non-reproducible builds.
**Fix**: Adopt `pip-tools`. Run `pip-compile pyproject.toml` to generate a locked `requirements.txt`. Pin this in CI.

### 4. Real Windows Hello Biometric Bridge `[INFRA — biometrics.py exists as POC]`
**Problem**: `core/biometrics.py` is a handshake simulation. Dangerous-level commands currently only prompt a text confirmation.
**Fix**: Implement the actual WinRT `UserConsentVerifier` API via `pywin32` or `winsdk`. Fall back gracefully to a PIN dialog on unsupported hardware. This unblocks the full "Biometric Approval" USP.

### 5. Expanded `.env.example` `[NET NEW]`
**Problem**: The current `.env.example` only exposes two keys. `GROQ_API_KEY`, `SHERLY_PHASE`, `CHROMA_HOST`, `CHROMA_PORT`, and `OLLAMA_BASE_URL` are all configurable but undocumented.
**Fix**: Add all recognized environment variables with comments to `.env.example`.

---

## Mid-Term Enhancements (3–9 Months)

### 6. Full Undo Coverage for Shell Commands `[INFRA — write/delete covered]`
**Problem**: The undo engine (`action_manager.py`) only reverses `write_file` and `delete_file`. Terminal commands executed via `safe_exec` are logged as non-undoable.
**Fix**: For whitelisted, reversible commands (e.g., `mkdir`, `mv`, `cp`), capture the inverse command at execution time and store it as `undo_data`. Implement `_undo_shell_command()` to replay it.

### 7. Async Plugin Execution `[INFRA — plugin_manager.py exists]`
**Problem**: Plugins run synchronously inside `route_command()`, blocking the response pipeline for slow plugins.
**Fix**: Route plugin calls through `task_queue.add_task()` with an `on_done` callback that pushes the result to the UI. Add a plugin execution timeout (configurable per-plugin in `config.json`).

### 8. Ollama Health Check & Auto-Recovery `[NET NEW]`
**Problem**: If Ollama is not running or becomes unresponsive, the circuit breaker opens but the error message ("Sorry, I ran into an error") gives no diagnostic context.
**Fix**: Add a pre-call `GET http://localhost:11434/api/tags` health check. If it fails, surface a specific "Ollama is not running — please start it with `ollama serve`" message. Attempt one auto-recovery by spawning `ollama serve` in the background.

### 9. Structured Logging with `structlog` `[NET NEW]`
**Problem**: All logging is done via a custom `log()` wrapper (`utils/runtime_utils.py`). This produces plaintext logs that are difficult to parse, filter, or pipe to observability tools.
**Fix**: Replace the `log()` function with `structlog` configured for JSON output. Add `level`, `module`, `timestamp` (UTC), and `correlation_id` fields to every log entry. Rotate at 10MB, keep 5 files.

### 10. Model Auto-Selection Based on Hardware `[INFRA — _get_optimal_local_model() exists]`
**Problem**: `_get_optimal_local_model()` exists in `model_manager.py` but is never called during startup. Users with 4GB RAM will silently try to load `phi3` and fail.
**Fix**: Wire `_get_optimal_local_model()` into `main.py` startup. Display a pre-flight model recommendation ("Your system has 8GB RAM — using Phi3. For better results, upgrade to 16GB to use Llama3:8B.").

---

## Long-Term Vision (9 Months – 2 Years)

### 11. WebAssembly (Wasm) Sandbox as Docker Alternative `[INFRA — wasm_sandbox.py exists]`
Execute user code inside a WASI-compliant Wasm runtime (e.g., Wasmtime) as a lightweight, cross-platform alternative to Docker. This removes the Docker Desktop requirement on macOS/Linux and reduces sandbox overhead from ~300ms to ~10ms.

### 12. Federated Knowledge Sharing with Differential Privacy `[INFRA — federated.py exists]`
Allow users to opt into sharing "self-healing" session fragments (anonymized) across a mesh of Sherly instances. Aggregate successful fix patterns without exposing private code. Implemented as a differential privacy layer over the `MemoryRAG` snapshot format.

### 13. LSP Integration (Language Server Protocol) `[NET NEW]`
Instead of relying on screenshot analysis for code understanding, connect Sherly to the active editor's LSP server (via `python-lsp-server` or VS Code's Language API). This enables precise diagnostic-aware patching: Sherly would receive typed error codes, cursor position, and symbol tables rather than inferred OCR text.

### 14. Sherly Cloud Relay (Optional, Self-Hosted) `[NET NEW]`
For users who want to control their development environment from a mobile device or across firewalls, provide a self-hostable relay server (FastAPI + WebSocket) that bridges the mobile client to the local Sherly daemon. End-to-end encrypted; no payload is stored on the relay.

### 15. Multi-User Session Support `[NET NEW]`
The router currently maintains a single global `LAST_INTERACTION` dict and mode flag, making multi-user use impossible. Introduce session tokens, per-session state isolation (mode, phase, pending actions), and a session manager with TTL-based cleanup.

---

## Scalability Improvements

### 16. PostgreSQL + ChromaDB Server Mode `[INFRA — config hooks exist]`
The `config.json` already contains `db_config.provider` and `chroma_config.mode` stubs. Implement the actual migration path:
- Replace SQLite `conn` in `services/memory.py` with a `SQLAlchemy` engine.
- Point ChromaDB to a remote `chromadb` server instance.
- Document the migration guide in `docs/`.

### 17. Horizontal LLM Inference Offloading `[INFRA — remote_api.py exists]`
The `core/remote_api.py` stub defines a remote inference endpoint. Build this into a FastAPI microservice that Sherly discovers via the P2P mesh. Allows "Compute Nodes" on a local network (e.g., a desktop GPU machine) to serve inference to "Control Nodes" (e.g., a laptop).

### 18. Distributed Task Queue with Redis `[NET NEW]`
Replace the single-threaded `Queue` in `core/task_queue.py` with a `Celery`+`Redis` backed queue for multi-worker environments. This is required for multi-user deployments and parallel agent execution.

---

## Security Upgrades

### 19. Sandbox Escape Detection `[NET NEW]`
Implement a post-execution diff of the filesystem outside `self.temp_dir` after each sandbox run. If any file outside the designated workspace was modified, raise a `SecurityError`, log the violation, and quarantine the plugin/command that triggered it.

### 20. Rate Limiting on LLM Calls `[NET NEW]`
Add a per-minute call rate limiter to `model_manager.py` to prevent accidental API cost explosions (e.g., from a looping self-healing cycle). Configurable via `config.json`. Alert the user when the threshold is approaching.

### 21. Secret Rotation Detection `[NET NEW]`
Extend `core/sanitizer.py` to detect API keys that match known provider formats (e.g., `sk-...` for OpenAI, `AIzaSy...` for Gemini) in addition to entropy-based detection. Add an active warning when a detected key is found in a log file that would be committed to Git.

---

## Performance Optimizations

### 22. Streaming LLM Responses to UI `[INFRA — stream_model() exists]`
`stream_model()` is implemented in `model_manager.py` but the UI renders responses only on full completion. Wire the `QTextEdit` in `window.py` to a signal that appends chunks as they arrive, eliminating the perceived latency gap.

### 23. RAG Incremental Indexing `[NET NEW]`
The current `index_project()` re-indexes all files on every call. Implement a file modification timestamp cache (persisted in SQLite). On subsequent calls, only index files whose `mtime` has changed. Expected 90%+ reduction in re-indexing time for large projects.

### 24. Lazy Module Imports `[NET NEW]`
Several heavy imports (`playwright`, `chromadb`, `faster_whisper`) are at the module level, increasing cold-start time. Move these behind `importlib.import_module()` guarded by first-use flags to reduce startup from ~4s to under 1s.

---

## AI / Automation Opportunities

### 25. Automated Prompt Tuning via RLHF `[INFRA — optimizer.py exists, Phase C data collection active]`
Phase C already collects y/n feedback in `feedback_log.jsonl`. Build a scheduled job that:
1. Loads successful (y-rated) and failed (n-rated) exchanges.
2. Fine-tunes the system prompt template using a local Alpaca/PEFT adapter.
3. A/B tests the new prompt against the baseline over a 100-query window.
4. Promotes the winner automatically.

### 26. AST-Aware Code Patching (Beyond Line-Diffs) `[INFRA — ast_tools.py exists]`
Extend `tools/ast_tools.py` from basic AST analysis to full transformation: parse the file into an AST, identify the target node (function, class, expression), apply the LLM-suggested change at the AST level, and unparse back to source. Eliminates whitespace-sensitive diff errors.

### 27. Synthetic Training Data Export `[INFRA — data_gen.py exists]`
Formalize the `core/data_gen.py` export format to match the Alpaca dataset schema (`instruction`, `input`, `output`). Add a UI command: `"export training data"` → generates a `sherly_training_data.jsonl` from all Phase C session logs ready for local fine-tuning.

---

## UI/UX Improvements

### 28. Real-Time Streaming Output `[see #22]`
Replace the "loading spinner → full response dump" pattern with a word-by-word streaming render, matching the interaction pattern users expect from modern AI assistants.

### 29. Conversation History Panel `[NET NEW]`
Add a collapsible side panel to `window.py` that shows the full conversation history (scrollable, searchable) with timestamps and action badges (↩ undoable, 🔒 locked).

### 30. Accessibility: High-Contrast & Screen Reader Support `[NET NEW]`
Add a `--accessibility` launch flag that applies a high-contrast QSS theme and enables Qt accessibility hints for screen reader compatibility. Critical for enterprise or regulated-environment adoption.

---

## DevOps / CI-CD Ideas

### 31. Code Coverage Reporting `[NET NEW]`
Add `pytest-cov` to the CI pipeline. Set a minimum coverage threshold of **60%** (current baseline) with a target of **80%** over six months. Publish coverage reports to the repository's GitHub Pages.

### 32. Pre-Commit Hooks `[NET NEW]`
Add a `.pre-commit-config.yaml` with `ruff` (lint), `black` (format), and `bandit` (security scan) hooks. Prevents style violations and obvious security issues from entering the repository.

### 33. Automated Release Packaging `[NET NEW]`
Add a GitHub Actions workflow triggered on `tag: v*.*.*` that:
1. Runs the full test suite.
2. Builds a `pyinstaller` single-file executable for Windows (`.exe`) and macOS (`.app`).
3. Uploads the artifacts to the GitHub Release.

### 34. Dependabot Configuration `[NET NEW]`
Enable GitHub Dependabot for `pip` to automatically open PRs when dependencies in `pyproject.toml` have security patches or minor version updates.

---

*This roadmap is a living document. Items are intentionally specific and implementation-ready — not vague aspirations. Review and reprioritize monthly based on user feedback collected through Phase C rating data.*
