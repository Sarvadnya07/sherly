# Sherly Assistant UX Specification (Phase 8)

**Target Surface**: `frontend/src/views/AssistantView.tsx`  
**Classification**: ChatGPT / Claude-Class Desktop Conversation Experience  
**Status**: ACTIVE & PRODUCTION-READY  

---

## 1. Core Principles

1. **Native Text Selection Integrity**: The conversation surface maintains complete native clipboard text selection without `user-select: none`. Drag selection, double-click word selection, paragraph selection, `Ctrl+A`, `Ctrl+C`, and right-click copying operate seamlessly across headings, paragraphs, lists, blockquotes, inline code, and code blocks.
2. **Context-Aware Keyboard Scoping**:
   - **`Ctrl+F`**: Activates in-conversation search across canonical message data only when the user is not actively typing inside a text input.
   - **`Ctrl+A`**: Selects text inside the composer if the composer is focused; selects selectable conversation content if the conversation view is active.
   - **`Enter`**: Submits the prompt; `Shift+Enter` inserts a newline.
   - **`Esc`**: Cancels active generation, closes conversation search, or rejects pending modal approvals.
3. **Deterministic Generation Lifecycle & Cancellation**:
   - During generation, the send button morphs into a high-contrast `Stop` button.
   - Clicking `Stop` or pressing `Esc` aborts active generation via `AbortController`, emits a cancellation signal to the backend, and reconciles the conversation state to `[Stopped]`.
4. **Transparent Tool Activity**:
   - Real-time tool execution chips display the canonical registered tool name from `ToolRegistry` (e.g., `terminal.execute`, `filesystem.read`, `web.search`) with status and cancellation support.
   - No private chain-of-thought or fabricated metadata is exposed.

---

## 2. Conversation Features & Interaction Matrix

| Feature | Interaction | Behavior |
| :--- | :--- | :--- |
| **Message Copy** | Hover over assistant response → click `Copy` | Copies exact response markdown to system clipboard with temporary `Copied` confirmation. |
| **Prompt Copy** | Hover over user message → click `Copy` | Copies exact prompt text. |
| **Prompt Edit** | Hover over user message → click `Edit` | Loads the original user prompt into the composer and focuses the textarea without silently sending. |
| **Regenerate / Retry** | Hover over assistant response → click `Retry` | Re-executes generation for that prompt without duplicating user messages. |
| **Code Block Copy** | Click `Copy` button in code header | Copies exact source code only (excluding language header). |
| **In-Conversation Search** | Press `Ctrl+F` | Scans canonical message state, highlights matched substrings, provides `X of Y` match counter, and Next/Previous navigation. |
| **Smart Auto-Scroll** | Automatic when near bottom (<80px) | Automatically follows assistant streaming; immediately pauses if user scrolls up; provides floating `Scroll to latest` button. |
| **File Attachments** | Click `Paperclip` icon | Attaches file with removable pill badge. |
| **Voice Input** | Click `Mic` icon or `Ctrl+Shift+L` | Triggers voice HUD. |

---

## 3. Keyboard Shortcuts

- `Enter`: Submit prompt (when not holding Shift)
- `Shift + Enter`: Newline in composer
- `Ctrl / Cmd + F`: Open in-conversation search (scoped)
- `Esc`: Stop active generation / Close search / Cancel modal
- `Ctrl / Cmd + A`: Select all (contextually scoped to active element)
- `Ctrl / Cmd + C`: Copy selected text
