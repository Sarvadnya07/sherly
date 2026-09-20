# Sherly Human-in-the-Loop Approval Model (Phase 11)

**Target Surface**: `frontend/src/components/ui/ApprovalDialog.tsx`, `approval_service.py`, `action_manager.py`
**Classification**: Server-Authoritative, Session-Scoped Approval & Gate System
**Status**: ACTIVE & PRODUCTION-READY (session-scoped since the ARCH-001/SEC-005 remediation)

---

## 1. Approval Queue Lifecycle

```text
1. REQUEST_APPROVAL (approval_service.create_ticket)
   ├── Cryptographically random ticket ID (secrets token, unguessable)
   ├── Immutable ticket: owner session, action payload, risk, TTL (120s)
   └── Bound to the requesting session identity

2. DISPLAY_APPROVAL_MODAL
   ├── Accessible modal dialog (ARIA modal, focus trapped)
   ├── Details: What, Target, Reason, Risk Level, Reversibility
   └── Keyboard controls: Enter (Approve when focused), Esc (Reject)

3. APPROVAL_DISPATCH
   ├── User clicks Approve or Reject
   ├── POST /api/actions/approvals/{action_id}/approve or /reject
   ├── Backend resolves the caller's session identity (X-API-Key remote key
   │   → remote session; X-Session-ID header → that session; else local)
   ├── Ownership enforced server-side; wrong/unknown session → 409 generic message
   ├── Atomically consumed (single-use; exactly one execution under concurrency)
   ├── Execute via safe_exec / apply_preview
   └── Broadcast action_update WebSocket event
```

## 2. Session & Ownership Model

- Tickets are owned by a session identity, never by process-global state.
- Client A can never approve, cancel, view, or consume client B's ticket —
  foreign and unknown IDs are indistinguishable (no existence oracle).
- The remote agent runs under its own distinct session identity.
- Command-router replies must name the ticket: `approve <id>` / `cancel <id>`
  / `confirm <id>`. Bare "yes"/"confirm" never consumes a ticket.

## 3. Immutability & Re-entrancy Protection

- **No Argument Tampering**: The backend executes only the exact action stored
  in the frozen `ApprovalTicket` at creation time.
- **Idempotency**: A second `/approve` on a consumed ticket returns 409
  ALREADY_CONSUMED; the action executes exactly once.
- **TTL Expiration**: Tickets expire after 120 seconds and cannot be
  resurrected; expired tickets cannot be approved or executed.
- **States**: PENDING → APPROVED(consumed) | CANCELLED | EXPIRED. All
  transitions are atomic under the service lock.
