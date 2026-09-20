# REMEDIATION STATUS — SESSION-SCOPED APPROVALS (ARCH-001 / SEC-005) — 2026-09-20

## 1. Baseline

- Branch: `main` at `16699a2` (clean, up to date with origin).
- Previous remediation (PR #143) intact; no stale branches used.

## 2. Previous implementation

Two independent process-global approval stores:

- `safety_guard._pending_confirmation` — a single-slot dict; `handle_confirmation_reply` accepted bare `confirm`/`yes` from **any** caller and confirmed whatever was pending (audit SEC-006).
- `action_manager._pending_actions` — ID-keyed (8 chars of a UUID4) but **ownerless**: any client that learned an action ID could approve or cancel it (audit ARCH-001/SEC-005).

No session-identity primitive existed anywhere in the system.

## 3. Security weakness

- Any client (local UI, remote PWA via the agent, concurrent browser tabs) could approve another client's pending command.
- A stray "yes" on one surface consumed a confirmation raised by another.
- Repeated approval of the same ID raced on pop-then-execute (double execution possible under interleaving).

## 4. New architecture

One canonical service, `approval_service.py`:

- `ApprovalTicket` — frozen dataclass: unguessable `ticket_id` (`secrets`), `session_id` (owner, immutable), `action` payload (immutable), risk, `created_at`/`expires_at` (120s TTL preserved), `status` ∈ PENDING/CANCELLED/EXPIRED/CONSUMED.
- API: `create_ticket`, `get_ticket`, `list_pending`, `approve_ticket`, `cancel_ticket`. All lookups take the caller's `session_id` and enforce ownership inside the service.
- Unknown and foreign IDs return the identical generic error (`ApprovalError("NOT_FOUND")`) — no existence oracle.
- Single lock guards the table; `approve_ticket` transitions PENDING→CONSUMED **under** the lock before executing, so exactly one concurrent caller wins.
- Session identities: `local` (default desktop), `remote-agent` (remote agent process), or a client-supplied `X-Session-ID` header (bounded to 128 chars). Remote callers authenticated with the gateway API key resolve to `remote-agent`.

## 5. Files changed

| File | Change |
|---|---|
| `approval_service.py` | **New** — canonical ticket service |
| `safety_guard.py` | Global slot removed; CONFIRM creates a ticket; replies must be `confirm <id>` / `cancel <id>`; `__CONFIRMED__` contract preserved |
| `action_manager.py` | `_pending_actions` removed; request/approve/cancel/list delegate to the service with `session_id` |
| `command_router.py` | `route_command(text, session_id=...)`; approve/cancel/pending all session-scoped; ApprovalError surfaces the deliberate message |
| `tools/policy_engine.py` | `execute_capability(..., session_id=)`; tool CONFIRM tickets bind to the session |
| `backend/api/routes/actions.py` | `_session_id(request)` identity resolution; approve/reject/list scoped; ApprovalError → 409 |
| `remote_agent/agent.py` | Routes under `REMOTE_SESSION_ID` |
| `tests/test_approval_sessions.py` | **New** — 24 behavioral tests |
| `tests/test_safety_guard.py`, `tests/test_remote_agent_security.py` | Updated to ticket model; remote session assertion added |
| `docs/APPROVAL_MODEL.md` | Rewritten for the session-scoped model |

## 6. Approval lifecycle

`policy/classify` → `create_ticket(session)` → prompt/queue with ticket ID → owner presents `approve <id>` (route or API) → backend resolves identity → ownership+TTL verified → atomic CONSUMED → executor (`safe_exec`/`apply_preview`) runs once → action history/undo (unchanged) → broadcast.

## 7. Security invariants (all enforced server-side, all tested)

1. Owner immutable (frozen dataclass) ✅ 2. Payload immutable ✅ 3/4. Only owner approves/cancels ✅ 5. Expired rejected ✅ 6. Cancelled rejected ✅ 7. Single-use; replay → ALREADY_CONSUMED ✅ 8. Foreign = unknown (no oracle) ✅ 9. Executor receives the frozen payload only ✅ 10. Reconnect keeps ownership with the session; a new identity inherits nothing ✅.

## 8. Tests added

24 tests in `tests/test_approval_sessions.py` covering every scenario from the phase brief, including 8-thread concurrent approval (exactly one execution, 7 ALREADY_CONSUMED), approve-vs-cancel race, TTL expiry, immutability, cross-session isolation, router integration with `safe_exec` as executor, and remote-agent identity distinctness.

## 9. Test results

- Full suite: **165 passed, 2 failed** — the same 2 `pvporcupine` native-lib environment failures present before this phase (CI installs the package and passes).
- Ruff: clean on all touched files. Frontend `tsc --noEmit`: clean (no contract change required; API paths unchanged).

## 10. Compatibility

- Public HTTP contracts unchanged (paths, methods, response shapes). New: 409 with a deliberate message for expired/cancelled/consumed/foreign tickets; pending list is now per-session.
- Bare `confirm`/`cancel`/`yes` no longer consume anything — prompts now always include the ticket ID. Existing UI already sends the ID in the URL path.
- `preview_store` (patch previews) is intentionally unchanged: previews are separate from approvals and are addressed in the deferred consolidation item below.

## 11. Remaining risks / Deferred

- `tools/preview.py` `preview_store` remains ID-keyed without session binding — a remote client could apply a patch preview ID it learned. Deferred to a follow-up that threads the same session identity through previews (same pattern, separate scope).
- WebSocket clients are not individually authenticated; they share the local session by design (single-user local app). A multi-user deployment must issue server-side identities first.
- `X-Session-ID` is client-supplied; it scopes tickets but does not *authenticate* (only the remote API key authenticates). Acceptable for a local-first product; revisit if remote multi-client becomes a real deployment.

## 12. Master remediation status

ARCH-001/SEC-005 in `docs/audits/REMEDIATION-STATUS-2026-09-20.md` moves from DEFERRED to **FIXED** (preview-store session binding noted as follow-up).
