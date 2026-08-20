# Sherly Human-in-the-Loop Approval Model (Phase 11)

**Target Surface**: `frontend/src/components/ui/ApprovalDialog.tsx` & `action_manager.py`  
**Classification**: Server-Authoritative Approval & Gate System  
**Status**: ACTIVE & PRODUCTION-READY  

---

## 1. Approval Queue Lifecycle

```text
1. REQUEST_APPROVAL
   ├── Generate unique action_id (UUID short)
   ├── Record immutable command/arguments, timestamp, and risk level
   └── Prune expired entries (>120s TTL)

2. DISPLAY_APPROVAL_MODAL
   ├── Accessible modal dialog (ARIA modal, focus trapped)
   ├── Details: What, Target, Reason, Risk Level, Reversibility
   └── Keyboard controls: Enter (Approve when focused), Esc (Reject)

3. APPROVAL_DISPATCH
   ├── User clicks Approve or Reject
   ├── POST /api/actions/approvals/{action_id}/approve or /reject
   ├── Atomically pop action from pending store (idempotent, single-use)
   ├── Execute via safe_exec / apply_preview
   └── Broadcast action_update WebSocket event
```

---

## 2. Immutability & Re-entrancy Protection

- **No Argument Tampering**: The backend executes only the exact `cmd` stored in `_pending_actions[action_id]` at creation time.
- **Idempotency**: Calling `/approve` twice on the same `action_id` fails gracefully on the second attempt because the action was already consumed.
- **TTL Expiration**: Stale actions older than 120 seconds are automatically purged, preventing delayed or abandoned dangerous operations from executing.
