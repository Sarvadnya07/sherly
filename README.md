# Sherly AI – Local-First Voice + Remote-Control Assistant

## Overview
Sherly is a desktop-native AI assistant that listens, thinks, executes, and notifies in real time. It blends local speech/LLM workflows with a remote web/PWA control surface, agent routing, and background task automation—optimized for low RAM and responsive UX.

## Features
- **Voice + UI**
  - Fast STT (Whisper tiny int8), debounce logic, short responses for snappy TTS.
  - PySide6 floating panel with status states (Idle/Listening/Thinking/Executing/Speaking).
- **Smart Routing**
  - LLM-based agent selection (coder/browser/system) for better intent mapping.
  - Plugin registry + tool routing for extensibility.
- **Remote Control**
  - FastAPI remote agent + public API gateway, PWA UI with mic and uploads, ntfy push notifications.
  - File upload endpoint auto-processes code/logs and pushes explanations to phone.
- **Automation & Tasks**
  - Background task scheduler, task queue, async worker helper to prevent UI blocking.
  - System automation via pyautogui, terminal commands, screen analysis.
- **Memory**
  - Dual memory: chat DB plus `memory_brain` key-value “personal brain” injected into prompts.
  - Prompt builder includes user context; DEV_MODE adds developer-style reasoning.
- **Notifications**
  - ntfy push after command/processing and uploads.
- **Safety & Performance**
  - Response/length caps, idle model unload, safe wrappers, controlled step executor (max 3 steps).

## Architecture / Folder Structure
```
agents/               # Coder/Browser/System agents
agent_manager.py      # LLM-driven agent classification + dispatch
core/                 # worker.py (run_async), task_queue.py
remote_agent/         # Local FastAPI executor calling route_command
remote_api/           # Public FastAPI proxy + PWA static mount + upload
remote_ui/            # PWA (index.html, manifest.json, icon.png)
sherly_ui/            # PySide6 window, tray, worker thread
tools/                # STT/TTS, screen, automation, task_engine, etc.
runtime_utils.py      # logging, safe_execute, safe_run, ntfy send_notification
model_manager.py      # prompt builder, model routing, idle unload, DEV_MODE
memory_brain.py       # persistent user facts
task_scheduler.py     # background interval tasks
command_router.py     # main intent router
requirements.txt
config.json
```

## Installation & Setup
```bash
pip install -r requirements.txt
# start desktop app
python main.py
# start local agent
uvicorn remote_agent.agent:app --host 127.0.0.1 --port 5001
# start remote API + PWA
uvicorn remote_api.server:app --host 0.0.0.0 --port 8000
```
Prereqs: Python 3.10+, Ollama running if using local LLM, ntfy mobile app (subscribe to `sherly-channel` or your chosen topic), microphone access.

## Usage
- Desktop: launch `main.py`, press Listen Once or enable auto-mode; speak commands (“open vscode”, “explain this code”).
- Remote: open `http://YOUR_IP:8000` (PWA), tap mic or upload file; API key via `key` query/`x-api-key` header (`SHERLY_REMOTE_API_KEY`, default `sherly123`).
- Memory: “remember project is sherly”, “what is project”.
- Background tasks: import `add_task`/`start_scheduler` to register periodic jobs.

## API
- `POST /command` (remote_api): `{text}` → `{response}` (requires API key).
- `POST /upload` (remote_api): file → saved to `uploads/`, auto explain via model, ntfy push.
- `POST /execute` (remote_agent): `{text}` → router response.

## Tech Stack
Python, FastAPI, PySide6, faster-whisper, pyttsx3, requests, ntfy, duckduckgo-search, pyautogui, Ollama (local LLM), PWA (HTML/CSS/JS).

## Configuration
- `config.json`: current_model, auto_mode, API keys, plugin toggles.
- Env: `SHERLY_REMOTE_API_KEY` for remote API; ntfy channel configurable in `runtime_utils.send_notification`.
- Models: set via voice (“use openai/gemini/groq/local”) or config.

## Performance
- STT tiny/int8; prompts short; responses clipped to 250 chars; `max_tokens=100`.
- Idle unload after 60s; async worker + task queue to avoid UI blocking.
- Expect sub-second UI responsiveness on typical laptops; remote API latency depends on network/LLM.

## Testing
- `python -m py_compile` over modules or targeted smoke runs.
- Manual: voice command, remote `/command`, file upload → ntfy push.

## Security
- API key required for remote endpoints; set strong `SHERLY_REMOTE_API_KEY`.
- ntfy topics are public by default—use a private/random channel.
- CORS open for remote_api; restrict origins in production.
- Uploaded files stored under `uploads/`—treat as untrusted.

## Deployment
- Desktop app: run `python main.py` (bundle with PyInstaller if desired).
- Remote services: `uvicorn remote_api.server:app` and `uvicorn remote_agent.agent:app` behind reverse proxy; optional `ngrok http 8000` for quick exposure.
- PWA served from remote_api static mount (`remote_ui/`).

## Documentation References
- Key modules: `command_router.py`, `model_manager.py`, `agent_manager.py`, `sherly_ui/app_manager.py`, `remote_api/server.py`, `remote_ui/index.html`.
- External: Ollama, ntfy.sh, FastAPI, faster-whisper docs.

## Contributing
- Fork, branch, keep responses capped/non-blocking; follow async/task queue patterns.
- Add tests or smoke steps for new features.

## License
MIT License.
