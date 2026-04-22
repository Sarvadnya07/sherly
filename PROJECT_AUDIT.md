# 🔍 Project Improvement Audit: Sherly AI

This audit provides a critical analysis of the current codebase and architectural state, identifying areas for immediate remediation and long-term enhancement.

---

## 🛑 REQUIRED CHANGES (High Priority)

### 1. Robust Dependency Management
- **Issue**: `requirements.txt` is missing version pinnings, which will lead to "it works on my machine" failures as upstream packages (like `faster-whisper` or `fastapi`) update.
- **Fix**: Use `pip-compile` or `Poetry` to generate a lockfile with exact versions.

### 2. Comprehensive Error Handling in `command_router.py`
- **Issue**: Many routes use `safe_execute` which returns a string on failure, but doesn't always provide sufficient context for the AI or user to fix the underlying issue (e.g., missing binaries).
- **Fix**: Implement structured error types and a dedicated diagnostic tool to verify environment health (Ollama status, mic access, etc.).

### 3. Missing Unit & Integration Tests
- **Issue**: The project lacks a test suite. Only `test_voice.py` exists, which is insufficient for an orchestrator of this complexity.
- **Fix**: Implement `pytest` suites for:
    - Intent classification logic in `classify_action`.
    - Undo/Redo stack reliability in `action_manager`.
    - Safe-execution whitelist filtering in `runtime_utils`.

### 4. Hardware/Environment Pre-flight Scaling
- **Issue**: `main.py` checks for modules but not for hardware requirements (e.g., minimum 8GB RAM for local LLMs).
- **Fix**: Add a hardware telemetry check to warn users if their system might struggle with the selected model.

---

## ✨ OPTIONAL ENHANCEMENTS (Medium to Low Priority)

### 1. Sandbox Execution
- **Architecture**: Move away from `subprocess.Popen` on the host machine for "confirm" level commands. 
- **Benefit**: Using a containerized environment (Docker/Podman) prevents accidental `pip install` conflicts or environment corruption during AI-driven fixes.

### 2. Telemetry & Observability
- **Feature**: Add an optional (opt-in) telemetry layer to track success rates of "Self-Healing" loops.
- **Benefit**: This data can be used to fine-tune the prompt templates in `model_manager.py` for higher accuracy.

### 3. Advanced Memory RAG
- **Architecture**: The current memory is key-value based (SQL/JSON). 
- **Benefit**: Transitioning to a Vector Database (like ChromaDB) would allow Sherly to "read" your entire project history and documentation to answer much more complex architectural questions.

### 4. Multi-Modal Vision
- **Feature**: Enhance `analyze_screen` to support multi-monitor setups and regional captures.
- **Benefit**: More accurate debugging when the error is visible in one window (e.g., a browser console) while the code is in another.

---

## 🛠️ Code Quality & Refactoring Suggestions

| Location | Suggestion | Rationale |
| :--- | :--- | :--- |
| `command_router.py` | Break into sub-routers (e.g., `file_router`, `dev_router`) | The file is exceeding 500 lines and becoming difficult to maintain. |
| `action_manager.py` | Use a persistent DB for history | Currently, the history is in-memory (`deque`). A restart wipes your undo stack. |
| `sherly_ui/` | Implement QSS (Qt Style Sheets) | Centralizing styles will make theme switching (Dark/Light) much more robust. |
| `agents/` | Abstract the Agent base class | standardizing `run()` and `stop()` methods across all agents for better lifecycle management. |

---

## 🛡️ Security Audit Notes
- **Prompt Injection**: The current `input_validator.py` is a great start, but should be supplemented with a more robust LLM-based "intent firewall" for high-risk commands.
- **API Key Management**: Move all cloud provider keys (OpenAI, Gemini) into a `.env` file and ensure it is included in `.gitignore`. **(CRITICAL)**
