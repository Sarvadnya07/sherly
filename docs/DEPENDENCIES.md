# Sherly AI — Dependency & Runtime Specification

**Modernization Phase**: PHASE 1 — Dependency & Runtime Modernization  
**Specification Level**: Production / Strict Compatibility  

---

## 1. Runtime Environment Matrix

| Runtime / Engine | Target Version | Tested & Validated | Architecture |
| :--- | :--- | :--- | :--- |
| **Python** | `>=3.10, <3.14` | `3.13.9` | Windows x86_64 |
| **Node.js** | `>=18.0.0` | `26.2.0` | V8 / ESM |
| **NPM** | `>=9.0.0` | `11.6.2` | Workspace package manager |
| **Rust / Cargo** | `>=1.75.0` | `1.97.1` | Native Tauri 2 compilation |
| **Ollama Local Engine** | `>=0.3.0` | `0.32.14` | Local model inference (REST / WebSocket) |

---

## 2. Python Backend & Core Dependencies

| Package | Modernized Specification | Installed | Rationale & Modernization Notes |
| :--- | :--- | :--- | :--- |
| **`fastapi`** | `>=0.115.0` | `0.115.x` | Core async ASGI API routing. Auto-generates OpenAPI contracts. |
| **`uvicorn`** | `>=0.34.0` | `0.52.4` | High-throughput ASGI server engine with WebSocket support. |
| **`pydantic`** | `>=2.10.0` | `2.13.4` | Strongly-typed schema serialization powered by Rust pydantic-core. |
| **`httpx`** | `>=0.28.0` | `0.28.1` | **Consolidated HTTP Client**: Replaces `requests` across all sync and async outbound LLM and API calls. |
| **`ddgs` / `duckduckgo-search`** | `>=9.0.0` | `8.1.0` / `9.0.0` | Modernized search integration without runtime deprecation warnings. |
| **`tenacity`** | `>=9.1.0` | `9.1.4` | Deterministic retry decorator for network/LLM calls. |
| **`sounddevice`** | `>=0.5.0` | `0.5.5` | PortAudio low-latency voice capture stream. |
| **`numpy`** | `>=2.2.0, <3.0` | `2.2.x` | Numerical array operations for audio processing. |
| **`faster-whisper`** | `>=1.1.0` | `1.1.1` | Quantized local Whisper STT powered by CTranslate2 (int8). |
| **`pyttsx3`** | `>=2.98` | `2.99` | Local offline SAPI5 speech synthesis. |
| **`pvporcupine`** | `>=3.0.0` | `3.0.x` | Wake-word listener for voice trigger. |
| **`mss`** | `>=10.2.0` | `10.0.0` | Fast multi-monitor screen capture. |
| **`Pillow`** | `>=12.3.0` | `11.1.x` | Image processing for vision tools and icon extraction. |
| **`pyperclip`** | `>=1.11.0` | `1.11.0` | Cross-platform clipboard accessor. |
| **`pynput`** | `>=1.8.0` | `1.8.1` | Global keyboard hotkey listener (`Ctrl+Shift+L`). |
| **`PySide6`** | `>=6.8.0` | `6.11.0` | Transitional / legacy desktop window shell. |

---

## 3. Frontend Dependencies ([`frontend/package.json`](file:///c:/Users/ASUS/Desktop/STUDY/PROJECTS/sherly/frontend/package.json))

| Package | Specification | Role & Modernization Notes |
| :--- | :--- | :--- |
| **`react` / `react-dom`** | `^18.3.1` | Declarative UI framework with concurrency support. |
| **`typescript`** | `^5.4.5` | Strict static typing for contracts and components. |
| **`vite`** | `^5.2.13` | Instant HMR development server and fast production bundler. |
| **`tailwindcss`** | `^3.4.4` | Atomic CSS engine mapped to obsidian dark tokens. |
| **`zustand`** | `^4.5.2` | Minimalist atomic state store connected to WebSockets. |
| **`@tauri-apps/api`** | `^2.11.1` | Native Tauri 2 window controls, dialogs, and IPC. |
| **`@tauri-apps/plugin-shell`** | `^2.3.5` | Controlled shell execution bridge. |
| **`lucide-react`** | `^1.30.0` | Accessible tree-shakeable SVG icons. |

---

## 4. Upgrades, Consolidations & Deprecations Summary

1. **`requests` Consolidated into `httpx`**:
   - Eliminated redundant HTTP client library.
   - All outbound calls in `model_manager.py`, `runtime_utils.py`, `remote_api/server.py`, and `sherly_ui/app_manager.py` migrated to `httpx.post()` / `httpx.get()` with explicit timeouts.
2. **`duckduckgo-search` Upgraded to `ddgs`**:
   - Eliminated upstream package rename runtime warnings.
   - Preserved graceful offline / timeout fallback in `web_search.py`.
3. **PySide6 Kept Transitional**:
   - Preserved for desktop fallback while consolidating future features in React / Tauri.
