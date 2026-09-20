# Changelog

## 2026-09-20 — Remediation pass (audit findings)

### Security
- Browser agent: model-supplied starting URLs are now validated through the
  canonical SSRF policy (`core/network_security.is_safe_url`) before
  navigation; loopback/private/reserved/scheme/credential attacks fall back to
  the default URL. (SEC-001)
- `run_project` now enforces the same contract as `safe_exec`: chaining-operator
  rejection, parsed-executable allowlist (prefix collisions such as
  `pythonista` no longer match), and dangerous/confirm classification. (SEC-003)
- Remote agent: undo requests over remote access are explicitly rejected (undo
  has no remote path by design); loopback-only bind contract documented. (SEC-004)
- Screen capture re-classified from SAFE to CONFIRM with approval required —
  it can no longer be auto-executed by the tool loop. (SEC-009)
- `requires_approval` on tool specs is now enforced by the policy engine
  instead of being write-only state. (CODE-009)
- Removed dead execution chain containing an ungated Windows shutdown command
  (`sherly_core/intent_router.py`, `sherly_commands/`, `sherly_ai/`). (SEC-002)

### Product reliability
- Workspace editor saves now participate in the canonical backup/undo
  pipeline: previous content is snapshotted, the write is logged as an
  undoable action, and undo restores the original content. (PRODUCT-001)
- Optimistic-concurrency guard on file writes: the editor sends the content it
  loaded; the backend rejects the write with 409 if the file changed on disk
  in the meantime, instead of silently clobbering external edits.

### Packaging
- Wheel now includes all 18 root-level production modules (`py-modules`) and
  the previously omitted subpackages (`backend.api.*`, `plugins`, `remote_api`,
  `remote_agent`, `sherly_ui.views`). `pip install` yields an importable
  application. (PKG-001)
- CI runs a wheel-completeness smoke test on every build.

### Quality gates
- CI ruff gate now covers all root modules; bandit pre-commit hook scans the
  real layout instead of the nonexistent `src/`. (CODE-001, CODE-002)

### Documentation
- README test count corrected to the actual suite result (141 passing / 143
  collected, wake-word caveat documented); mypy honestly labeled as
  developer-side, not a CI gate. (DOC-001, DOC-003)
- PERFORMANCE.md benchmark figures relabeled as design targets — no benchmark
  harness exists to reproduce the previously published "measured" numbers.
  (DOC-002)

### Deferred (documented in docs/audits/REMEDIATION-STATUS-2026-09-20.md)
- ARCH-001 session-scoped approvals (needs a session-identity design),
  ARCH-002 consolidation (3 breakers / 2 queues / 3 memory stores / 2 TTS),
  SEC-005 upload collision handling, SEC-008 workspace-root model.
