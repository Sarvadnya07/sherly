# Sherly Production Operations Runbook (Phase 15)

**Target Audience**: DevOps Engineers, SREs, and System Administrators  
**Version**: 2.0.0  
**Status**: ACTIVE & OPERATIONAL  

---

## 1. Service Management & Operations

### Starting the Server (Production Local Mode)
```bash
# Activate environment
.venv\Scripts\activate   # Windows
source .venv/bin/activate # Linux/macOS

# Launch full application (FastAPI + Desktop UI)
python main.py
```

### Health Probes & Monitoring
- **Process Health**: `GET http://127.0.0.1:8000/api/health`
- **Provider Status**: `GET http://127.0.0.1:8000/api/health/providers`
- **Recent Timelines**: `GET http://127.0.0.1:8000/api/health/diagnostics`

---

## 2. Common Failure Modes & Recovery

| Issue | Root Cause | Resolution |
| :--- | :--- | :--- |
| **`Ollama is not reachable`** | Ollama daemon is not running on `localhost:11434`. | Start Ollama (`ollama serve`) or configure cloud API key in settings. |
| **`Port 8000 already in use`** | Lingering background process holding port 8000. | Set custom port: `export SHERLY_PORT=8080` (or `set SHERLY_PORT=8080`). |
| **`Config schema corrupted`** | Manual invalid JSON edits in `config.json`. | Remove invalid file or restore from `config.json.bak`; Sherly auto-recreates safe defaults. |
| **`Microphone device error`** | Audio device disconnected or locked by another app. | Select available input from the dropdown menu in Voice HUD. |
