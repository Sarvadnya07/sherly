# 🚀 Sherly AI: The Definitive User Guide

Welcome to the future of hands-free autonomous development. This guide covers every feature from basic voice commands to advanced production deployments.

---

## 🛠️ Prerequisites

| Requirement | Purpose | Install |
| :--- | :--- | :--- |
| **Python 3.10+** | Core runtime | [python.org](https://python.org) |
| **Ollama** | Local LLM inference | `winget install Ollama.Ollama` |
| **Git** | Version control integration | [git-scm.com](https://git-scm.com) |
| **pip-tools** | Reproducible dependency locking | `pip install pip-tools` |

> [!NOTE]
> Docker is no longer required — the hardened sandbox now uses subprocess + filesystem escape detection with an optional `wasmtime` backend (FS-#11).

---

## 🏁 Quick Start

```powershell
# 1. Clone & install
git clone https://github.com/Sarvadnya07/sherly.git
cd sherly
pip install -e .

# 2. Configure
cp .env.example .env
# Add your API keys (optional — works offline with Ollama)

# 3. Install pre-commit hooks (recommended)
pip install pre-commit
pre-commit install

# 4. Launch (standard UI mode)
python src/sherly/main.py

# 5. Or headless mode (no UI, for Docker/server)
python src/sherly/main.py --headless
```

---

## ⚡ LLM Backends

Sherly supports four inference backends. Set `model` in `config.json` or switch at runtime:

| Backend | Config value | Env var | Notes |
| :--- | :--- | :--- | :--- |
| **Local (Ollama)** | `"phi3"` / `"llama3:8b"` | `OLLAMA_BASE_URL` | Auto health-checked before every call |
| **OpenAI** | `"openai"` | `OPENAI_API_KEY` | GPT-4o-mini |
| **Gemini** | `"gemini"` | `GEMINI_API_KEY` | Gemini 1.5 Flash |
| **Groq** | `"groq"` | `GROQ_API_KEY` | Llama3-70B, fastest free tier |

### Streaming (RC-8)
All four backends support token-by-token streaming. The `/infer/stream` SSE endpoint yields chunks live. Switch the model at any time — `stream_model()` handles the backend routing automatically.

---

## 🔒 Security Features

### Multi-Layer Input Validation
Every user input passes through **3 independent guards** before execution:

1. **Primary Regex Filter** — 40+ injection patterns (SQL, shell, jailbreak)
2. **Hardened Regex Firewall** — DAN mode, developer mode, sudo override — runs even when LLM is offline
3. **LLM Intent Firewall** — semantic classification (optional, fail-safe)

### Biometric Approval (RC-2)
DANGEROUS commands trigger a three-tier identity check:
- **Tier 1**: Windows Hello via WinRT `UserConsentVerifier` (fingerprint/face/PIN)
- **Tier 2**: Windows MessageBox PIN/password dialog
- **Tier 3**: Text `APPROVE` prompt (headless / Linux / CI)

### Sandbox Execution (FS-#11)
All untrusted code runs in an isolated environment:
- **Tier 1**: `wasmtime` WASM runtime (zero-trust: no FS, no network by default)
- **Tier 2**: Hardened subprocess sandbox with filesystem escape detection

```python
from sherly.core.wasm_sandbox import WasmSandbox
sandbox = WasmSandbox()
result  = sandbox.execute_wasm("tool.wasm", "run", [])
```

---

## 🎮 Feature Guide

### 1. 🎙️ Voice Commands
```
"Scan this project"           → Deep scan & incremental RAG indexing
"Fix the last error"          → Captures traceback, applies AST-aware patch
"Switch to Groq model"        → Hot-swaps backend (no restart needed)
"Export training data"        → Generates Alpaca-format fine-tuning dataset
"Show recent actions"         → Lists last 5 actions with undo flags
"Undo last action"            → Reverts file writes, deletes, and shell commands
```

### 2. 🔄 Undo Engine (FS-#6)
Sherly tracks reversible actions automatically:

| Action | Undoable? | Method |
| :--- | :--- | :--- |
| Write file | ✅ | Restores previous content |
| Delete file | ✅ | Moves `.bak` backup back |
| `mkdir foo` | ✅ | Runs `rmdir foo` |
| `mv a b` | ✅ | Runs `mv b a` |
| `shutdown` | ❌ | Irreversible — blocked |

### 3. 🧠 Incremental RAG (FS-#23)
The first `index_project` is slow. Every subsequent call only re-indexes changed files:
```
[RAG] Incremental scan: 3 to index, 847 unchanged (skipped).
[RAG] Incremental index complete: 3 files re-indexed, 847 unchanged.
```

### 4. 🛠️ AST-Aware Patching (FS-#26)
```python
from sherly.tools.ast_tools import ASTPatcher
patcher = ASTPatcher()

# Rename a function everywhere it appears
new_src = patcher.rename_symbol(source, "old_fn", "new_fn")

# Inject a missing import
new_src = patcher.add_import(source, "import asyncio")

# Replace a class method body
new_src = patcher.patch_class_method(source, "MyClass", "run", "return 42")
```

### 5. 🔌 LSP Integration (FS-#13)
Get real IDE-quality diagnostics from any Language Server:
```python
from sherly.tools.lsp_client import analyze_file_with_lsp

report = analyze_file_with_lsp("src/sherly/main.py")
# → [ERROR] L42:5 — undefined name 'foobar'
```
Supported servers (auto-detected by extension): `pylsp`, `typescript-language-server`, `rust-analyzer`, `gopls`.

### 6. 👻 Ghost Mode (OE-1)
Run Sherly without any UI for server / Docker deployments:
```powershell
# Terminal 1 — start the daemon
python src/sherly/main.py --headless

# Terminal 2 — send commands via TCP socket (port 5555 by default)
echo '{"command": "scan project"}' | nc localhost 5555
```
Change the port in `config.json → ghost_mode_port`.

### 7. 🌐 Remote Inference Gateway (FS-#17)
Offload heavy LLM inference to a GPU machine on your network:
```powershell
# On the GPU machine (Compute Node)
SHERLY_API_TOKEN=my-secret python -m sherly.core.remote_api

# On your laptop (Control Node) — call it
curl -H "Authorization: Bearer my-secret" \
     -H "Content-Type: application/json" \
     -d '{"prompt": "explain this code"}' \
     http://gpu-machine:8080/infer

# Streaming endpoint (SSE)
curl -H "Authorization: Bearer my-secret" \
     -H "Content-Type: application/json" \
     -d '{"prompt": "write a pytest fixture"}' \
     http://gpu-machine:8080/infer/stream
```

### 8. 👥 Multi-User Sessions (FS-#15)
Each API client gets isolated state (mode, phase, pending actions):
```python
from sherly.core.session_manager import get_session_manager
mgr = get_session_manager()
ctx = mgr.get_or_create("user_token_abc")
ctx.mode  = "dev"
ctx.phase = "C"
# State is fully isolated from all other sessions
```

### 9. 🗄️ Database Backend Switching (FS-#16)
Switch from SQLite (default) to PostgreSQL without changing any application code:
```json
// config.json
{
  "db_backend": "postgresql",
  "postgresql": {
    "host": "db.example.com",
    "port": 5432,
    "database": "sherly_prod",
    "user": "sherly",
    "password": "..."
  }
}
```

### 10. 🤝 Federated Knowledge (FS-#12)
Share anonymized fix patterns with other Sherly nodes using differential privacy:
```python
from sherly.core.federated import FederatedKnowledge
fed = FederatedKnowledge()

snippet = fed.generate_snippet(
    error_trace="ImportError: No module named 'requests'",
    solution="pip install requests",
)
# Snippet is Laplace-noised, path-scrubbed, PII-stripped, and HMAC-signed
fed.share_knowledge(snippet)   # Broadcasts to P2P mesh
```

---

## 📜 Command Reference

| Intent | Command Example | Action |
| :--- | :--- | :--- |
| **Analyze** | *"Scan this project"* | Incremental RAG indexing |
| **Dev Ops** | *"Run tests and fix failures"* | `pytest` in sandbox + auto-patch |
| **Security** | *"Sanitize my logs"* | Redacts 15+ secret formats |
| **Undo** | *"Undo last action"* | Reverts writes, deletes, shell cmds |
| **Train** | *"Export training data"* | Alpaca JSONL from telemetry+feedback |
| **System** | *"Switch to Groq"* | Hot-swaps LLM backend |
| **Web** | *"Search latest Python docs"* | DuckDuckGo + LLM summary |
| **Biometrics** | *(triggered automatically)* | Windows Hello → PIN → text gate |

---

## 🆘 Troubleshooting

| Problem | Fix |
| :--- | :--- |
| **Ollama slow / not starting** | Run `ollama serve`; check GPU with `nvidia-smi` |
| **Sandbox permission error** | Check `temp_dir` is writable; ensure no AV blocking |
| **Ghost Mode port in use** | Set `ghost_mode_port` in `config.json` to a free port |
| **LSP not found** | Run `pip install python-lsp-server` for Python analysis |
| **Remote gateway 401** | Set `SHERLY_API_TOKEN` env var on both client and server |
| **Rate limit hit** | Increase `llm_rate_limit_per_minute` in `config.json` |

---

## 🧪 Running Tests

```powershell
# Full suite (214 tests across 17 files)
python -m pytest tests/ -v

# With coverage
python -m pytest tests/ --cov=src/sherly --cov-report=term-missing

# Specific module
python -m pytest tests/test_safety_guard.py tests/test_sanitizer.py -v
```

---

> [!TIP]
> Use the **Global Hotkey** (`Ctrl+Shift+S`) to toggle Sherly's listening mode instantly.
> In headless mode, use the TCP socket interface or the REST gateway instead.
