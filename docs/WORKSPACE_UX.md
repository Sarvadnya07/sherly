# Sherly Workspace UX Specification (Phase 9)

**Target Surface**: `frontend/src/views/WorkspaceView.tsx`  
**Classification**: Professional AI-Integrated Developer Workspace  
**Status**: ACTIVE & PRODUCTION-READY  

---

## 1. Architecture & Design Principles

1. **Client & Visualization Separation**: The Workspace acts as an interactive client and visualization layer. The backend (`ToolRegistry`, `PolicyEngine`, `ActionManager`) remains authoritative for all filesystem operations, command execution, and patch applications.
2. **Multi-Tab Workspace State**:
   - Multiple open file tabs with active tab highlighting and dirty state tracking (`●`).
   - `Ctrl+S` writes changes atomically to the backend and clears the dirty flag.
   - `Ctrl+W` closes the active tab.
3. **Safe Patch Diff & Review**:
   - AI-proposed code modifications are rendered as clear diffs highlighting additions (`+` green) and deletions (`-` red).
   - Modifications are never applied silently: users must review and explicitly Accept (`Ctrl+Enter`) or Reject (`Esc`).
   - External file changes are detected before writing to prevent silent overwrite conflicts.
4. **Deterministic Terminal & Output Protection**:
   - Terminal execution routes through `safe_exec` with whitelist/blacklist policy verification.
   - Command history navigation (Up/Down arrow keys) remembers previously typed commands.
   - Output buffer is capped at 400 lines to prevent DOM bloat and preserve high-DPI rendering performance.
5. **Deterministic Undo & Reversibility**:
   - Every file modification logs reversible backup checkpoints in `ActionManager`.
   - The `Undo` action restores previous file states with zero data loss.

---

## 2. Workspace Interaction Matrix

| Area | Interaction | Behavior |
| :--- | :--- | :--- |
| **Explorer** | Click file in sidebar tree | Opens file in a new or existing tab in the Workspace; activates Workspace view. |
| **Tabs** | Click tab header | Activates tab, loads content, synchronizes line numbers. |
| **Close Tab** | Click `X` on tab or `Ctrl+W` | Closes tab and focuses neighboring tab. |
| **Editor** | Monospace textarea | Line numbers in gutter; tracks cursor position `Ln X, Col Y`; tracks dirty state. |
| **Save** | `Save` button or `Ctrl+S` | Validates path, sends atomic write request, clears dirty dot (`●`). |
| **Diff Mode** | Triggered by preview/patch | Shows additions/deletions; provides `Accept` (`Ctrl+Enter`) and `Reject` (`Esc`). |
| **Terminal** | Input prompt + Up/Down arrows | Safe CLI execution; displays exit code; clear action. |
| **Undo** | Click `Undo` button | Calls `/api/actions/undo` to restore previous file state. |

---

## 3. Keyboard Shortcuts

- `Ctrl / Cmd + S`: Save active file
- `Ctrl / Cmd + W`: Close active tab
- `Ctrl / Cmd + Enter`: Accept AI patch diff (in diff preview mode)
- `Esc`: Reject AI patch diff / close dialogs
- `Arrow Up / Down`: Navigate command history in terminal prompt
