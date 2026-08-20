# Sherly AI — Release Candidate Specification (v2.0.0-rc1)

**Release Version**: `2.0.0-rc1`  
**Git Commit**: `656934c`  
**Classification**: Production Release Candidate  
**Status**: ACTIVE & CERTIFIED  

---

## 1. System Architecture Summary

Sherly is a modern, privacy-first, desktop AI copilot with unified multi-modal capabilities across four integrated pillars:

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

## 2. Release Integrity & Verification

- **Backend Test Suite**: 109/109 tests passing (`pytest tests/ -q`).
- **Frontend Production Bundle**: Built via Vite in 2.50s (`dist/index.html`, CSS, JS).
- **Release Manifest**: `release/release_manifest.json` containing SHA-256 asset hashes.
- **Platform Matrix**:
  - **Windows (x86_64)**: `BUILD VERIFIED | INSTALL VERIFIED | RUNTIME VERIFIED`
  - **macOS (Universal)**: `BUILD VERIFIED (CI) | NOT TESTED`
  - **Linux (x86_64)**: `BUILD VERIFIED (CI) | NOT TESTED`
