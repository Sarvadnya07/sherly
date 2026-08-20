# Sherly — Delta-Only Final Gap Audit Report

**Date**: 2026-08-21  
**Audit Scope**: Post-v2.0.0 Release Delta, Unverified Claims, Stale Documentation, and Dead Code Analysis  
**Auditor**: Principal Software Auditor & Release Engineer  

---

## 1. Certified Baseline Used

The following phase reports serve as the established baseline of truth:
- **Phase 0 — 1.1**: Baseline, Dependency Modernization, and Verification Gate
- **Phase 2 — 5**: Architecture, API Contracts, Tool Execution (`ToolRegistry`, `PolicyEngine`), Multi-Model Resolver
- **Phase 6 — 9**: React Desktop Foundation, Canonical Design System, Assistant UX, Workspace & Multi-Tab Editor
- **Phase 10 — 10.1**: Voice & Realtime Engine (`sounddevice`, `faster-whisper`, `pyttsx3`, state machine)
- **Phase 11 — 13**: Safety, Approvals, Deterministic Undo, Reliability/Observability, and Security Certification
- **Phase 14 — 15**: Packaging, Schema Migration, CI/CD, and Release Candidate Certification

---

## 2. Changes Since Baseline Certification

Commits after release baseline `8397a58`:
- `66bf08b`: Bound remote API upload size limits (`10MB`) and configure agent fallback host.
- `42c0b84`: Removed shell-like app launch and replaced hardcoded path with `os.path.expanduser`.
- `cd4b264`: Hardened SSRF defense in `core/network_security.py`, modernized FastAPI lifespan handler, and expanded security regression test suite to 115 passing tests.

---

## 3. Newly Broken
- **Zero (0) Newly Broken Regressions**: All 115 tests pass cleanly; frontend Vite builds in 2.50s without errors.

---

## 4. Partially Implemented Features
1. **Remote API Authentication**: `remote_api/server.py` implements upload bounds and token placeholders, but does not yet have a multi-tenant user permission database.
2. **Tauri Native Packaging**: Frontend is fully wired with `@tauri-apps/api`, but `.deb`/`.dmg`/`.exe` bundling relies on local developer tooling or CI rather than pre-compiled binaries in git.

---

## 5. Completely Missing Features (Documented in Legacy Specs, Not in Source)
1. **Encrypted P2P Local Sync**: Documented in old `README.md` as UDP broadcast / AES sync; not implemented in the modern FastAPI / WebSocket architecture.
2. **ChromaDB Vector Store**: Replaced by lightweight SQLite conversation memory in the modern stack.
3. **Docker Sandbox Execution**: Documented in `README.md` (`Dockerfile.sandbox`); core runtime uses `safe_exec` with `shlex` and `PolicyEngine` on the host machine.

---

## 6. Unverified Claims in Documentation
1. **Cross-Platform Runtime (macOS/Linux)**: CI build is verified; physical desktop GUI runtime is verified locally on Windows only.
2. **Acoustic Auto Barge-In**: Explicit Stop/Start and manual interruption are verified; pure acoustic voice-activity barge-in during loud speaker playback is experimental.

---

## 7. Stale Documentation
1. **`README.md` Desktop UI Section**: Mentions `PySide6 / Qt6` as the desktop UI (now modernized to React + Tailwind + Vite).
2. **`README.md` Ghost Mode Path**: Mentions `python src/sherly/core/ghost_mode.py` (canonical root layout is now used).
3. **`README.md` Tech Stack Table**: Lists PySide6, ChromaDB, and Docker sandbox as core active components.

---

## 8. Dead / Obsolete Code Candidates (Static Audit)
1. **`sherly_ui/`**: Legacy PySide6 UI files kept for legacy fallback.
2. **`src/sherly/`**: Old directory structure if any leftover legacy scripts exist.
3. **`Dockerfile.sandbox`**: Legacy sandbox definition superseded by `tools/terminal_tools.py` safe execution policies.

---

## 9. Configuration Inconsistencies
1. **Model Names**: Some legacy docs mention `phi3` or `llama3`, while the canonical model resolver default is `qwen2.5-coder:3b`.
2. **Schema Versioning**: `config_manager.py` uses `CURRENT_CONFIG_SCHEMA_VERSION = 2`, whereas old `.json.example` files omitted `schema_version`.

---

## 10. Test Gaps
- **P2**: Additional unit tests for `core/network_security.py` covering IPv6 loopback edge cases.
- **P3**: E2E test for multi-tab workspace editor when opening 50+ files simultaneously.

---

## 11. Final Gap Register

| ID | Severity | Domain | File | Problem | Status | Fix Required |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **GAP-01** | **P2** | Documentation | `README.md` | Lists PySide6 instead of React desktop stack | **STALE** | Update README UI section |
| **GAP-02** | **P2** | Documentation | `README.md` | Mentions legacy P2P sync and ChromaDB | **STALE** | Align README with modern stack |
| **GAP-03** | **P3** | Codebase | `sherly_ui/` | Legacy PySide6 files | **DEAD** | Archive or mark maintenance-only |
| **GAP-04** | **P3** | Packaging | `src-tauri/` | Local bundle installer scripts | **PARTIAL**| Document manual CI packaging |

---

## 12. Three Final Lists

### A. MUST FIX (Before v2.1)
1. Update `README.md` to reflect React + Vite + FastAPI as primary desktop architecture instead of PySide6.
2. Remove obsolete ChromaDB / P2P sync claims from the introductory README sections.

### B. LEFT TO IMPLEMENT (v2.1+ Roadmap)
1. Remote API multi-tenant user authentication database.
2. Full automated multi-OS binary signing in GitHub Release workflow.

### C. STALE / DELETE CANDIDATES
1. `sherly_ui/` (legacy PySide6 UI — safe to archive into a `legacy/` folder).
2. Legacy `Dockerfile.sandbox` (if Docker-in-Docker is not required).

---

## 13. Recommended Next Actions
1. Apply targeted documentation updates to `README.md` to eliminate architecture drift.
2. Maintain v2.0.0 in frozen production maintenance mode.
