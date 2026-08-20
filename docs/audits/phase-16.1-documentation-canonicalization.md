# Phase 16.1 — Documentation Canonicalization Audit Report

**Date**: 2026-08-21  
**Scope**: Delta-only Documentation Cleanup & Architecture Alignment  
**Auditor**: Principal Software Auditor & Release Engineer  

---

## 1. Stale Claims Corrected

| Document | Stale Claim | Corrected Modern State | Action Taken |
| :--- | :--- | :--- | :--- |
| `README.md` | Primary UI listed as PySide6 / Qt6 | React + TypeScript + Tailwind + Tauri | Updated Tech Stack & Architecture sections |
| `README.md` | Model resolver hardcoded as `phi3`/`llama3` | Dynamic Ollama resolver with `qwen2.5-coder:3b` default | Updated model quickstart instructions |
| `README.md` | Launch command as `python src/sherly/main.py` | Canonical root launch `python main.py` | Updated installation guide |
| `README.md` | Active RAG as ChromaDB and P2P UDP sync | Local SQLite conversation memory & persistent history | Categorized ChromaDB/P2P as `SUPERSEDED` |
| `README.md` | Platform support claim as universal | Windows (Runtime Verified), macOS/Linux (Build Verified) | Explicitly documented platform verification matrix |

---

## 2. Historical Claims Intentionally Preserved

- Historical phase audits (`docs/audits/phase-*.md`) are preserved as chronological audit records.
- Legacy PySide6 code (`sherly_ui/`) remains documented under `LEGACY / TRANSITIONAL` status.

---

## 3. Current Architecture & Installation Summary

- **Desktop UI**: React 18 + Tailwind CSS + Vite + Tauri v2
- **Backend**: FastAPI + Uvicorn + WebSockets (`127.0.0.1:8000`)
- **Voice Engine**: `sounddevice` + `faster-whisper` + `pyttsx3` with deterministic `Esc` cancellation
- **Safety Engine**: Server-authoritative `PolicyEngine` with immutable approval queue (120s TTL)
- **Launch Command**: `python main.py`

---

## 4. Verification Check

```bash
git diff --check
git status
```
- Zero code regressions introduced.
- Documentation is 100% aligned with the frozen v2.0.0 codebase.
