# Sherly Final End-to-End Test Plan & Validation Protocols (Phase 15)

**Target Scope**: Comprehensive 24-Point Acceptance Gate Protocol  
**Status**: COMPLETED & VERIFIED  

---

## 1. User Journey Verification Matrix

| # | User Journey | Target Capability | Verification Method | Result |
| :--- | :--- | :--- | :--- | :--- |
| **A** | **First Run & Startup** | Clean launch when Ollama offline | `main.py` launches safely without model crash. | **PASS** |
| **B** | **Text Assistant** | Conversational chat & markdown | Model streams response with code block formatting. | **PASS** |
| **C** | **Structured Tool Call** | `filesystem.read` & `terminal.execute` | Structured JSON tool call dispatched and synthesized. | **PASS** |
| **D** | **Safety Approval Gate** | Sensitive command confirmation | UI Approval modal appears; Enter to approve / Esc to reject. | **PASS** |
| **E** | **Workspace Multi-Tab** | File editing with dirty indicator | Files open in tabs, track cursor line/column and `●` dirty state. | **PASS** |
| **F** | **Diff Review & Apply** | Visual patch diff preview | Displays line additions/deletions; applies patch cleanly. | **PASS** |
| **G** | **Conflict Detection** | External file modification | Refuses silent overwrite if file changed externally. | **PASS** |
| **H** | **Deterministic Undo** | Restore original file | Reverts file modifications from pre-state backup snapshot. | **PASS** |
| **I** | **Voice Modality** | STT, TTS, and HUD | Transcribes audio via Whisper; synthesizes via pyttsx3; cancels on Esc. | **PASS** |
| **J** | **Model Switching** | Auto vs Manual / Pinned mode | Pinned model locks mode to manual without auto-override. | **PASS** |
| **K** | **Observability & Tracing**| Correlation IDs & log redaction | Propagates `trace_id`/`request_id`; redacts `sk-...` API keys. | **PASS** |
| **L** | **Resilience & Breakers** | Circuit breakers & backoff | Trips breaker on consecutive errors; avoids retry storms. | **PASS** |
| **M** | **Schema Migration** | v1 to v2 config upgrade | Automatically upgrades schema and creates `config.json.bak`. | **PASS** |
| **N** | **Graceful Teardown** | Process exit cleanup | Releases audio hardware and background threads on exit. | **PASS** |
