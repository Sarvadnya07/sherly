# REMEDIATION STATUS — 2026-09-20

Remediation pass against findings in `docs/audits/master-audit-2026-09-20.md` (PR #142).
Each finding was re-verified against current `main` before fixing.

| ID | Finding | Previous State | Current State | Fix | Tests | Docs | Status |
|----|---------|----------------|---------------|-----|-------|------|--------|
| PRODUCT-001 | Workspace editor writes bypass backup/undo pipeline | STILL_VALID | `write_file()` routes through `action_manager.write_file_safe()`; snapshot + undoable action + 409 conflict guard (`expected_content`) | `backend/api/routes/files.py`, `contracts.py`, frontend save path passes `activeOriginalContent` | `tests/test_files_route_undo.py` (6: undo round-trip, creation undo, conflict, no-false-history, traversal, bounded history) | — | **FIXED** |
| SEC-001 | Browser agent navigates to unvalidated model-supplied URL | STILL_VALID | `resolve_safe_start_url()` applies canonical `is_safe_url` (SSRF policy) before `page.goto` | `agents/playwright_agent.py` | `tests/test_security.py` (5: loopback, private/IPv6/link-local, schemes+credentials, public allow, garbage fallback) | `docs/PERFORMANCE.md` SSRF claim now accurate | **FIXED** |
| SEC-002 | Dead chain `intent_router` → `sherly_commands` (ungated `shutdown`) | STILL_VALID | Dead modules deleted (`sherly_core/intent_router.py`, `sherly_commands/`, `sherly_ai/`) | deleted | full suite green post-delete | — | **FIXED** |
| SEC-003 | `run_project` bypassed allowlist + safety_guard | STILL_VALID | Same contract as `safe_exec`: chaining rejection → parsed-executable allowlist (prefix-collision safe) → risk classification | `tools/executor.py` | `tests/test_security.py` (5: chaining, non-allowlisted, `pythonista` collision, confirm-class blocked, safe allow) | — | **FIXED** |
| SEC-004 | Remote undo reachable without session ownership; local agent no auth | STILL_VALID | Remote undo explicitly rejected with deliberate response; loopback bind contract documented | `remote_agent/agent.py` | `tests/test_remote_agent_security.py` (5) | boundary documented in module docstring | **FIXED** (local-API loopback-token design deferred — see below) |
| SEC-005 | Uploads silently overwrite same-named files | STILL_VALID | not addressed this pass | — | — | — | **DEFERRED** |
| SEC-006 | Global single-slot confirmation state | STILL_VALID | not addressed this pass (needs session identity — ARCH-001) | — | — | — | **DEFERRED → FIXED 2026-09-20** (tickets require `confirm <id>`; bare yes/confirm no longer consumes anything) |
| SEC-008 | `Path.cwd()` workspace boundary | STILL_VALID | verified intentional (loopback-only app); no boundary change made | — | — | — | **DEFERRED** (documented risk) |
| SEC-009 | `screen.capture` classified SAFE | STILL_VALID | re-classified CONFIRM + `requires_approval=True`; not auto-executable via `execute_capability` | `tools/native_tools.py`, `tools/policy_engine.py` | 2 tests | description updated | **FIXED** |
| PKG-001 | Wheel omitted all 18 root modules and backend subpackages | STILL_VALID | `py-modules` + full subpackage list; wheel verified to contain runtime modules, routes, schemas, ws, remote_agent/api, plugins | `pyproject.toml` | CI package smoke test (wheel contents assertion) | — | **FIXED** |
| CODE-001 | CI ruff excluded all root modules | STILL_VALID | gate now includes `*.py`; 3 findings fixed (2 in new tests, 1 lambda in TTS) | `.github/workflows/ci.yml`, `text_to_speech.py` | ruff exit 0 | — | **FIXED** |
| CODE-002 | Bandit scans nonexistent `src/` (no-op) | STILL_VALID | scans repo root | `.pre-commit-config.yaml` | — | — | **FIXED** |
| CODE-003 | mypy advertised as gate, not configured | STILL_VALID | README now states mypy is developer-side/optional, not a CI gate (option 2: honesty) | `README.md` | — | corrected | **FIXED** (documentation honesty) |
| CODE-009 | `requires_approval` written 6×, read 0× | STILL_VALID | `evaluate_tool_policy` now enforces the flag (CONFIRM escalation, respecting argument-aware overrides) | `tools/policy_engine.py` | existing policy tests + screen.capture tests | — | **FIXED** |
| DOC-001 | Test count: badge 120 / prose 117 / actual differs | STILL_VALID | badge and prose updated to 141 passing / 143 collected with wake-word caveat | `README.md` | — | corrected | **FIXED** |
| DOC-002 | Benchmarks published as measured, no harness | STILL_VALID | table relabeled "Design target — not yet benchmarked" with explanatory note | `docs/PERFORMANCE.md` | — | corrected | **FIXED** |
| DOC-003 | "Certified GA / zero P0-P1" | STILL_VALID | superseded by `docs/audits/master-audit-2026-09-20.md`; certification doc left as historical record | — | — | superseded | **FIXED** (via audit) |
| ARCH-001 | Global approval/preview/undo state (no session isolation) | STILL_VALID | not addressed this pass | — | — | — | **DEFERRED** |
| ARCH-002 | Duplicated concerns (3 breakers, 2 queues, 3 memory stores, 2 TTS, 2 provider stacks) | STILL_VALID | not addressed this pass | — | — | — | **DEFERRED** |
| TEST-001 | No client-isolation tests | STILL_VALID | blocked by ARCH-001 (cannot test a property that doesn't exist) | — | — | — | **DEFERRED → FIXED 2026-09-20** (`tests/test_approval_sessions.py`, 24 isolation/concurrency tests) |

## DEFERRED items — reasons and required next phase

| ID | Reason for deferral | Risk | Recommended next phase |
|----|--------------------|------|------------------------|
| ARCH-001 (+ SEC-006, TEST-001) | Session/client identity did not exist; approvals/confirmations/patch previews were process-global. **RESOLVED 2026-09-20** — approvals via `approval_service.py` (`REMEDIATION-STATUS-SESSION-APPROVALS-2026-09-20.md`); patch previews via session-scoped store (`REMEDIATION-STATUS-PREVIEW-OWNERSHIP-2026-09-20.md`). | MEDIUM — single-user local app; risk materializes with remote PWA concurrent use | Delivered across PRs #144 and the preview-ownership phase | **FIXED** |
| ARCH-002 | Consolidation requires choosing canonical implementations per concern and migrating callers; mechanical in places (task queues) but behavioral in others (memory stores hold existing user data that must not be lost) | LOW-MEDIUM (dead/duplicate code, not attack surface) | Follow the already-designed consolidation plan; start with the two task queues and the unused `sherly_core/providers.py` |
| SEC-005 | Small, real, but not on the critical path; fixing without its own test would violate the test-first rule this pass follows | LOW | One-line collision check + test; fold into the next PR touching `remote_api` |
| SEC-008 | Verified intentional for a loopback-only local app; changing the boundary model (config-based root) is a product decision, not a defect fix | LOW while loopback-only; MEDIUM if the API is ever exposed | Product decision + explicit config boundary + tests, only if network exposure is planned |

## Validation performed

- `pytest`: **141 passed, 2 failed** (both `pvporcupine` native-lib environment failures, pre-existing, CI installs the package) — 22 new tests added this pass, all passing
- `ruff` (full gate incl. root modules): **clean**
- `compileall`: clean
- Frontend: `tsc --noEmit` clean, `npm run build` green (232.81 kB JS / 68.53 kB gz)
- Wheel build: verified complete via the new CI smoke assertions locally
