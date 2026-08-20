# Sherly Action History & Deterministic Undo Model (Phase 11)

**Target Module**: `action_manager.py` & `tools/preview.py`  
**Classification**: Reversible State Checkpointing Engine  
**Status**: ACTIVE & PRODUCTION-READY  

---

## 1. Supported Reversible Action Types

| Action Type | Checkpoint Mechanism | Undo Behavior |
| :--- | :--- | :--- |
| **`write_file`** | Copies pre-write file content to memory/disk before overwrite. | Restores original file content on demand. |
| **`batch_write_file`** | Backs up all target files to `backups/` directory before multi-file patch application. | Reverts all affected files atomically to pre-patch state. |
| **`delete_file`** | Copies target file to `.bak` backup file before removal. | Restores file from `.bak` backup to original path. |
| **`conversation`** | Tracks last conversation context entry. | Pops recent turn from conversation memory. |
| **`NON_UNDOABLE`** | Flagged as non-reversible (shutdown, format, external API). | Excluded from undo stack with clear user message. |

---

## 2. Reversibility Verification

When the user triggers `Undo`:
1. The engine checks the most recent undoable entry on the bounded history stack (`_action_history`).
2. If the entry is non-undoable or history is empty, it returns: `"Nothing to undo — recent actions are irreversible."`
3. If undoable, it executes the restoration payload and returns the restored file list.
