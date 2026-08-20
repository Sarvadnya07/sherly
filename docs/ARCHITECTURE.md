# Sherly AI — System Architecture & Design Specification

**Document Version**: 2.0.0  
**Classification**: Enterprise Architecture Specification  

---

## 1. High-Level Architecture Overview

Sherly unifies desktop interaction, local LLM intelligence, hardware voice capture, and safe file execution into a single cohesive system.

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

---

## 2. Key Engineering Decisions

1. **Deterministic Safety First**: Known workflows bypass LLM generation entirely via deterministic sub-routers.
2. **Server-Authoritative Security**: Client UI and model output are untrusted. The backend `PolicyEngine` determines execution permissions (`SAFE`, `CONFIRM`, `DANGEROUS`, `BLOCKED`).
3. **Pre-Write Conflict Detection**: `apply_preview` validates on-disk file hashes before applying code diffs, preventing silent overwrites.
4. **Deterministic Undo Checkpoints**: Atomic snapshots prior to destructive modifications guarantee zero data loss.
5. **Observability & Secret Redaction**: Request correlation IDs (`trace_id`, `request_id`) and regex sanitization mask credentials across all logs.
