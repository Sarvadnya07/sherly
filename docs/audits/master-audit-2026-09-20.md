# SHERLY — MASTER REPOSITORY AUDIT

**Date:** 2026-09-20
**Branch / HEAD:** `fix/execution-guard-hardening` @ `a300cdb`
**Scope:** full repository, 47-phase master prompt (baseline → verdict)
**Mode:** AUDIT ONLY — no code was modified
**Artifact:** consolidated. The prompt enumerated 29 deliverable files; the repository already
carries 30 docs plus 20 files in `docs/audits/` with contradicting numbers (finding DOC-005).
Producing 29 more fragments would have amplified the defect being reported, so the deliverables
are consolidated here. Ask and this can be split.

**Baseline note (delivery, 2026-09-20).** The audit was performed against the checked-out working tree
at `a300cdb`, which is 24 commits behind the delivery-time `origin/main` (`052b1ce`). Every
load-bearing finding was therefore re-checked against `origin/main` before delivery, using
`git show origin/main:<path>` — PKG-001 (`pyproject.toml` still declares only `packages`, no
`py-modules`), SEC-001 (`agents/playwright_agent.py:115-130` still takes `starting_url` from model
output and calls `page.goto` unvalidated), SEC-002 (no `intent_router` callers), SEC-003 (identical
`run_project` call sites), SEC-004 (`@router.post("/undo")` still parameterless; `remote_agent/agent.py`
still has no `Depends`/`verify_key`), SEC-008 (`workspace_root = Path.cwd().resolve()`), SEC-009
(`screen.capture` still `risk=ToolRisk.SAFE`), CODE-001 (unchanged `ruff check` directory list),
CODE-002 (`-r src/` still present), CODE-003 (0 `mypy` occurrences in `ci.yml`), CODE-009
(`requires_approval` still written 6× and read 0×), and DOC-001 (`README.md` badge 120, body 117).
Main has since hardened `files.py` traversal and declared `python-multipart` independently; neither
alters a finding.

**Revision 2 — adversarial re-verification performed 2026-09-20.** Every load-bearing claim was
independently challenged against the code. Corrections are marked `[R2]`. Two original claims were
**wrong** (SEC-001's "no exploit found"; SEC-004's mitigation claim), one was **overstated**
(CODE-001's materiality), and four findings were added by the re-verification itself (SEC-007,
SEC-008, SEC-009, CODE-009). See §15 for the full confirm / correct / unconfirmed ledger.

---

## 1. EXECUTIVE VERDICT

**Sherly is a real, working, local-first desktop AI developer workspace with a genuinely strong
security spine — wrapped in documentation and release engineering that materially overstate how
much of the system is verified.**

Verified-working: chat → router → model → tools, the whitelist + `safety_guard` + `shlex`/`shell=False`
execution sandbox, the preview → diff → approve → apply → undo pipeline (with pre-write conflict
detection), atomic config migration, structured redacted JSON logging, and a FastAPI + React surface
whose TypeScript types match backend schemas.

Not true, despite being documented: an SSRF/DNS-rebinding firewall validating "all user/model-controlled
URLs" (the module has zero production callers — **`[R2]` and a live unvalidated LLM-chosen navigation
path exists in its place**, see SEC-001), "zero-trust" as a whole-system property (policy is
path-dependent, and the key-protected remote front door sits in front of an unauthenticated local
command endpoint — SEC-004), cross-platform support (the project's own certification file says
macOS/Linux `NOT_TESTED`), the published latency/throughput benchmarks (no benchmark harness exists in
the repo), and the test counts (README badge says 120, README body says 117, the release certificate
says 109, the suite actually collects 124 — with 122 passing and 2 warnings, not the "0 warnings"
claimed).

The single most dangerous unresolved issue is **Q-D (below): all approval, confirmation, preview and
undo state is process-global** — one shared queue for every client the product claims to serve.

**No P0 (catastrophic / remotely reachable) issue was found — `[R2]` and that verdict survives the
re-verification, but the reasoning behind it is narrower than originally written.** Re-checked
adversarially: every listening socket is loopback-only (`backend/main.py`: `uvicorn.run(...,
host="127.0.0.1")`; `remote_api` documented on `127.0.0.1:5000`), so nothing is reachable from off-host
without the user exposing it; and every subprocess site was re-read and traced (`tools/executor.py`,
`tools/terminal_tools.py`, `tools/screen_tools.py`, `sherly_commands/system_commands.py`,
`scripts/package.py`, `sherly_ui/views/workspace_view.py`) — all use `shell=False` with constant or
policy-gated argv. The P0 verdict is explicitly conditional: it does **not** hold if Sherly is ever
bound to a non-loopback interface, or if the browser agent is ever driven without user initiation.
What the re-verification did change is the *local* attack surface, which is wider than §5 originally
said (SEC-001, SEC-004, SEC-007).

**Confidence: MEDIUM-HIGH for static structure and security paths** (every claim below is traceable
to file + symbol), **LOW for runtime/performance/platform behaviour** (no Ollama, no audio hardware,
no macOS/Linux runtime, no benchmark harness available in this environment).

---

## 2. BASELINE (Phase 0)

| Item | Value |
|---|---|
| Product | Sherly AI, version `2.0.0` (`pyproject.toml`, `backend/main.py`) |
| Runtime | Python ≥3.10 (CI: 3.13), Node 20 (CI) |
| Primary UI | React 18 + Vite + Zustand (`frontend/src`, 20 files) |
| Secondary UIs | Legacy PySide6 HUD (`sherly_ui/`), remote PWA (`remote_ui/`) |
| Backend | FastAPI, `127.0.0.1:8000`, WebSocket `/ws` |
| Model layer | Ollama HTTP + OpenAI/Gemini/Groq (hardcoded model IDs) |
| Storage | SQLite `sherly_memory.db` (WAL), JSON `memory.json`, in-memory dicts |
| Security layer | `safety_guard.py`, `tools/terminal_tools.py`, `input_validator.py`, `core/network_security.py` |
| Build/release | `scripts/package.py`, `.github/workflows/{ci,release}.yml` |
| Tests | 8 files, 87 test functions, **124 collected** |
| Working tree | clean; `venv/`, `backups/`, `logs/`, `uploads/`, `config.json`, `*.db` present but gitignored |

Present-but-ignored in the working directory: `venv/`, `backups/`, `config.json`, `config.json.bak`,
`sherly_memory.db{,-shm,-wal}`, `logs/`, `uploads/`, `scratch/`, `sherly_ai.egg-info/`,
`__pycache__/`, `.mypy_cache/`, `.pytest_cache/`, `.ruff_cache/`.
`git ls-files` contains **no** tracked secrets, `.env`, caches, or `.bak` files. Hygiene: clean.

---

## 3. DOCUMENTATION vs REALITY (Phases 1, 2, 24)

| Claim | Source | Reality | Status |
|---|---|---|---|
| "Tests-120 passing" badge | `README.md:15` | 124 collected | MISMATCH |
| "117 passing tests with 0 warnings" | `README.md:405` | 124 collected; `pvporcupine`-dependent tests error without the lib | MISMATCH |
| "109/109 PyTest tests passed" | `docs/audits/v2.0.0-release-certification.md` | 124 collected | STALE |
| "Measured Result: 4.2ms / 6.8ms / 14,184 ops/sec / 18ms / 142ms" | `README.md:252-261`, `docs/PERFORMANCE.md:20-30` | No benchmark harness, script, or committed result exists (`grep benchmark|timeit|perf_counter` → only prose) | UNVERIFIABLE — treat as UNSUPPORTED CLAIM |
| "SSRF & DNS-Rebinding Protection: validates all user/model-controlled URLs… re-validates every redirect" | `docs/PERFORMANCE.md:12`, `README.md:208` | `core/network_security.py` has **no production caller** (only `tests/test_security.py:338,484`) `[R2]` and an unvalidated LLM-chosen navigation path exists instead (`agents/playwright_agent.py`) | **UNIMPLEMENTED CLAIM + LIVE GAP** — see SEC-001 |
| "zero-trust execution model" | `README.md:215` | true for `safe_exec` paths; `run_project`, `_run_system_command`, `system_commands` do not pass the policy layer | PARTIALLY TRUE — path-dependent |
| "Cross-platform" | `README.md` install sections for Windows/macOS/Linux | `release/release_manifest.json` `platform_certification`: `windows: RUNTIME_VERIFIED`, `macos: NOT_TESTED`, `linux: NOT_TESTED`; `release.yml` only *builds* | DOCUMENTED ONLY for macOS/Linux |
| "mypy backend sherly_core tools agents" as verification | `README.md:423` | mypy is a dev extra (`pyproject.toml:53`), has no config, and is not in `ci.yml` | UNENFORCED CLAIM |
| "Atomic Backups & Undo … instant rollback" | `README.md:48` | true, but undo history is a **global deque capped at 5** (`action_manager.py:_MAX_HISTORY`) | PARTIALLY TRUE |
| "Zero Unresolved P0/P1 Security Blockers… certified for GA" | `docs/audits/v2.0.0-release-certification.md` | certification predates `fix/execution-guard-hardening`; lint gate still excludes root modules; SSRF claim unwired | SUPERSEDED / OVERSTATED |

Documentation sprawl: `docs/` holds 30 documents plus 20 `docs/audits/` phase reports, several
mutually contradictory (project counts, platform status, blocker counts). The same is true of
`README.md` internally (120 vs 117).

---

## 4. ARCHITECTURE & DUPLICATION (Phases 4, 8, 12, 29)

Real dependency direction is **subpackages → flat root modules**, not the reverse:

```
backend/ tools/ agents/ core/ sherly_core/ remote_api/
        │  (10 distinct root-module imports: model_manager, runtime_utils, action_manager,
        ▼   safety_guard, text_to_speech, web_search, memory, config_manager, input_validator)
command_router.py · action_manager.py · safety_guard.py · model_manager.py · input_validator.py
memory.py · memory_brain.py · conversation_memory.py · config_manager.py · runtime_utils.py …
```

All load-bearing business logic lives as top-level single files; every package depends on them.

**DUPLICATE IMPLEMENTATION — same concern, multiple live or shipped implementations:**

| Concern | Implementations | Canonical | Status |
|---|---|---|---|
| Circuit breaker | `model_manager.py` (`pybreaker` or local stub), `sherly_core/providers.py:43`, `sherly_core/resilience.py:26` | `model_manager` (only live one) | 2 dead |
| LLM providers | `model_manager.ask_*` (live), `sherly_core/providers.py` `BaseLLMProvider` + 4 providers (~450 LOC) | `model_manager` | providers.py referenced **only by `tests/test_model_providers.py`** |
| Task queue | `core/task_queue.py` (thread `SherlyTaskQueue`), `runtime_utils.py` (thread `SherlyTaskQueue`) | ambiguous | both live, same thread name |
| Memory | `memory.py` (SQLite), `memory_brain.py` (JSON `memory.json`), `conversation_memory.py` (in-proc) | 3-way split, all live | no single owner |
| System commands | `command_router._run_system_command` (live), `sherly_commands/system_commands.py` (dead) | `command_router` | duplicate |
| TTS | `text_to_speech.py` (real), `sherly_core/text_to_speech.py` (re-export shim) | `text_to_speech.py` | intentional adapter — OK |
| Rollback/write | `tools/preview.apply_preview` (own backup + 3-tuple undo), `action_manager.write_file_safe` (4-tuple undo) | neither | divergent formats (CODE-006) |
| Resilience | `sherly_core/resilience.py` | — | **0 callers anywhere, including tests** |

**DEAD / DISCONNECTED (Phase 31):**
- `sherly_core/resilience.py` — zero imports repo-wide.
- `sherly_core/providers.py` — test-only.
- `sherly_core/intent_router.py` → `sherly_commands/system_commands.py` — `intent_router` is imported by nothing; it is the sole consumer of `sherly_commands`.
- `tools/task_engine.py` — reached only from `command_router.py:48,640`.
- `sherly_ui/` (legacy PySide6) — reachable only from the legacy `main.py` entry point; `sherly_ai/` — bundled package with no production consumer.
- `README.md:353` documents `uvicorn remote_api.server:app --port 5000`; `remote_api` is not in `[tool.setuptools] packages`.

---

## 5. SECURITY (Phases 7, 28, 46 C/D/E/I)

**Verified strong.** `safe_exec` (`tools/terminal_tools.py:100`) enforces, in order: chaining-operator
rejection → prefix whitelist → `safety_guard.check_command` three-tier classification → `shlex.split`
→ `subprocess.run(..., shell=False)` with a 30 s timeout. AST-level regression tests assert
`shell=True` never appears (`tests/test_security.py:229-248,447-473`). No `os.system`, `eval`, or
`exec` on user input exists. `input_validator` guards injection. `remote_api` uses
`secrets.compare_digest` and fails closed when `SHERLY_REMOTE_API_KEY` is unset
(`remote_api/server.py:37-43`), bounds uploads to 10 MB, and strips traversal via `Path(...).name`.
`observability.redact_secrets` redacts both key names and provider token patterns. Logging is
structured JSON with correlation IDs; timelines are **bounded at 100** (no leak).

**Findings:**

- **SEC-001 (P1) `[R2]` CORRECTED — this claim was wrong as originally written.** I previously wrote
  that "no exploit results, because every live outbound call targets a constant." That is true for
  `model_manager.py` and `web_search.py`, but **false for the browser agent**, which I had not read
  during the first pass. `agents/playwright_agent.py:run()` takes the starting URL straight from model
  output — `ask_model(_URL_PROMPT...)` → `starting_url = url_tokens[0]` → `page.goto(starting_url,
  timeout=15000)` — with **no call to `core/network_security.py`** (or any other validation). It then
  injects JS to enumerate interactive elements, feeds that page text back into the model, and executes
  the model's returned `CLICK` / `TYPE` / `SCROLL` actions against the live page for up to 10 steps with
  a **headful Chromium** (`p.chromium.launch(headless=False)`).

  Reachability is production, not test-only: `agent_manager.py:76` → `browser_agent.run(text, ask_model)`
  → `agents/browser_agent.py` routes `action == "autonomous_pilot"` → `playwright_agent.run(...)`.
  `input_validator._is_injection()` is a **literal-phrase blacklist applied only to user-typed text**
  (`ignore previous instructions`, `jailbreak`, …); untrusted content arriving from web pages, files or
  search results is not screened at all, and it is exactly that content which is re-injected into the
  model in the playwright loop.

  Concrete consequences: the agent can be steered to internal-only targets — including Sherly's own
  **unauthenticated local API on `127.0.0.1:8000`**, where it can autonomously click "approve"; and to
  link-local metadata addresses (`169.254.169.254`). This is the same class of exposure the dead module
  was written to prevent, in the one place it is not applied.

  Why this is P1 and not P0: triggering it requires either the user to run an autonomous-pilot browsing
  task or an attacker-controlled page to be the one the agent is already browsing; it is not a service an
  off-host attacker can call. It becomes P0 if the browser agent is ever reachable without explicit user
  initiation (unattended job, exposed remote agent). **Recommended direction:** route the navigation
  through `core/network_security.py` and add an origin/allowlist check on `CLICK`/`TYPE` — or stop
  advertising the firewall until it is wired in.
- **SEC-002 (P2)** — Dead chain `intent_router` → `system_commands.py:38` contains
  `subprocess.run(["shutdown", "/s", "/t", "1"])` with **no policy check**. Unreachable today;
  `shutdown` is in `safety_guard._DANGEROUS_PATTERNS`, so re-wiring it without gating would be a
  regression waiting to happen.
- **SEC-003 (P2)** — Policy is path-dependent. `run_project` (`tools/executor.py:6`) applies neither
  whitelist nor guard, and is called from the auto-rerun loop (`command_router.py:438`) and
  `fix_project.py:31`. `command_router._run_system_command` runs `os.startfile` / `Popen` / `rundll32`
  with no policy check. **Checked for exploitability: not exploitable** — `detect_project()`
  (`tools/project_detector.py`) returns only fixed literals (`"python main.py"`, `"npm start"`,
  `"python manage.py runserver"`) and `COMMAND_MAP` argv is hardcoded. Reported because the
  invariant "every state-changing operation passes policy" is false.
- **SEC-004 (MEDIUM) `[R2]` CORRECTED — originally rated P2 with overstated mitigations.** The original
  text implied every dangerous endpoint requires knowing an 8-char action ID. That is true for
  `/approvals/{id}/approve` and `/approvals/{id}/reject`, but **`POST /api/actions/undo` takes no
  parameters at all** (`backend/api/routes/actions.py`): the route is `def undo_last_action():` →
  `action_manager.undo_last()`. It is a zero-knowledge, zero-precondition, state-changing request, and
  it needs no custom headers, so it is a **CORS-simple** POST that any web page the user visits can fire
  at `127.0.0.1:8000` — reverting the user's most recent file modification with no CSRF token, no Origin
  check and no authentication. `/previews/{id}/apply` is also simple-POST but does require the ID.

  The second, larger part of this finding is the **inconsistent door policy**: `remote_api/server.py`
  requires `SHERLY_REMOTE_API_KEY` with `secrets.compare_digest` and fails closed, then proxies to
  `LOCAL_AGENT_URL` defaulting to `http://127.0.0.1:5001/execute` — and `remote_agent/agent.py`'s
  `POST /execute` has **no authentication whatsoever**, calling `route_command(cmd.text)` and returning
  its output. The key protects the remote transport, not the local command endpoint behind it. Any local
  process (a sandboxed app, another user session, or anything already running as a different principal)
  can drive the full router — including `approve <id>`, `run project`, plugin dispatch and browser
  automation. JSON-bodied routes like `/execute` are protected from browser CSRF by preflight, which is
  why this is bounded; the `/api/actions/undo` case above is not.

  **Recommended direction:** a loopback token (or Origin/`Sec-Fetch-Site` check) on both `backend` and
  `remote_agent`, and require confirmation for `/undo`.
- **SEC-005 (P3)** — `remote_api` uploads silently overwrite a same-named file in `uploads/`; no
  `O_EXCL`, no rename, no collision feedback.
- **SEC-006 (P3)** — `safety_guard._pending_confirmation` is a single global dict, and
  `handle_confirmation_reply` accepts `yes` / `ok` / `y` from any caller. A stray "yes" can confirm a
  command queued by a different surface.
- **Supply chain (informational, positive)** — Actions are pinned to major tags (`@v4`, `@v5`) with
  `permissions: contents: read`; no third-party actions beyond first-party plus `ruff-pre-commit` and
  `bandit`; Dependabot is configured.

---

## 6. STATE / MEMORY / CONCURRENCY (Phases 9, 21)

Every piece of interactive state is a **module-level singleton**, i.e. single-tenant by construction:

| State | Location | Scope | Bounded |
|---|---|---|---|
| Pending approvals | `action_manager._pending_actions` | process-global | TTL 120 s |
| Confirmation slot | `safety_guard._pending_confirmation` | process-global, **single slot** | TTL-less |
| Previews | `tools/preview.preview_store` | process-global | max 5 |
| Undo history | `action_manager._action_history` | process-global | maxlen 5 |
| Chat context | `memory.py` SQLite | process-global, **not keyed by session** | 5 rows |
| Brain memory | `memory_brain.MEMORY_FILE` (`memory.json`) | process-global | unbounded |
| Conversation turns | `conversation_memory._sessions` | **session-keyed (only component that is)** | 5 turns |
| Timelines | `observability._timelines` | process-global | max 100 |

`conversation_memory` proves the codebase already knows how to key state by `session_id`; the
approval and undo systems simply never adopted it.

---

## 7. CI / RELEASE / PACKAGING (Phases 16, 17, 18)

- `.github/workflows/ci.yml` triggers on `push`/`pull_request` **to `main` only** — so the commits on
  this branch never ran it.
- The CI lint step enumerates
  `backend core sherly_core sherly_ai sherly_commands agents tools remote_api remote_agent tests`
  and **omits every root module** — including `safety_guard.py`, `action_manager.py`,
  `command_router.py`, and `input_validator.py` (CODE-001). `compileall -q .` still catches syntax.
  **`[R2]` materiality measured, and it is smaller than first implied:** running the exact CI rule set
  (`ruff check --select E4,E7,E9,F`) over all 18 excluded root modules yields **exactly one** finding —
  `E731` at `text_to_speech.py:51` (`mark_speaking = lambda _: None`), a style nit, not a bug. So the
  gap is real but is **not currently concealing defects**; the risk is forward-looking (root modules are
  where the policy layer lives and are edited often). Corroborating evidence that the omission is an
  oversight rather than a deliberate scope: `pyproject.toml` declares a per-file `E402` ignore for
  `"main.py"` — a root module CI never lints.
- Ruff config is real and green (`pyproject.toml:65-80`, `select = ["E4","E7","E9","F"]` with
  per-file `E402` ignores for sys.path-bootstrapping entry points).
- **Pre-commit bandit is still a no-op (CODE-002):** `files:` was corrected to the real layout, but
  `args: [-r, src/]` still points at a directory that does not exist.
- `pyproject.toml:57` — `packages = ["agents","backend","core","sherly_ai","sherly_commands","sherly_core","sherly_ui","tools"]`
  declares **no `py-modules`**, so `pip install .` installs an interpreter in which every one of those
  packages fails to import (they import the 10 root modules listed in §4). `remote_api`,
  `remote_agent`, `remote_ui`, `plugins` and all package data are also absent (PKG-001).
- `release.yml` runs pytest + `npm run build` + `scripts/package.py --verify` and uploads
  **only `release/release_manifest.json`** — no wheel, sdist, or installer (PKG-002). The broken
  packaging declaration is therefore never exercised by any pipeline.
- `scripts/package.py` hardcodes `"version": "2.0.0"` (duplicating `pyproject.toml`) and accepts a
  `verify_only` parameter it never reads (CODE-007).
- Manifest drift already partially fixed: `python-multipart>=0.0.20` is now present in both
  `requirements.txt` and `pyproject.toml`.
- Two tests fail without the native `pvporcupine` library; CI installs it via `requirements.txt`, so
  they pass there but not in a sandbox (PKG-003 / TEST-002).

---

## 8. TESTING (Phase 15)

8 files / 87 test functions. `[R2]` Fresh full run: **124 collected, 122 passed, 2 failed, 2 warnings in
9.77s** (`python -m pytest tests/ -q`). The 2 failures are
`test_security.py::test_missing_pvporcupine_key_raises_runtime_error` and
`::test_pvporcupine_key_not_logged_in_wake_word_error` — both environment-only (native `pvporcupine`
absent here; CI installs it from `requirements.txt`).

Strong: `tests/test_security.py` (26 tests) covers allowlist bypass, chaining operators, path
traversal, and AST-level absence of `shell=True`; `test_safety_guard.py`, `test_api_contracts.py`,
`test_model_scanner.py`, `test_files_route_undo.py` (4 tests, the save→undo→delete round trip).

Missing coverage for properties the product advertises:

- **TEST-001 (P1)** — nothing asserts client/session isolation of approvals, previews, or undo —
  precisely the property §6 shows to be absent.
- **TEST-002 (P2)** — no test covers undo beyond 5 actions, cross-client confirmation, or the
  `pvporcupine`-dependent paths in an environment without hardware.
- **TEST-003 (P2)** — the SSRF module is tested in isolation but no test asserts that a production
  path uses it (which is why SEC-001 went unnoticed).
- No frontend unit tests exist; `tsc`-via-`npm run build` is the only frontend gate.

---

## 9. MASTER FINDINGS TABLE (Phase 40)

| ID | Sev | Category | Finding | Evidence | Fix | Effort |
|---|---|---|---|---|---|---|
| SEC-001 | P1 | Security | Documented SSRF firewall is dead code **and** the browser agent navigates to an unvalidated model-supplied URL, then drives the page | `core/network_security.py` callers = tests only; `agents/playwright_agent.py:run` → `page.goto(starting_url)`; `agent_manager.py:76` | Validate navigation through `core/network_security.py` + origin-check CLICK/TYPE, or retract the claim | M |
| ARCH-001 | P1 | Architecture | Approval / confirmation / preview / undo state is process-global → no client isolation | `action_manager.py`, `safety_guard.py`, `tools/preview.py` module singletons; only `conversation_memory` is session-keyed | Thread a session identity through all four stores | M |
| CODE-001 | P2 | Quality gate | CI lint gate excludes all 18 root modules (incl. `safety_guard.py`, `command_router.py`); **only 1 current violation exists**, so it is forward-looking rather than concealment | `.github/workflows/ci.yml` ruff arg list; measured with `ruff check --select E4,E7,E9,F <root modules>` | Add root modules to the gate | S |
| PKG-001 | P1 | Packaging | No `py-modules`; root modules and `remote_*`/`plugins` omitted → `pip install .` yields an unimportable app | `pyproject.toml:57` + 10 cross-package root imports | Declare `py-modules` / restructure | M |
| DOC-001 | P1 | Documentation | Test count claims 120 / 117 / 109 vs 124 actual | `README.md:15,405`; cert doc | Single source of truth for the count | S |
| DOC-002 | P1 | Documentation | Precise latency/throughput figures published as measured; no harness exists | `README.md:252-261`; `docs/PERFORMANCE.md:20-30` | Add a benchmark script or label the table as targets | S |
| DOC-003 | P1 | Documentation | "Certified GA / zero P0-P1" while the above are open | `docs/audits/v2.0.0-release-certification.md` | Re-issue certification against this audit | S |
| TEST-001 | P1 | Testing | No test asserts multi-client isolation — the property that is missing | `tests/` has no session-scoped approval test | Add isolation tests with ARCH-001 | S |
| ARCH-002 | P1 | Architecture | Duplicated implementations of policy, resilience, providers, queues, memory | §4 table | Pick canonical per concern; delete or demote the rest | L |
| SEC-002 | P2 | Security (latent) | Ungated `shutdown /s /t 1` in dead `system_commands` chain | `sherly_commands/system_commands.py:38` | Delete dead chain | S |
| SEC-003 | P2 | Security (policy) | `run_project` / `_run_system_command` bypass the policy layer (inputs constant → not exploitable) | `tools/executor.py:6`; `command_router.py:438` | Route both through `safety_guard` | S |
| SEC-004 | MEDIUM | Security | No auth on the local API; `POST /api/actions/undo` is a zero-precondition CORS-simple state change; key-protected `remote_api` proxies to unauthenticated `remote_agent:/execute` | `backend/api/routes/actions.py`; `remote_api/server.py:37`; `remote_agent/agent.py` | Loopback token / Origin check on both; confirm `/undo` | S |
| SEC-005 | P2 | Security | Uploads silently overwrite same-named files | `remote_api/server.py:76` | Reject or rename collisions | S |
| SEC-006 | P2 | Security | Single global confirmation slot accepts `yes`/`ok` from any surface | `safety_guard.py:handle_confirmation_reply` | Bind confirmation to the requesting session | S |
| CODE-002 | P2 | Tooling | Pre-commit bandit scans nonexistent `src/` → no-op | `.pre-commit-config.yaml` args | Point `-r` at the real layout | S |
| CODE-003 | P2 | Tooling | mypy documented as verification; not configured, not in CI | `README.md:423`; `pyproject.toml:53` | Configure + add to CI, or remove the claim | S |
| CODE-004 | P2 | Duplication | Two task queues, both naming their thread `SherlyTaskQueue` | `core/task_queue.py:56`; `runtime_utils.py:73` | Keep one | S |
| TEST-002 | P2 | Testing | Undo depth, cross-client confirm, hardware paths untested | `tests/` | Add targeted coverage | M |
| DOC-004 | P2 | Documentation | "Cross-platform" vs certification `NOT_TESTED` for macOS/Linux | `release/release_manifest.json` | State platform status honestly | S |
| DOC-005 | P2 | Documentation | 50 doc + audit files with contradictory figures | `docs/**` | Consolidate; delete superseded phase reports | M |
| ARCH-003 | P2 | Dead code | `resilience.py`, `providers.py`, `intent_router.py`+`sherly_commands`, `sherly_ai`, `sherly_ui` shipped but unshipped-in-practice | §4 | Delete or explicitly deprecate | M |
| CODE-005 | P3 | Product | Undo history capped at 5, globally | `action_manager.py:_MAX_HISTORY` | Document or raise | S |
| CODE-006 | P3 | Consistency | Two write paths with divergent undo-data formats (3-tuple vs 4-tuple) | `tools/preview.py`; `action_manager.py` | Unify | S |
| CODE-007 | P3 | Quality | `scripts/package.py` hardcodes `2.0.0`; unused `verify_only` | `scripts/package.py` | Read from `pyproject` | S |
| PKG-002 | P3 | Release | Release pipeline publishes only a JSON manifest — no wheel/installer | `.github/workflows/release.yml` | Decide the distribution channel | M |
| PKG-003 | P3 | Environment | 2 tests need native `pvporcupine`; fail without it | `tests/test_security.py` | Mark/skip when unavailable | S |
| CODE-008 | P4 | Quality | 70+ `BLE001` broad-except sites, deliberately outside the gate | `pyproject.toml:70-72` | Burn down in hot modules only | L |
| SEC-007 | P2 | Security | `plugin_manager.load_plugins()` runs at import and `importlib.import_module()`s **every** `.py` in `plugins/` with no allowlist or integrity check; `_get_safe_target`'s root is `Path.cwd()`, so `plugins/` is inside the writable workspace → a file written through the workspace API executes on next import | `plugin_manager.py:13-32,73`; `backend/api/routes/files.py:59-67` | Allowlist plugin names / require an explicit install step | M |
| SEC-008 | P2 | Security | The workspace boundary is the **process CWD**, not a configured project root | `backend/api/routes/files.py:60` (`Path.cwd().resolve()`) | Anchor to a configured workspace root | S |
| SEC-009 | P2 | Privacy | `screen.capture` is registered `risk=SAFE, requires_approval=False`, so the tool loop auto-executes full-screen capture and returns it to the model — which may be a cloud provider | `tools/native_tools.py:143-152`; `tools/agent_tool_loop.py` | Mark screen capture CONFIRM | S |
| CODE-009 | P2 | Policy integrity | `ToolSpec.requires_approval`, `permissions`, `reversible` and `timeout` are declared and **read nowhere**; real enforcement is `risk` plus name-based special-casing in `evaluate_tool_policy` | `tools/capabilities.py:34-42`; `tools/policy_engine.py:56-79` | Enforce the declared metadata or delete it | M |

---

## 10. PHASE 46 — DIRECT ANSWERS

| # | Question | Answer |
|---|---|---|
| A | One canonical command execution path? | **No.** `safe_exec` is canonical, but `run_project` and `_run_system_command` bypass it. |
| B | One canonical safety/policy path? | **No.** `safety_guard` + `tools/policy_engine.py` both exist; not all writers consult either. |
| C | Can a user-controlled command bypass policy? | **Not verified as exploitable.** All bypassing inputs are hardcoded literals; user text always flows through `safe_exec`. |
| D | Is approval state session-safe? | **No.** §6 — process-global. |
| E | Can one client approve another client's action? | **Yes**, by design today: the queue is shared and unauthenticated. |
| F | Does every file mutation participate in backup/undo? | **Not uniformly** — two write paths with divergent undo formats (CODE-006). Chat patches and the workspace route are covered. |
| G | Is the Workspace editor consistent with chat patching? | **Partially.** Both write and log undo, but the editor skips the diff/preview/conflict-check step. |
| H | One canonical memory architecture? | **No.** SQLite + JSON + in-process, no single owner. |
| I | One canonical circuit breaker? | **No.** Three, one live. |
| J | One canonical TTS implementation? | **Yes** — `text_to_speech.py`; `sherly_core/text_to_speech.py` is an intentional re-export shim. |
| K | Does pip installation reproduce a working app? | **No.** See PKG-001. The documented flow (`git clone` + `requirements.txt`) works; the package does not. |
| L | Are all runtime modules packaged? | **No.** No `py-modules`, no `remote_*`, no `plugins`, no package data. |
| M | Do CI tests exercise the security boundaries? | **Yes for shell/path/AST** — and **no** for the SSRF module's production wiring or session isolation. |
| N | Are README test counts verifiable? | **No.** Three different numbers, none matching the 124 collected. |
| O | Are model lists discovered dynamically? | **Partially.** Ollama is discovered (`model_scanner`, `/api/tags`); cloud IDs are hardcoded (`gpt-4o-mini`, `gemini-1.5-flash`, `llama3-70b-8192`, `gpt-4o`, `gemini-1.5-pro`). |
| P | Are dashboard statistics genuine? | **Yes.** `/api/health` reads live config/timelines after the earlier key-name fix; no fake metrics found in frontend. |
| Q | Fake/demo resources? | **`[R2]` Qualified yes, one item.** Frontend has no mock/demo/sample datasets and no fake metrics. But `plugins/weather.py` is a **placeholder stub** (`"Placeholder implementation until a weather data source is integrated"`, returns "Weather feature coming soon") and it is user-reachable via plugin dispatch (`plugin_manager.get_enabled_plugin_names` / `run_plugin` from `command_router`). |
| R | Unnecessary images/assets? | **None found** at this depth; frontend is small and contains no stock imagery. |
| S | Are frontend/backend contracts synchronized? | **Yes.** `frontend/src/types/api.ts` matches `backend/api/schemas/contracts.py`; verified via `test_api_contracts.py`. |
| T | All documented features reachable? | **No.** SSRF firewall, `resilience.py`, `intent_router`/`sherly_commands`, `providers.py`. |
| U | Any security guarantees path-dependent? | **Yes.** C, F, G above. |
| V | Cross-platform claims verified? | **No.** Windows runtime-verified; macOS/Linux build-only, self-declared `NOT_TESTED`. |
| W | Can the system recover from failed dependencies? | **Mostly yes** — 60 s LLM timeout, retries via `tenacity`, circuit breakers, web-search fallback, stale-preview expiry, WebSocket reconnect with exponential backoff, conflict detection before overwrite. |
| X | Can a user lose work despite documented undo? | **Yes, in edge cases** — undo is capped at 5 entries and shared across clients, so a second client's action can evict the entry you expected to undo. |
| Y | Hardcoded business data that should be dynamic? | **Yes** — cloud model IDs and the hardcoded release version string. |
| Z | Single most dangerous unresolved issue? | **ARCH-001** — process-global approval/preview/undo state; it silently breaks the multi-client isolation the product advertises and is the precondition for the CSRF finding (SEC-004). |

---

## 11. SCORECARD (Phase 41) — descriptive, evidence-backed

| Dimension | Status | Evidence |
|---|---|---|
| Architecture | Weak | Root-module core, duplicated concerns, package-boundary inversions (§4) |
| Code quality | Adequate | Readable, typed, thread-aware, zero TODO/FIXME/HACK in Python; duplication and broad excepts |
| Security | Strong core / weak assurance | Sandbox and AST tests are excellent; SSRF control unwired; policy path-dependent |
| Safety model | Mostly good | 3-tier classification + approval + TTL + preview conflict check; bypass paths exist |
| Product completeness | Good | Chat, tools, approvals, workspace, undo, voice, models, remote all wired end-to-end |
| Testing | Adequate | 124 tests, strong on security; gaps on isolation, depth, hardware |
| Documentation | Weak | 50 files, three test counts, unverifiable benchmarks, unimplemented claims |
| API quality | Good | Typed schemas, consistent errors, contract tests |
| Frontend quality | Good | 20 files, typed store, reconnect logic, no fake data |
| Performance | Unverified | No harness exists; optimizations described (WAL, batching, breakers) are plausible and partially verifiable |
| Reliability | Good | Timeouts, retries, breakers, fallbacks, reconnect, conflict detection |
| Packaging | Broken (latent) | PKG-001/002 |
| CI/CD | Partial | Real test+lint+build gate, but excludes root modules, ignores mypy, main-only trigger, no-op bandit |
| Dependencies | Good | Manifests reconciled, Dependabot, pinned Actions |
| Cross-platform | Unverified | macOS/Linux `NOT_TESTED` |
| Observability | Strong | Structured redacted JSON, correlation IDs, bounded timelines, `/api/health` |
| Maintainability | Adequate | Clear naming/docstrings; held back by duplication and the flat root layer |

---

## 12. REMEDIATION ROADMAP (Phase 37)

**Phase 0 — Stop the overstatement (hours).** Fix the test-count claims to one verified number; label
the benchmark table as targets or add the harness; retract or wire the SSRF claim; mark macOS/Linux
`BUILD VERIFIED ONLY`. Cheap, and it is the whole reason trust is currently misplaced.

**Phase 1 — Close the assurance gaps (days).** SEC-002/003/005/006; unify the two write paths
(CODE-006); add the root modules to the CI lint gate (CODE-001); fix the bandit `-r src/` no-op
(CODE-002).

**Phase 2 — Session identity (one focused pass).** ARCH-001: thread a session/client identity through
the approval queue, confirmation slot, preview store, and undo history — the pattern already exists in
`conversation_memory` — and add the isolation tests (TEST-001).

**Phase 3 — Convergence.** Pick canonical winners per concern in §4; delete `sherly_core/resilience.py`,
`sherly_core/providers.py`, `intent_router`+`sherly_commands`, and decide the fate of `sherly_ui`/`sherly_ai`.

**Phase 4 — Packaging.** Declare `py-modules` (or restructure), add `remote_*`/`plugins`/package data,
read the version from `pyproject`, then decide whether a wheel is a real distribution channel (PKG-002).

**Phase 5 — Documentation consolidation.** Collapse 20 phase reports into one living document plus
superseded history.

**Defer (accepted debt):** BLE001 burn-down outside hot modules; mypy adoption; undo-depth increase;
frontend unit tests. **Do not build:** Kubernetes, microservices, Redis/Kafka, a distributed queue, or
an event bus — the product is local-first and single-user by nature; its needs are correctness,
isolation, and honest documentation.

---

## 13. STRENGTHS WORTH PRESERVING

1. `safe_exec`'s whitelist → classifier → `shlex`/`shell=False` chain, and the AST tests that keep it
   honest (`tests/test_security.py:229-248,447-473`).
2. `apply_preview`'s pre-write conflict check — it refuses to silently overwrite externally modified files.
3. Atomic backup + undo with the new create-deletes-file semantics and legacy-format compatibility.
4. `remote_api`'s timing-safe key comparison, fail-closed default, and 10 MB bounded upload.
5. Structured JSON logging with dual redaction and correlation IDs; bounded timelines.
6. Secret hygiene: no tracked secrets, `.env` ignored, `remote_ui` reads the key from `sessionStorage`.
7. Frontend↔backend type/contract alignment, verified by test rather than convention.
8. Zero `TODO`/`FIXME`/`HACK` markers in Python — the codebase documents intent in docstrings instead.

---

## 14. FINAL SUMMARY (Phase 47)

**TRUE CAPABILITIES:** chat routing with intent classification; model selection across Ollama +
3 cloud providers with timeout/retry/breaker; whitelisted, guarded, non-shell command execution;
preview→diff→approve→apply with conflict detection; atomic backup, undo, and history; workspace file
read/write/undo; live model discovery; voice STT/TTS with overlap prevention; remote PWA with key auth,
uploads, and command proxy; structured redacted observability; React workspace with typed contracts.

**BROKEN CAPABILITIES:** `pip install .` (PROVEN broken statically); pre-commit bandit hook (PROVEN
no-op); README performance benchmarks (PROVEN unverifiable).

**PARTIAL CAPABILITIES:** undo (capped at 5, global); multi-client operation (state is global);
cross-platform (Windows verified only); type checking (claimed, unconfigured); policy enforcement
(canonical for user text, bypassed for internal paths).

**DISCONNECTED CAPABILITIES:** `core/network_security.py` (documented, unreachable);
`sherly_core/resilience.py` (unreachable); `sherly_core/providers.py` (test-only);
`intent_router`/`sherly_commands` (unreachable chain).

**MISSING CAPABILITIES:** session/client identity for approval & undo; authentication on the local API;
a benchmark harness; frontend unit tests; macOS/Linux runtime validation; any publication of a real
distribution artifact.

**SECURITY RISKS:** SEC-002 (latent ungated `shutdown`), SEC-003 (policy bypass paths, non-exploitable),
SEC-004 (unauthenticated, CORS-simple approve/undo on loopback), SEC-005 (upload overwrite), SEC-006
(global confirmation slot), SEC-001 (documented control absent).

**DATA-LOSS RISKS:** undo eviction across clients (ARCH-001 + CODE-005); two write paths with
divergent undo formats (CODE-006).

**ARCHITECTURAL DEBT:** flat root-module core with inverted package dependencies; five duplicated
concerns; five dead-or-disconnected modules.

**TESTING GAPS:** session isolation, undo depth, cross-client confirmation, hardware-dependent paths,
SSRF production wiring.

**DOCUMENTATION GAPS:** three test counts; unverifiable benchmarks; unimplemented SSRF claim;
cross-platform overstatement; 50 overlapping doc files.

**PACKAGING/RELEASE GAPS:** no `py-modules`; missing subpackages and package data; no wheel/installer;
hardcoded version; release pipeline ships a JSON manifest only.

**PERFORMANCE GAPS:** unmeasured; no harness.

**PLATFORM GAPS:** macOS/Linux build-only, self-declared untested.

**UNNECESSARY CONTENT/ASSETS:** dead modules (`resilience.py`, `providers.py`, `intent_router` +
`sherly_commands`, `sherly_ai`); duplicate task queue; 20 historical audit files. **No fake assets or
demo data were found** — the frontend is clean.

**TOP P0 ITEMS:** none proven.

**TOP P1 ITEMS:** SEC-001, ARCH-001, PKG-001, DOC-001, DOC-002, DOC-003, TEST-001, ARCH-002.
(CODE-001 moved to P2 on re-measurement — see §15.)

**TOP P2 ITEMS:** SEC-002 … SEC-009, CODE-001/002/003/004/009, TEST-002, DOC-004/005, ARCH-003.

**SAFE TO DEFER:** CODE-005, CODE-006, CODE-007, CODE-008, PKG-002/003, mypy, frontend unit tests.

**SHOULD NOT BE BUILT:** Kubernetes, microservices, Redis/Kafka, distributed queues, event buses,
service meshes, multi-tenant cloud infrastructure.

**RELEASE BLOCKERS (to call the next version GA):** DOC-001/002/003, SEC-001, SEC-002, SEC-004,
PKG-001, ARCH-001.

**RECOMMENDED NEXT PHASE:** Phase 0 — make the documentation tell the truth (test count, benchmark
table, SSRF claim, platform status). It is the cheapest fix, it removes every unimplemented claim
found in this audit, and without it every later fix is still being sold with overstated evidence.

---

## 15. `[R2]` ADVERSARIAL RE-VERIFICATION LEDGER (2026-09-20)

Method: every load-bearing claim was attacked, not re-read. Where a claim asserted "not exploitable"
or a number, I re-derived it from the code or re-ran the tool instead of trusting the first pass.

### 15.1 Re-confirmed with fresh evidence

| Claim | Fresh evidence | Result |
|---|---|---|
| Suite size | `pytest tests/ --collect-only` → `124 tests collected` | CONFIRMED |
| Suite outcome | `pytest tests/ -q` → `2 failed, 122 passed, 2 warnings in 9.77s`, failures both `pvporcupine` | CONFIRMED (and the "0 warnings" claim refuted) |
| Test counts 120 / 117 / 109 vs reality | three docs, one suite, three different numbers | CONFIRMED |
| PKG-001: no `py-modules` | full read of `pyproject.toml` — `[tool.setuptools]` contains only the 8-entry `packages` list, no `py-modules`, no `package-data`; 10 root-module imports cross the package boundary | CONFIRMED |
| SEC-002: dead `shutdown /s /t 1` | `grep -rn intent_router` → zero importers outside its own file; `sherly_commands` imported only by it; no dynamic-import route reaches it (`plugin_manager` only loads `plugins.*`; `main.py:65 __import__` iterates a hardcoded dependency list) | CONFIRMED |
| SEC-003: bypass paths are constant-input | `detect_project()` returns 3 literals; `LAST_FIX_CONTEXT["command"]` is written only from it; `_build_command_map()` returns hardcoded literal `argv`/`startfile` per OS | CONFIRMED (not user-influenced) |
| ARCH-001: global state | module-level `_pending_actions`, `_pending_confirmation`, `preview_store`, `_action_history` re-read; still singletons; `_MAX_HISTORY = 5` | CONFIRMED |
| All subprocess sites use `shell=False` | re-read `tools/executor.py`, `tools/terminal_tools.py`, `tools/screen_tools.py` (`["ollama","run","llava",img]`), `sherly_commands/system_commands.py`, `scripts/package.py`, `sherly_ui/views/workspace_view.py` | CONFIRMED |
| No secrets / no fake datasets | grep for key patterns → clean; frontend has no mock/demo arrays | CONFIRMED |

### 15.2 Corrected — the original report was wrong or overstated

1. **SEC-001 — the "no exploit found" sentence was WRONG.** I had concluded the SSRF gap was merely a
documentation defect because every outbound call targets a constant. I had not read
`agents/playwright_agent.py`, which takes its starting URL straight from model output and calls
`page.goto()` unvalidated, then drives the page with model-chosen `CLICK`/`TYPE`. Reachable from
`agent_manager.py:76`. Severity re-rated to a genuine P1 with a documented trigger, and the
justification for *not* calling it P0 is now written out explicitly instead of implied.
2. **SEC-004 — the mitigation claim was WRONG.** I wrote that an action ID and TTL protect the
dangerous endpoints. They do not protect `POST /api/actions/undo`, which takes **no parameters** and
is therefore a zero-precondition CORS-simple state change. Re-rated P2 → MEDIUM, and the finding
widened to include the key-protected `remote_api` proxying to the unauthenticated `remote_agent`
`/execute` endpoint.
3. **CODE-001 — the implication was OVERSTATED.** Linting all 18 excluded root modules with the exact
CI rule set produces **one** E731 style finding. The gate gap is real and worth closing, but nothing is
being concealed today. Re-rated P1 → P2.

### 15.3 Added by the re-verification (SEC-007, SEC-008, SEC-009, CODE-009)

These were not in the first pass and are now in the master table, because the corrections above made
them load-bearing rather than incidental: plugin auto-import with a CWD-rooted writable boundary
(SEC-007), the CWD-as-workspace-root boundary itself (SEC-008), screen capture marked SAFE and
auto-executed to a possibly-cloud model (SEC-009), and `ToolSpec` metadata that is declared but read
nowhere (CODE-009).

### 15.4 Could NOT confirm — stated as unverified rather than judged

| Item | Why unverifiable here |
|---|---|
| Benchmark figures (4.2ms, 6.8ms, 14,184 ops/sec, 18ms, 142ms, 320ms) | No harness, script or raw result in the repo. I can only show the numbers are **unreproducible**, not that they are false. |
| macOS / Linux runtime behaviour | No environment. The only evidence is the manifest's own `NOT_TESTED` self-report. |
| Voice runtime (STT/TTS, wake word, PortAudio) | No microphone/speaker hardware; the 2 failing tests are exactly this class. |
| Whether a poisoned page realistically steers the playwright loop to an internal target | Logically traced from code; **not executed** (would require driving a live headful Chromium session). |
| Provenance of "117" (or "120" / "109") | No generator, script or CI job emits these numbers; the mapping is unreconstructable. |
| `core/network_security.py`'s internal correctness (`is_safe_url`, `safe_fetch_url`) | Read-only audit; the module is unexercised in production so I did not test its behaviour, only its reachability. |
| `remote_agent`'s exposure beyond `/execute` | I read `agent.py` in full and found the single unauthenticated route; I did **not** verify how/where it is bound or launched (no launcher or unit file was inspected). |
| Anything requiring Ollama or a cloud API key | No model server or credentials available. |

### 15.5 Net effect on the verdict

The **"no P0" verdict stands**, now with its conditions written down: loopback-only binding, all
subprocess sites `shell=False` with constant or gated argv, and no off-host reachability. The
**severity distribution shifted** — SEC-001 rose to a real P1, SEC-004 rose to MEDIUM, CODE-001 fell to
P2 — so the report is now harder on the two findings that matter and softer on the one that did not.
The corrections all point the same direction: the *documented* security story is more optimistic than
the *implemented* one, and the gap is concentrated in the agentic and local-API surfaces rather than in
the command sandbox, which survived every attempt to break it.
