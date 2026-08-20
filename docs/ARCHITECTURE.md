# Sherly AI — Complete Architecture Specification

**Target Version**: 2.0.0  
**Classification**: Enterprise Architecture & System Topology Specification  
**Status**: ACTIVE & VERIFIED  

---

## 1. Executive System Topology (C4 Level 1 & 2)

Sherly is structured as an asynchronous, event-driven local developer orchestrator. It couples hardware voice pipelines, local LLM inference engines, and a zero-trust AST execution sandbox into a unified developer environment.

```mermaid
graph TD
    classDef clientNode fill:#1e293b,stroke:#3b82f6,stroke-width:2px,color:#f8fafc;
    classDef serverNode fill:#1e1b4b,stroke:#6366f1,stroke-width:2px,color:#f8fafc;
    classDef engineNode fill:#0f172a,stroke:#475569,stroke-width:1px,color:#cbd5e1;
    classDef storageNode fill:#18181b,stroke:#52525b,stroke-width:1px,color:#e4e4e7;

    subgraph Clients["🖥️ User Interface Tier"]
        W["🌐 React 18 + Vite (+ Tauri Shell)<br/>(PRIMARY Desktop & Web Workspace)"]:::clientNode
        Q["💻 PySide6 Qt Desktop HUD<br/>(Transitional / Legacy Maintenance)"]:::clientNode
        P["📱 Remote PWA Companion<br/>(Mobile Audio & Uploads)"]:::clientNode
    end

    subgraph CoreServer["⚡ Application Tier (FastAPI Lifespan Hub)"]
        API["🚀 FastAPI REST & WebSocket Router<br/>(127.0.0.1:8000)"]:::serverNode
        FW["🛡️ IntentFirewall & InputValidator"]:::serverNode
        CR{"🧭 CommandRouter"}:::serverNode
        SG{"🛡️ SafetyGuard (PolicyEngine)"}:::serverNode
        SE["⚡ SandboxExecutor (shlex + shell=False)"]:::serverNode
    end

    subgraph Engines["🧠 Intelligence & Hardware Tier"]
        OLLAMA["🦙 Ollama Local Inference<br/>(qwen2.5-coder:3b)"]:::engineNode
        CLOUD["☁️ Cloud LLMs (Gemini / OpenAI / Groq)<br/>(Circuit Breaker Protected)"]:::engineNode
        AUDIO["🎙️ faster-whisper (STT) + pyttsx3 (TTS)<br/>+ pvporcupine (Wake Word)"]:::engineNode
    end

    subgraph Persistence["💾 Storage Tier"]
        DB["🗄️ SQLite WAL (sherly_memory.db)<br/>(Action Ledger & Context)"]:::storageNode
        BAK["📁 backups/ (Pre-State Snapshots)"]:::storageNode
    end

    W <==>|"HTTP / WebSocket"| API
    Q <==>|"PortAudio / Local IPC"| API
    P <==>|"HTTPS Bearer Auth"| API

    API --> FW --> CR
    CR --> SG --> SE
    CR -.->|"Inference"| OLLAMA
    CR -.->|"Fallback"| CLOUD
    CR <--> AUDIO

    SE --> DB
    SE --> BAK
```

---

## 2. Component Routing & Policy Architecture (C4 Level 3)

```mermaid
flowchart TD
    classDef inputNode fill:#1e293b,stroke:#3b82f6,stroke-width:2px,color:#f8fafc;
    classDef firewallNode fill:#334155,stroke:#64748b,stroke-width:1px,color:#f8fafc;
    classDef routerNode fill:#1e1b4b,stroke:#6366f1,stroke-width:2px,color:#f8fafc;
    classDef subRouter fill:#0f172a,stroke:#475569,stroke-width:1px,color:#cbd5e1;
    classDef guardNode fill:#312e81,stroke:#818cf8,stroke-width:2px,color:#f8fafc;
    classDef statusReject fill:#881337,stroke:#f43f5e,stroke-width:2px,color:#ffe4e6;
    classDef statusConfirm fill:#713f12,stroke:#eab308,stroke-width:2px,color:#fef08a;
    classDef statusExec fill:#064e3b,stroke:#10b981,stroke-width:2px,color:#d1fae5;
    classDef storageNode fill:#18181b,stroke:#52525b,stroke-width:1px,color:#e4e4e7;
    classDef outputNode fill:#172554,stroke:#38bdf8,stroke-width:2px,color:#f0f9ff;

    IN["🎙️ Voice / Text Input"]:::inputNode --> FW["🛡️ Intent Firewall"]:::firewallNode
    
    FW -- "BLOCKED" --> REJ["🚫 Rejected"]:::statusReject
    FW --> IV["🔍 Input Validator"]:::firewallNode
    
    IV --> CR{"🧭 Command Router"}:::routerNode
    
    CR -- "Known Command" --> DH["⚡ Deterministic Handlers"]:::subRouter
    CR -- "File Ops" --> FR["📂 File Router"]:::subRouter
    CR -- "Dev Ops" --> DR["🛠️ Dev Router"]:::subRouter
    CR -- "System Ops" --> SR["💻 System Router"]:::subRouter
    CR -- "Unknown Intent" --> LLM["🤖 LLM Agents (Coder/Browser/Sys)"]:::subRouter
    
    DH --> SG{"🛡️ Safety Guard (Pillar 5)"}:::guardNode
    FR --> SG
    DR --> SG
    SR --> SG
    LLM --> SG
    
    SG -- "DANGEROUS" --> REJ
    SG -- "CONFIRM" --> AQ["⏳ Approval Queue (120s TTL)"]:::statusConfirm
    AQ -- "Approved" --> SE["⚡ Sandbox Executor (shlex + shell=False)"]:::statusExec
    SG -- "SAFE" --> SE
    
    SE --> AH["💾 Action History / SQLite Brain"]:::storageNode
    AH --> RES["🔊 Response + TTS Audio"]:::outputNode
```

---

## 3. Concurrency, State & Memory Model

1. **Active-Model Lock**: A thread-safe `threading.Lock` in `model_manager.py` prevents concurrent multi-model VRAM loading.
2. **Idle VRAM Unloader**: A background daemon thread releases GPU memory via Ollama `keep_alive: 0` after 120 seconds of inactivity.
3. **SQLite WAL Concurrency**: `sherly_memory.db` executes with `PRAGMA journal_mode=WAL` and `PRAGMA synchronous=NORMAL`, allowing non-blocking concurrent readers during active background writes (14,184 ops/sec).
4. **WebSocket Stream Coalescing**: Token stream chunks are coalesced at 60 FPS (~16ms/frame) via `requestAnimationFrame` before React state commit.

---

## 4. Multi-Modal Execution Convergence

All user interfaces (React Workspace, Native PySide6 Qt HUD, and Remote PWA Companion) converge on the exact same backend policy engine:

```text
┌─────────────────┐   ┌─────────────────┐   ┌─────────────────┐
│  React 18 UI    │   │  PySide6 Qt HUD │   │  Remote PWA     │
└────────┬────────┘   └────────┬────────┘   └────────┬────────┘
         │                     │                     │
         └─────────────────────┼─────────────────────┘
                               ↓
                   Canonical Request Router
                               ↓
                       Input Sanitization
                               ↓
                       PolicyEngine Check
                               ↓
                ┌──────────────┴──────────────┐
              [SAFE]                 [CONFIRM / DANGEROUS]
                │                              │
                │                     Generate Action ID
                │                              │
                │                  Approval Dialog / Preview
                │                              │
                │                    User Approves/Rejects
                │                              │
                └──────────────┬───────────────┘
                               ↓
                   safe_exec (shell=False)
                               ↓
                    Backup & SQLite Logging
```
