# Sherly AI — Canonical Architecture Specification

**Specification Version**: 2.0.0 (Canonical Modernization Target)  
**Status**: APPROVED & LOCKED (Phase 2)  
**Classification**: Production Architecture & System Boundaries  

---

## 1. High-Level Architectural Topology

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          DESKTOP CLIENT INTERFACE                           │
│     React 18 + TypeScript + Vite + Tailwind CSS (Tauri 2 / WebView2)        │
│     • Atomic UI State (Zustand)                                             │
│     • Markdown & Codeblock Rendering                                        │
│     • In-Conversation Search & Workspace Navigation                         │
│     • Native Text Selection & Keyboard Command Palette                      │
└──────────────────────────────────────┬──────────────────────────────────────┘
                                       │ Typed REST (/api/*) & WebSockets (/ws)
                                       ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                          FASTAPI APPLICATION LAYER                          │
│     • Typed Contract Validation (Pydantic v2 Contracts)                     │
│     • Route Endpoints: /chat, /models, /voice, /files, /actions, /settings  │
│     • Real-time Event Broadcaster (ConnectionManager)                       │
│     • CORS & Security Isolation Middleware                                  │
└──────────────────────────────────────┬──────────────────────────────────────┘
                                       │
                                       ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                             SHERLY CORE ENGINE                              │
│  ┌─────────────────────────┬─────────────────────────┬───────────────────┐  │
│  │   MODEL ORCHESTRATION   │     AGENT DISPATCH      │   MEMORY BRAIN    │  │
│  │ • Model Resolver (Auto) │ • Intent Classifier     │ • SQLite Memory   │  │
│  │ • Ollama / Cloud HTTPX  │ • Command Router        │ • Session Context │  │
│  │ • Circuit Breakers      │ • Subsystem Handlers    │ • Background Info │  │
│  │ • Single Model Lock     │ • Plugin Dispatcher     │ • Auto Pruning    │  │
│  └─────────────────────────┴─────────────────────────┴───────────────────┘  │
│                                      │                                      │
│                                      ▼                                      │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │                         POLICY & SAFETY LAYER                         │  │
│  │ • Safety Guard Pattern Matcher (Safe / Confirm / Dangerous)           │  │
│  │ • Action Approval Queue & Confirmation State Machine                  │  │
│  │ • Code Preview Store & Visual Diff Generator                          │  │
│  │ • Undo Stack & Rollback Engine                                        │  │
│  └───────────────────────────────────┬───────────────────────────────────┘  │
│                                      │                                      │
│                                      ▼                                      │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │                         SAFE EXECUTION LAYER                          │  │
│  │ • Terminal Tools (safe_exec: Prefix Whitelist + shell=False)          │  │
│  │ • File Tools (Workspace Boundary Enforcement + Size Guard)            │  │
│  │ • Search Engine (ddgs Web Search with Timeout & Fallback)             │  │
│  │ • Voice Engine (faster-whisper STT + pyttsx3 Sync TTS)                │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Core Responsibility & Authority Boundaries

### Boundary 1: React / Tauri Frontend Client
* **Responsibility**: Pure presentation, user input capture, syntax highlighting, diff display, real-time telemetry rendering.
* **Constraints**:
  - Contains **zero business logic**, **zero shell execution**, and **zero secret credentials**.
  - Communicates exclusively via typed REST (`/api/*`) and WebSocket (`/ws`) endpoints.

### Boundary 2: FastAPI API Layer
* **Responsibility**: Request schema validation, error translation, WebSocket connection lifecycle, and event broadcasting.
* **Contracts**: Defined in [`backend/api/schemas/contracts.py`](file:///c:/Users/ASUS/Desktop/STUDY/PROJECTS/sherly/backend/api/schemas/contracts.py), strictly mirrored in [`frontend/src/types/api.ts`](file:///c:/Users/ASUS/Desktop/STUDY/PROJECTS/sherly/frontend/src/types/api.ts).

### Boundary 3: Model Authority & Resolution
* **Authority**: [`sherly_core/model_resolver.py`](file:///c:/Users/ASUS/Desktop/STUDY/PROJECTS/sherly/sherly_core/model_resolver.py) + [`model_scanner.py`](file:///c:/Users/ASUS/Desktop/STUDY/PROJECTS/sherly/model_scanner.py).
* **Guarantees**:
  - Dynamically discovers local Ollama models (`qwen2.5-coder`, `llama3`, `deepseek-r1`, etc.).
  - Resolves optimal coding/reasoning models automatically when set to `AUTO` mode.
  - Model names are **never hardcoded**.
  - Single-model mutex lock ensures only one local model resides in VRAM at any time, with automatic idle unloading after 120 seconds.

### Boundary 4: Safety, Approvals & Policy Layer
* **Authority**: [`safety_guard.py`](file:///c:/Users/ASUS/Desktop/STUDY/PROJECTS/sherly/safety_guard.py) + [`action_manager.py`](file:///c:/Users/ASUS/Desktop/STUDY/PROJECTS/sherly/action_manager.py).
* **Guarantees**:
  - All command and tool invocations must pass through risk classification:
    1. `SAFE`: Executed immediately.
    2. `CONFIRM`: Enqueued in `PendingApproval` queue requiring explicit user approval (`/approve` / `approve <id>`).
    3. `DANGEROUS`: Hard blocked with visible security explanation.
  - Zero bypass: No raw terminal runner or agent can bypass the safety policy.

### Boundary 5: Execution Layer
* **Authority**: [`tools/terminal_tools.py`](file:///c:/Users/ASUS/Desktop/STUDY/PROJECTS/sherly/tools/terminal_tools.py) + [`tools/file_tools.py`](file:///c:/Users/ASUS/Desktop/STUDY/PROJECTS/sherly/tools/file_tools.py).
* **Guarantees**:
  - `safe_exec` validates commands against the allowed prefix whitelist (`python`, `git`, `npm`, `pytest`, `uvicorn`, `ollama`, etc.).
  - Blocks command chaining operators (`&`, `;`, `|`, newline).
  - Uses `subprocess.run(argv, shell=False)` with a 30-second timeout.
  - File operations enforce workspace root boundaries via path resolution (`is_relative_to`) and 5MB size limits.

### Boundary 6: Memory Authority
* **Authority**: [`memory.py`](file:///c:/Users/ASUS/Desktop/STUDY/PROJECTS/sherly/memory.py) (short-term conversation turns) + [`memory_brain.py`](file:///c:/Users/ASUS/Desktop/STUDY/PROJECTS/sherly/memory_brain.py) (long-term developer profile).
* **Storage**: SQLite local database (`sherly_memory.db`) and JSON storage.

### Boundary 7: Voice Pipeline
* **Speech-to-Text**: [`speech_to_text.py`](file:///c:/Users/ASUS/Desktop/STUDY/PROJECTS/sherly/speech_to_text.py) using `faster-whisper` (int8 quantized).
* **Text-to-Speech**: [`text_to_speech.py`](file:///c:/Users/ASUS/Desktop/STUDY/PROJECTS/sherly/text_to_speech.py) using `pyttsx3` with mutual exclusion flag (`mark_speaking`) to prevent mic audio feedback.

### Boundary 8: Remote & Secondary Access
* **Authority**: [`remote_api/server.py`](file:///c:/Users/ASUS/Desktop/STUDY/PROJECTS/sherly/remote_api/server.py) + [`remote_agent/agent.py`](file:///c:/Users/ASUS/Desktop/STUDY/PROJECTS/sherly/remote_agent/agent.py).
* **Guarantees**: Routes all requests through canonical `route_command` with mandatory `SHERLY_REMOTE_API_KEY` verification using constant-time comparison (`secrets.compare_digest`).

### Boundary 9: Transitional PySide6 UI
* **Status**: Transitional desktop client in [`sherly_ui/`](file:///c:/Users/ASUS/Desktop/STUDY/PROJECTS/sherly/sherly_ui).
* **Policy**: Shares identical underlying `sherly_core` and backend services without divergent business logic.

---

## 3. Real-Time WebSocket Event Envelope Specification

All WebSocket telemetry transmitted on `ws://127.0.0.1:8000/ws` adheres to the canonical event envelope:

```json
{
  "event_type": "status | stt_text | action_update | model_changed | pong",
  "payload": {
    "status": "ready | thinking | listening",
    "prompt": "optional user prompt string",
    "current_model": "optional active model name",
    "action_id": "optional action id string"
  }
}
```

---

## 4. Architectural Verification Matrix

| Subsystem | Canonical Authority | Verification Mechanism | Status |
| :--- | :--- | :--- | :--- |
| **Client UI** | React 18 + Tauri 2 | Production Vite Build | **LOCKED** |
| **API Endpoints** | FastAPI (`backend/main.py`) | Pydantic v2 Contracts | **LOCKED** |
| **Model Resolution** | `sherly_core/model_resolver.py` | Auto Tag Scanner | **LOCKED** |
| **Safety & Approvals** | `safety_guard.py` + `action_manager.py` | Policy Gate Tests | **LOCKED** |
| **Subprocess Execution** | `tools/terminal_tools.py` (`safe_exec`) | Prefix Whitelist + `shell=False` | **LOCKED** |
| **Memory** | `memory.py` + `memory_brain.py` | SQLite WAL Storage | **LOCKED** |
| **Web Search** | `web_search.py` (`ddgs`) | Timeout + Fallback | **LOCKED** |
