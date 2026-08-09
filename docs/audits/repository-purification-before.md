# Repository Purification — Initial State Audit

**Date:** 2026-08-09T15:07:35+05:30  
**Branch:** `main`  
**Commit:** `dbcea7a` (HEAD → main, origin/main)  
**Status:** Clean working tree

## Git Branch Summary

- **Active Local Branch:** `main` (up to date with `origin/main`)
- **Remote Branches:** 100+ branches, predominantly Sentinel/Dependabot security fix branches that were merged or abandoned.
- **Tags:** `pre-tauri-migration` at `e4ed5d2`

## Recent Commits (HEAD~5)

```
* dbcea7a (HEAD -> main) Changed sherly UI/UX and stack + added model auto detection system
* e4ed5d2 (tag: pre-tauri-migration) pre-tauri-migration: Working Python/Qt codebase state
* 57f324a Merge pull request #25 from recovery_review_restore_src_layout
* fd8f51d Merge pull request #6 from sentinel-api-security-fixes
* a6f69e6 Merge pull request #12 from sentinel-auth-security-fix
```

## Critical Findings

### 1. GENERATED ARTIFACTS TRACKED IN GIT
- **7,374 files** in `frontend/node_modules/` are committed
- **71 `.pyc` files** are committed across multiple `__pycache__/` directories
- `src/sherly_ai.egg-info/` (build artifact) is committed
- `logs/sherly.log` (46 KB runtime log) is committed
- `sherly_memory.db` (41 KB SQLite runtime database) is committed

### 2. SECRET AUDIT
- `.env` is tracked but contains **placeholder values only** (`your_openai_api_key_here`, `your_gemini_api_key_here`). No real secret leakage detected in git history.
- `remote_ui/index.html` contains hardcoded API key `sherly123` for the remote API.

### 3. SUSPICIOUS ROOT FILES
- `=1.15.0`: Accidental pip install output for scipy (shell redirect artifact)
- `=2.0.0`: Accidental pip install output for numpy (shell redirect artifact)
- `test_numpy.py`: Diagnostic script (`pip install -e .`), NOT a test
- `test_voice.py`: Diagnostic script (TTS check), NOT a test

### 4. .GITIGNORE (DANGEROUSLY MINIMAL)
```gitignore
__pycache__/
*.pyc
```
Only 2 entries. Missing: `.env`, `node_modules/`, `logs/`, `*.db`, `dist/`, `build/`, `.egg-info/`, IDE files, OS files, etc.

### 5. ARCHITECTURE DUPLICATION MAP
| Area | Canonical | Legacy / Dead |
|---|---|---|
| UI Application | `sherly_ui/` (PySide6 Qt) + `frontend/` (React/Tauri) | `remote_ui/` (PWA), `src/sherly/main.py` |
| Agent System | `agents/` + `agent_manager.py` | `sherly_ai/` (2/3 files empty) |
| Command Tools | `tools/` (14 modules) | `sherly_commands/` (3/4 files empty) |
| Utilities | `runtime_utils.py` + `tools/*` | `sherly_utils/` (3/4 files empty), `developer_tools.py`, `screen_tools.py` |
| Task Scheduling | `runtime_utils.py` + `core/task_queue.py` | `task_scheduler.py`, `core/worker.py` |
| Plugin Loading | `plugin_manager.py` | `plugin_loader.py` |
| Notifications | `runtime_utils.py` | `notifier.py` |
| Backend API | `backend/` (FastAPI, port 8000) | `remote_api/` + `remote_agent/` |
| Configuration | `config_manager.py` + `config.json` | `config/settings.py` (0 bytes) |
| Source Package | Root-level flat modules | `src/sherly/` (empty skeleton except `atomic_writer.py`) |

### 6. DEAD MODULE INVENTORY
| File | Reason |
|---|---|
| `developer_tools.py` | Orphaned; never imported |
| `notifier.py` | Redundant re-export shim |
| `plugin_loader.py` | Superseded by `plugin_manager.py` |
| `screen_tools.py` (root) | Superseded by `tools/screen_tools.py` |
| `task_scheduler.py` | Superseded by `runtime_utils.py` |
| `sherly_utils/*` | 3/4 files are 0-byte; 1 file unreferenced |
| `sherly_commands/control_commands.py` | Unreferenced |
| `sherly_commands/dev_commands.py` | 0-byte stub |
| `sherly_commands/web_commands.py` | 0-byte stub |
| `sherly_ai/prompt_templates.py` | 0-byte stub |
| `sherly_ai/reasoning_engine.py` | 0-byte stub |
| `sherly_ui/assistant_panel.py` | 0-byte stub |
| `sherly_ui/mic_animation.py` | 0-byte stub |
| `sherly_ui/tray_icon.py` | Legacy; superseded by `app_manager.py` |
| `sherly_core/sherly_loop.py` | Broken imports |
| `core/worker.py` | Superseded by `core/task_queue.py` |
| `config/settings.py` | 0-byte stub |
| `src/sherly/main.py` | Obsolete entry point |
