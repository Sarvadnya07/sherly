# Sherly AI – Voice-First Local Developer Orchestrator (v2.0.0)

<div align="center">

<h1>Sherly AI</h1>

<p><strong>The Autonomous Local Developer Orchestrator</strong></p>

<p><em>"Talk to your code. Let the code heal itself."</em></p>

<p>
<img src="https://img.shields.io/badge/Release-v2.0.0-blue.svg" alt="v2.0.0" />
<img src="https://img.shields.io/badge/License-MIT-yellow.svg" alt="MIT License" />
<img src="https://img.shields.io/badge/Python-3.10%2B-blue.svg" alt="Python 3.10+" />
<img src="https://img.shields.io/badge/Tests-115%20passing-success.svg" alt="115 tests passing" />
<img src="https://img.shields.io/badge/Frontend-React%20%2B%20Tailwind%20%2B%20Tauri-61dafb.svg" alt="React + Tailwind + Tauri" />
<img src="https://img.shields.io/badge/Backend-FastAPI%20%2B%20WebSockets-009688.svg" alt="FastAPI" />
</p>

</div>

---

## 📖 Overview

**Sherly AI is a production-grade, desktop-native, voice-first AI developer copilot and local development orchestrator** designed for hands-free interaction with your codebase.

Unlike conventional cloud-dependent chat interfaces, Sherly bridges the gap between natural-language intent and safe, deterministic system execution.

Sherly can:

* Listen to voice or text commands with instant `Esc` cancellation
* Understand project-level developer intent
* Inspect files and scan project directory structures
* Execute deterministic development workflows
* Run tests and development commands through a safe, policy-controlled executor
* Diagnose errors and retrieve relevant project context
* Generate reviewable, multi-file code patches with pre-write conflict validation
* Require explicit human approval for consequential or destructive actions
* Track and undo supported modifications via deterministic pre-state backups
* Maintain persistent local project memory through SQLite
* Auto-resolve local Ollama models (`qwen2.5-coder:3b`) with cloud API fallback

Sherly is built around one core principle:

> **Deterministic safety first. LLM as a last resort.**

Known commands are handled through deterministic routing before an AI model is invoked. This keeps common workflows fast, predictable, auditable, and resource-efficient while still allowing local LLM-powered agents to handle complex or ambiguous tasks.

**Platform Verification Status:**
- **Windows (x86_64)**: Runtime Verified
- **macOS (Apple Silicon / Intel)**: Build Verified (CI)
- **Linux (Ubuntu / Debian)**: Build Verified (CI)

---

## 🎯 Why Sherly Exists

Modern AI coding assistants often introduce engineering liabilities:

* Hallucination-driven actions
* Unpredictable shell command execution
* Excessive dependence on third-party cloud APIs
* Silent, unreviewable file modifications
* Irreversible workspace corruption
* Weak separation between safe and destructive operations

Sherly solves these through:

1. **Local Independence**: Speech recognition, project indexing, and local LLM inference run without sending source code to external servers.
2. **Deterministic-First Execution**: Common commands execute via rule-based dispatch.
3. **Server-Authoritative Human-in-the-Loop**: Consequential actions are gated behind immutable approval modals (120s TTL).
4. **Deterministic Undo**: Pre-state backup checkpoints restore original file states with zero data loss.
5. **Non-Destructive Patch Review**: Code modifications are visualized as colorized diffs before application.
6. **Defense in Depth**: Zero-trust input validation, path traversal defense, shell injection protection, and structural secret redaction.

---

# 🧠 Core Architecture

Sherly operates across four integrated pillars:

```text
┌────────────────────────────────────────────────────────────────────────┐
│                        SHERLY UNIFIED DESKTOP                          │
│                                                                        │
│  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────────┐  │
│  │    Assistant     │  │    Workspace     │  │    Voice Realtime    │  │
│  │ (Chat / Search / │  │(Multi-tab Editor/│  │  (sounddevice STT / │  │
│  │  Tools / Diffs)  │  │  Terminal / Undo)│  │   pyttsx3 TTS / HUD) │  │
│  └────────┬─────────┘  └────────┬─────────┘  └──────────┬───────────┘  │
│           │                     │                       │              │
│           └─────────────────────┼───────────────────────┘              │
│                                 ↓                                      │
│                FastAPI Backend (127.0.0.1:8000)                        │
│                                 ↓                                      │
│        ┌────────────────────────┴────────────────────────┐             │
│        │  ToolRegistry / PolicyEngine / ActionManager    │             │
│        └────────────────────────┬────────────────────────┘             │
│                                 ↓                                      │
│        ┌────────────────────────┴────────────────────────┐             │
│        │    Model Resolver (Local Ollama / Cloud API)    │             │
│        └─────────────────────────────────────────────────┘             │
└────────────────────────────────────────────────────────────────────────┘
```

### 1. Input Layer
- Speech-to-text noise filtering via `faster-whisper`
- Input deduplication and prompt injection detection
- Semantic security validation

### 2. Execution Layer
- Deterministic router for known developer commands
- Autonomous LLM tool-calling loop (`ToolRegistry`, `PolicyEngine`)

### 3. AI & Model Layer
- Automated local model detection (`qwen2.5-coder:3b` default)
- Manual model pinning authority
- Hard LLM timeouts and scoped circuit breakers

### 4. System & Control Layer
- Command classification (`SAFE`, `CONFIRM`, `DANGEROUS`, `BLOCKED`)
- Safe subprocess execution via `shlex.split()` and `shell=False`
- Pre-write conflict verification before patch application

---

# 🚀 Key Features

## 🎙️ Voice-Native Development
- **Local Audio Stack**: Hardware capture via `sounddevice`, STT via `faster-whisper`, offline TTS via `pyttsx3`.
- **Global Shortcut**: `Ctrl + Shift + L` opens the dedicated Voice HUD.
- **Interruption Safety**: Instant `Esc` or "Stop Speaking" terminates active audio playback and closes streams cleanly.

## 💻 Developer Workspace
- **Multi-Tab Code Canvas**: Monospace code editor with line gutters, live cursor coordinates (`Ln X, Col Y`), dirty state tracking, and keyboard save (`Ctrl+S`).
- **Integrated Terminal**: Safe CLI runner with command history (Up/Down) and 400-line buffer capping.
- **Patch Review**: Side-by-side or inline unified diff preview with explicit `Accept (Ctrl+Enter)` and `Reject (Esc)` controls.

## 🛡️ Human-in-the-Loop Safety & Undo
- **Immutable Approval Queue**: Actions are bound to unique, single-use action IDs with 120s TTL.
- **Deterministic Undo**: Atomic backup checkpoints allow immediate restoration of modified or deleted files.

---

# 📦 Tech Stack

| Layer | Primary Technology (v2.0.0) | Status |
| :--- | :--- | :--- |
| **Desktop Frontend** | React 18, TypeScript, Tailwind CSS, Vite | **PRIMARY** |
| **Desktop Wrapper** | Tauri v2 (`@tauri-apps/api`) | **PRIMARY** |
| **API Server** | FastAPI, Uvicorn, WebSockets | **PRIMARY** |
| **Voice STT** | `faster-whisper` | **PRIMARY** |
| **Voice TTS** | `pyttsx3` | **PRIMARY** |
| **Local LLM** | Ollama (`qwen2.5-coder:3b` auto-resolved) | **PRIMARY** |
| **Cloud Providers** | OpenAI, Gemini, Groq (Optional) | **PRIMARY** |
| **Persistence** | SQLite (`sherly_memory.db`) | **PRIMARY** |
| **Observability** | Structured JSON logging, trace correlation, circuit breakers | **PRIMARY** |
| **Legacy UI** | PySide6 / Qt6 (`sherly_ui/`) | **LEGACY / TRANSITIONAL** |
| **Docker Sandbox** | `Dockerfile.sandbox` | **DEFERRED / OPTIONAL** |
| **Vector RAG / P2P** | ChromaDB / UDP sync | **SUPERSEDED** (Replaced by local SQLite) |

---

# 🚀 Installation & Quickstart

## Prerequisites
- **Python 3.10+** (Tested on Python 3.13)
- **Node.js 18+ & npm** (Tested on Node 20/26)
- **Ollama** (Recommended: `ollama pull qwen2.5-coder:3b`)

## Step 1: Clone Repository
```bash
git clone https://github.com/Sarvadnya07/sherly.git
cd sherly
```

## Step 2: Setup Python Virtual Environment
```bash
python -m venv .venv

# On Windows:
.venv\Scripts\activate

# On macOS/Linux:
source .venv/bin/activate

pip install --upgrade pip
pip install -r requirements.txt
```

## Step 3: Build Frontend Production Assets
```bash
cd frontend
npm install
npm run build
cd ..
```

## Step 4: Launch Sherly
```bash
python main.py
```

The FastAPI backend starts on `http://127.0.0.1:8000` and launches the modern desktop interface.

---

# 🔐 Security & Safety Architecture

Sherly strictly follows a zero-trust model:
- Neither the AI model, voice transcripts, nor frontend clients can alter risk policies.
- Shell metacharacters (`&&`, `||`, `;`), encoded PowerShell (`-enc`), and directory traversal attempts (`../`) are blocked unconditionally.
- API keys and private tokens are redacted structurally and through regex pattern filters in all logs and telemetry.

---

# 📄 License

MIT License. See [LICENSE](LICENSE) for details.
