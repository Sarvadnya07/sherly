# REMEDIATION STATUS — PATCH PREVIEW SESSION OWNERSHIP — 2026-09-20

## 1. Baseline

- Branch: `main` at `a61d754` (post-PR-#144, clean, up to date with origin).
- All fixes from PRs #142/#143/#144 intact and untouched.

## 2. Root cause

`tools/preview.py` stored staged patch previews in a process-global dict keyed
only by preview ID. Any client that learned an ID (e.g. from an assistant
message) could read, apply, or reject another session's patch preview — the
last remaining ownership gap flagged in the session-approvals remediation.

## 3. Architecture

`tools/preview.py` was rewritten as the canonical session-scoped preview
store, reusing the approval_service identity model (no second identity
mechanism):

- `_preview_store: {preview_id: {session_id, changes}}`
- `save_preview(changes, session_id)` → deep-copies the payload (immutable
  after creation) and issues an unguessable `secrets`-based ID
- `_resolve(preview_id, session_id)` enforces ownership inside the store;
  foreign and unknown IDs raise the identical `ApprovalError(NOT_FOUND,
  "Invalid preview ID")` — no existence oracle
- `consume_preview()` atomically removes the preview under the lock before
  any filesystem mutation → single-use, concurrency-safe
- `get/has/discard/apply_preview` all take `session_id` and delegate through
  ownership enforcement

## 4. Security invariants (all enforced server-side, all tested)

1. Owner immutable ✅ 2. Payload deep-copied and immutable after creation ✅
3–6. Wrong session cannot get/apply/cancel/list ✅ 7. Foreign = unknown ✅
8. Single-use; concurrent apply yields exactly one execution ✅
9. Pre-write conflict check unchanged ✅ 10. Backup + undo unchanged ✅

Approval↔preview identity agreement: the router's `approve <id>` path checks
`has_preview(..., session_id)` before applying, so a ticket/preview from
session A can never be consumed via session B's approval flow.

## 5. Changed files

| File | Change |
|---|---|
| `tools/preview.py` | Session-scoped store; ownership enforced in-layer; single-use consume; conflict/backup/undo behavior preserved |
| `tools/fix_project.py` | `apply_last_fix(..., session_id=)` binds created previews to the routing session; UUID IDs replaced by service-issued unguessable IDs |
| `command_router.py` | approve path and `apply fix` pass the session through |
| `backend/api/routes/actions.py` | preview get/apply/reject resolve identity server-side; 404 for unknown AND foreign previews (identical response); reject is not an oracle |
| `tests/test_preview_ownership.py` | **New** — 18 behavioral tests |
| `docs/audits/REMEDIATION-STATUS-2026-09-20.md` | ARCH-001 fully FIXED |

Frontend: no changes required (HTTP paths and response shapes unchanged;
backend authoritative).

## 6. Tests

18 new tests: session scoping, wrong-session get/apply/cancel/list rejection,
no-existence-oracle, payload/owner immutability, single-use, 6-thread
concurrent apply (exactly one execution), two-session isolation,
apply-after-removal, reconnect ownership, hash-conflict block, backup before
apply, undo after apply, approval↔preview identity match, and
fix_project session binding.

## 7. Validation

- Targeted suites (preview ownership + approval sessions + safety guard +
  remote agent): **96 passed**
- Full suite: **183 passed, 2 failed** — the pre-existing `pvporcupine`
  native-lib environment failures (unrelated; CI installs the package and
  passes)
- Ruff: clean on all touched files; frontend `tsc --noEmit`: clean

## 8. Remaining risks

- `_action_history` (undo stack) remains a shared bounded list by design:
  undo is a local-desktop operation (remote undo is explicitly rejected),
  so there is no second principal that could act on it today. Revisit if
  local multi-user sessions are ever introduced.
- `X-Session-ID` remains client-supplied scoping (not authentication);
  only the remote API key authenticates. Unchanged from the approvals phase.

## 9. Final status

**PREVIEW OWNERSHIP: FIXED.** With this change, every user-reachable
multi-principal mutable store (approvals, confirmations, patch previews) is
session-scoped and ownership-enforced at the storage layer.
