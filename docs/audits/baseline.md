# SHERLY AI — PHASE 0: GOLDEN BASELINE & REPOSITORY AUDIT

**Audit Timestamp:** 2026-08-19T19:40:00+05:30  
**Phase:** PHASE 0 — Golden Baseline & Repository Freeze  
**Auditor Role:** Principal Software Architect, Release Engineer & DevSecOps Engineer  
**Policy:** READ-ONLY AUDIT. Zero modifications, zero package updates, zero refactorings applied.

---

## 1. Git Baseline
| Parameter | Value | Status |
| :--- | :--- | :--- |
| **Current Branch** | `main` | PASS |
| **HEAD Commit SHA** | `f7f854dede4c2c6fb42ee948b67e011ca4bfd08a` | PASS |
| **origin/main SHA** | `2bc64cfd3934f98b25c2f63e5b9841c4f4e8c3b1` | PASS |
| **Ahead/Behind State** | Ahead of origin/main by 4 commits | AUDITED |
| **Uncommitted Changes** | Working tree clean except local working changes | AUDITED |
| **Latest Commit Message** | `feat: Enhance Dynamic Developer Workspace UI and add new components` | PASS |

---

## 2. Repository Inventory & Directory Classification
| Directory Path | Category | Purpose / Description |
| :--- | :--- | :--- |
| `frontend/` | **ACTIVE** | Canonical React 18 + TypeScript + Vite + Tailwind CSS desktop UI. |
| `backend/` | **ACTIVE** | FastAPI REST & WebSocket server (`backend/main.py`). |
| `sherly_core/` | **ACTIVE** | Model Resolver, Ollama dynamic discovery, agent orchestration. |
| `tools/` | **ACTIVE** | Desktop automation, terminal tools, safety guard, error fixer. |
| `agents/` | **ACTIVE** | Task classifier, planner, multi-agent manager. |
| `core/` | **ACTIVE** | Core utilities, runtime configs, memory brain. |
| `sherly_ai/` | **ACTIVE** | System prompts, model manager orchestration. |
| `sherly_commands/` | **ACTIVE** | Command mapping and action dispatcher. |
| `tests/` | **ACTIVE** | Pytest automated test suite (81 tests). |
| `docs/` | **ACTIVE** | UI design system specs and architectural documentation. |
| `sherly_ui/` | **TRANSITIONAL** | Legacy PySide6 (Qt6) desktop window and widgets. |
| `src-tauri/` | **NOT PRESENT** | Tauri client configured via `@tauri-apps/api` in `frontend/`. |

---

## 3. Runtime Environment & Toolchain
| Tool / Runtime | Declared Version | Actual Resolved Version | Status |
| :--- | :--- | :--- | :--- |
| **Python** | `>=3.10` | `3.13.9` (64-bit Windows) | PASS |
| **Pip** | N/A | `25.0.1` | PASS |
| **Node.js** | `>=18` | `v26.2.0` | PASS |
| **NPM** | N/A | `11.6.2` | PASS |
| **Rust Compiler** | N/A | `rustc 1.97.1` | PASS |
| **Cargo** | N/A | `cargo 1.97.1` | PASS |
| **Ollama Engine** | N/A | `0.32.14` | PASS |

---

## 4. Python Package Baseline (Key Dependencies)
| Package | Installed Version | Role in Sherly | Baseline Status |
| :--- | :--- | :--- | :--- |
| `fastapi` | `0.115.x` | Core REST API framework | PASS |
| `uvicorn` | `0.52.4` | ASGI server | PASS |
| `pydantic` | `2.13.4` | Schema validation & serialization | PASS |
| `httpx` | `0.28.1` | Async HTTP/2 client | PASS |
| `requests` | `2.34.2` | Sync HTTP client (marked for consolidation) | PASS |
| `numpy` | `2.2.x` | Audio DSP and numerical buffers | PASS |
| `sounddevice` | `0.5.5` | PortAudio low-latency voice capture | PASS |
| `faster-whisper`| `1.1.1` | Local quantized Whisper speech-to-text | PASS |
| `pyttsx3` | `2.99` | Local offline SAPI5 speech synthesis | PASS |
| `pvporcupine` | `3.0.x` | Hotword wake-word engine | PASS |
| `mss` | `10.0.0` | Ultra-fast desktop screen capture | PASS |
| `Pillow` | `11.1.x` | Image manipulation & vision analysis | PASS |
| `pynput` | `1.8.1` | Global keyboard hotkey listener | PASS |
| `pyperclip` | `1.11.0` | Desktop clipboard read/write | PASS |
| `tenacity` | `9.1.4` | Resilience & retry decorators | PASS |
| `PySide6` | `6.11.0` | Legacy Qt desktop UI (transitional) | PASS |

---

## 5. Python Static Compilation & Module Imports
| Test Command | Output | Status |
| :--- | :--- | :--- |
| `python -m compileall -q .` | 0 Syntax Errors | **PASS** |
| `import main` | `MAIN_IMPORT_OK` | **PASS** |
| `import backend.main` | `BACKEND_IMPORT_OK` | **PASS** |
| `import sherly_core` | `CORE_IMPORT_OK` | **PASS** |
| `import sherly_ui.window` | `UI_IMPORT_OK` | **PASS** |

---

## 6. Pytest Automated Test Suite Baseline
| Metric | Result | Status |
| :--- | :--- | :--- |
| **Total Tests Discovered** | 81 | PASS |
| **Passed Tests** | **81 (100%)** | **PASS** |
| **Failed Tests** | 0 | PASS |
| **Skipped Tests** | 0 | PASS |
| **Test Execution Duration**| **1.24s** | PASS |

---

## 7. Frontend Build & Static Verification (`frontend/`)
| Metric | Result | Status |
| :--- | :--- | :--- |
| **TypeScript Typecheck (`tsc`)** | 0 Errors | **PASS** |
| **Vite Production Bundle** | Built in **2.42s** (1,833 modules transformed) | **PASS** |
| **Output Assets** | `dist/index.html` (0.59 kB), `dist/assets/index.css` (26.14 kB), `dist/assets/index.js` (212.80 kB) | **PASS** |

---

## 8. Ollama & Model Integration Baseline
| Item | Baseline Finding | Status |
| :--- | :--- | :--- |
| **Ollama Server** | Running locally on `http://127.0.0.1:11434` | **PASS** |
| **Detected Local Models** | `qwen2.5-coder:3b` (1.9 GB footprint, Code Specialist) | **PASS** |
| **Model Resolution Mode** | `AUTO` (resolves best coding model from local tags) | **PASS** |
| **Active Model** | `qwen2.5-coder:3b` | **PASS** |

---

## 9. Voice Pipeline Baseline
| Component | Implementation | Baseline Finding | Status |
| :--- | :--- | :--- | :--- |
| **Speech-to-Text (STT)** | `faster-whisper` (int8) | CTranslate2 local Whisper model | PASS |
| **Text-to-Speech (TTS)** | `pyttsx3` | SAPI5 Windows offline driver | PASS |
| **Audio Capture** | `sounddevice` | PortAudio stream capture | PASS |
| **Wake Word** | `pvporcupine` | Wake listener configured | PASS |

---

## 10. Security Baseline & Vulnerability Scan
| Scan Area | Finding | Status |
| :--- | :--- | :--- |
| **Static Secrets Scan** | No plain-text API keys found in tracked files. API keys stored via local `config_manager`. | **PASS** |
| **Shell Injection Auditing**| Dangerous shell invocations removed. Explicit `argv` lists used with `shell=False`. | **PASS** |
| **`npm audit`** | 2 moderate/high devServer advisories in `vite@5.4` / `esbuild` (dev server only). | **AUDITED** |

---

## 11. Functional Smoke Test Matrix
| Capability | Action Tested | Result | Status |
| :--- | :--- | :--- | :--- |
| **A. Core Initialization** | `main.py` startup & module resolution | Started cleanly with model detection | **PASS** |
| **B. Prompt Response** | Query `"hi"` / `"hello"` | Returned greeting without debounce | **PASS** |
| **C. Model Auto-Detection** | `model_scanner.scan_ollama_models()` | Detected `qwen2.5-coder:3b` | **PASS** |
| **D. Model Selection** | `config_manager.set_current_model()` | Switched active model in memory | **PASS** |
| **E. Voice Initialization** | Audio device enumeration | Detected default Windows input | **PASS** |
| **F. Web Search** | `search_web("latest news")` | Clean DuckDuckGo response | **PASS** |
| **G. File Operations** | `explain_file()` & `read_file()` | Read workspace source files | **PASS** |
| **H. Workspace Explorer** | File tree scanner | Scanned nested workspace tree | **PASS** |
| **I. Safety Approval** | `classify_action()` & `request_approval()` | Queued high-risk commands | **PASS** |
| **J. Preview & Diff** | Visual diff preview generation | Formatted old vs new changes | **PASS** |
| **K. Undo Engine** | `undo_last()` | Reverted previous file mutation | **PASS** |

---

## 12. Technical Debt & Modernization Backlog
1. **Consolidate HTTP Clients**: Currently both `requests` and `httpx` are installed. Migrate all sync calls to `httpx`.
2. **Upgrade `duckduckgo-search`**: Migrate upstream package name to `ddgs`.
3. **Hybrid Neural TTS**: Complement `pyttsx3` with `edge-tts` for natural speech output.
4. **Vite Dev Server Dependency Modernization**: Plan non-breaking update for `vite` / `esbuild`.
5. **Retain PySide6 in Transitional State**: Keep as fallback desktop shell while driving canonical features through React/Tauri.
