# Sherly AI – Voice-First Local Dev Copilot

## Overview
Sherly is a desktop-native, voice-controlled developer copilot for your local machine. It runs, debugs, and explains your projects hands-free, with a PWA remote control, controlled task execution, and lightweight local models.

## ⚙️ How It Works
Voice → STT → Intent Router → Agent Selection → Execution → Response → TTS → Notification

## 🎯 Product (MVP Lock)
Core promise: run, debug, and understand your code just by speaking.
- KEEP: voice run, error detection/explanation, safe terminal execution, file/code explanation, one-click “fix my project.”
- DROP: multi-agent complexity, camera/vision, excessive plugins, fancy automation.

## 🧠 Why Sherly?
- Works offline (local-first) and faster than cloud assistants.
- Voice-first debugging copilot: say “Run my project,” get error analysis and fixes.
- Extensible via agents/plugins, yet controlled for safety.
- Remote control from phone via PWA + notifications.

## 💬 Example
User: “open chrome”  
Sherly: Opening Chrome...

User: “summarize this log file”  
Sherly: This log indicates...

## 📸 UI
![Sherly UI](sherly_ui/assets/sherlyai.png)
Add a screenshot of the PySide6 panel or PWA for quick visual context.


## Features
- **Voice + UI**: Whisper tiny int8 STT, debounce, short responses for fast TTS; PySide6 panel with Idle/Listening/Thinking/Executing/Speaking.
- **Smart Routing**: LLM-based agent selection (coder/browser/system); plugin/tool registry.
- **Remote Control**: FastAPI remote agent + public API gateway; PWA with mic/upload; ntfy push notifications.
- **Automation & Tasks**: Background scheduler, task queue, async worker to avoid UI blocking; safe terminal execution (`safe_exec`).
- **Memory**: Chat DB + `memory_brain` key-value context injected into prompts; DEV_MODE for developer-style reasoning.
- **Reliability**: Retry + circuit breaker around local models, response caps, idle model unload, safe wrappers, controlled step executor (max 3 steps).

## Architecture / Folder Structure
```
agents/               # coder/browser/system agents
agent_manager.py      # LLM-driven agent classification + dispatch
core/                 # worker.py (run_async), task_queue.py
remote_agent/         # Local FastAPI executor calling route_command
remote_api/           # Public FastAPI proxy + PWA static mount + upload
remote_ui/            # PWA (index.html, manifest.json, icon.png)
sherly_ui/            # PySide6 window, tray, worker thread
tools/                # STT/TTS, screen, automation, task_engine, etc.
runtime_utils.py      # logging, safe_execute, safe_run, ntfy send_notification
model_manager.py      # prompt builder, model routing, idle unload, DEV_MODE, retry/breaker
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
Prereqs: Python 3.10+, Ollama running if using local LLM, ntfy mobile app (subscribe to your channel), microphone access.

## Usage
- Desktop: run `main.py`, click mic or auto-mode; speak “run my project” / “explain this code.”
- Remote: open `http://YOUR_IP:8000`, tap mic or upload file; API key via `key` query or `x-api-key` header (`SHERLY_REMOTE_API_KEY`, default `sherly123`).
- Memory: “remember project is sherly”; “what is project”.
- Background tasks: use `add_task` / `start_scheduler`.

## API
- `POST /command` (remote_api): `{text}` → `{response}` (API key).
- `POST /upload` (remote_api): file → saved to `uploads/`, auto explain + ntfy push.
- `POST /execute` (remote_agent): `{text}` → router response.

## Tech Stack
Python, FastAPI, PySide6, faster-whisper, pyttsx3, requests, ntfy, duckduckgo-search, pyautogui, Ollama (local LLM), tenacity + pybreaker, PWA (HTML/CSS/JS).

## Configuration
- `config.json`: current_model, auto_mode, API keys, plugin toggles.
- Env: `SHERLY_REMOTE_API_KEY` for remote API; ntfy channel in `runtime_utils.send_notification`.
- Models: switch via voice (“use openai/gemini/groq/local”) or config.

## Performance
- STT tiny/int8; prompts short; responses clipped to 250 chars; `max_tokens=100`.
- Idle unload after 60s; async worker + task queue to avoid UI blocking.
- Retry + circuit breaker for local models; fallback to lightweight web snippet on failure.

## Security
- API key required for remote endpoints (FastAPI dependency).
- Safe command execution allowlist; treat uploads as untrusted.
- CORS can be restricted; ntfy topics should be private/random.

## Deployment
- Desktop: `python main.py` or bundle with PyInstaller (`pyinstaller --noconsole --onefile main.py`).
- Remote: `uvicorn remote_api.server:app` and `uvicorn remote_agent.agent:app` behind reverse proxy; `ngrok http 8000` for quick share.
- PWA served from `remote_api` static mount.

## Landing Page Copy (for marketing)
- Hero: “Talk to Your Code. Sherly runs, debugs, and fixes your projects — hands-free.”
- Problem: tired of manual debugging, context switching, repeated commands?
- Solution: say “Run my project.” Sherly executes, finds errors, explains, suggests fixes.
- CTA: Download Sherly (Beta).

## Demo Script (30–45s)
Open Sherly → say “Run my project” → show error → Sherly explains → suggests fix → (optional) applies fix.

## Feedback Loop
Add lightweight in-app prompt: “Was this helpful? (y/n)” and log responses to refine accuracy/speed.

## Contributing
- Fork, branch, keep responses capped/non-blocking; follow async/task queue patterns.
- Add tests or smoke steps for new features.

## License
MIT License.
