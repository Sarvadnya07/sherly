# Sherly Safety Architecture & Multi-Modal Control (Phase 11)

**Target System**: Entire Sherly Application (Assistant, Workspace, Voice, Remote API)  
**Classification**: Principle of Least Privilege & Human-in-the-Loop Security Architecture  
**Status**: ACTIVE & PRODUCTION-READY  

---

## 1. Core Principles

1. **Backend Safety Authority**:
   - The LLM does NOT decide whether an action is safe.
   - The frontend client does NOT decide whether an action is safe.
   - Voice transcript wording does NOT decide whether an action is safe.
   - The Python backend policy engine (`PolicyEngine`, `safety_guard`, `action_manager`) is 100% authoritative.
2. **Canonical Risk Model**:
   - **`SAFE`**: Read-only, non-destructive inquiries (e.g. `filesystem.read`, `filesystem.scan`, `web.search`). Auto-executed without human prompt.
   - **`CONFIRM`**: Standard state-changing developer actions (e.g. `filesystem.write`, `pip install`, git commits). Requires human approval or patch review.
   - **`DANGEROUS`**: High-risk or potentially destructive operations (e.g. file deletion, recursive remove, force push). Strongly gated behind explicit confirmation or blocked.
   - **`BLOCKED`**: Prohibited operations (e.g. directory nukes `rm -rf`, disk format, shell chaining `&&`, encoded powershell `-enc`, credential theft). Blocked unconditionally.
3. **Action Immutability & Safe Expiration**:
   - Every pending approval is bound to an immutable `action_id`, target command/arguments, risk level, and timestamp.
   - Pending actions automatically expire after 120 seconds (`_PENDING_TTL_SECONDS`).
   - Double-approval is idempotent: once approved or rejected, the pending action is permanently consumed.
4. **Pre-Write Conflict Detection**:
   - Before applying an AI-proposed patch, the system verifies that the target file's current on-disk content matches the base state (`old_code`). If an external modification is detected, the patch is rejected with a conflict error.
5. **Deterministic Undo & Reversibility**:
   - File writes, batch patches, and file deletions create automatic backup checkpoints in `action_manager.py`.
   - Irreversible actions (`NON_UNDOABLE`) are explicitly flagged and excluded from undo.

---

## 2. Multi-Modal Execution Convergence

All modalities converge on the exact same capability, safety, and approval pipeline:

```text
┌─────────────────┐   ┌─────────────────┐   ┌─────────────────┐   ┌─────────────────┐
│  Typed Chat UI  │   │  Voice (Whisper)│   │  Workspace UI   │   │   Remote API    │
└────────┬────────┘   └────────┬────────┘   └────────┬────────┘   └────────┬────────┘
         │                     │                     │                     │
         └─────────────────────┼─────────────────────┼─────────────────────┘
                               ↓
                   Canonical Request Handler
                               ↓
                        Tool Identification
                               ↓
                       Argument Validation
                               ↓
                       PolicyEngine Check
                               ↓
               ┌───────────────┴───────────────┐
             [SAFE]                 [CONFIRM / DANGEROUS]
               │                               │
               │                      Generate Action ID
               │                               │
               │                   Approval Dialog / Preview
               │                               │
               │                     User Approves/Rejects
               │                               │
               └───────────────┬───────────────┘
                               ↓
                   safe_exec / File Executor
                               ↓
                    Backup & Action Logging
                               ↓
                  Deterministic Undo Available
```
