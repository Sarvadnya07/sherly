# Sherly AI — Configuration & Model Resolver Guide

**Target System**: Runtime Configuration, Environment Variables, Model Resolution  
**Version**: 2.0.0  

---

## 1. Environment Variables Reference (`.env`)

```ini
# ==============================================================================
# Sherly AI — Production Environment Template
# ==============================================================================

# Network & Server Bindings
SHERLY_PORT=8000
SHERLY_HOST=127.0.0.1

# Remote API Server Authentication (Constant-Time Token)
SHERLY_REMOTE_API_KEY=your_secure_remote_api_key_here

# Optional Cloud Providers (Leave blank for 100% offline Ollama inference)
OPENAI_API_KEY=your_openai_key_here
GEMINI_API_KEY=your_gemini_key_here
GROQ_API_KEY=your_groq_key_here

# Wake-Word Hardware Engine (Picovoice Porcupine)
PVPORCUPINE_ACCESS_KEY=your_picovoice_access_key_here
```

---

## 2. Local Runtime Settings (`config.json`)

`config.json` stores mutable user preferences, audio configurations, and model bindings:

```json
{
  "mode": "auto",
  "selected_model": "qwen2.5-coder:3b",
  "auto_unload_idle_seconds": 120,
  "max_history_turns": 10,
  "voice": {
    "whisper_model": "base.en",
    "tts_rate": 180,
    "tts_volume": 1.0,
    "mic_device_index": null
  },
  "security": {
    "max_upload_size_mb": 10,
    "max_prompt_length": 4000,
    "require_approval_for_writes": true
  }
}
```

---

## 3. Model Resolver Algorithm (`sherly_core/model_resolver.py`)

The Model Resolver determines which model processes incoming requests according to strict prioritization:

```mermaid
flowchart TD
    classDef stepNode fill:#1e293b,stroke:#38bdf8,stroke-width:2px,color:#f8fafc;
    classDef resolveNode fill:#064e3b,stroke:#10b981,stroke-width:2px,color:#d1fae5;
    classDef failNode fill:#881337,stroke:#f43f5e,stroke-width:2px,color:#ffe4e6;

    START["Query Model Resolver"]:::stepNode --> MODE{"Resolver Mode?"}:::stepNode
    
    MODE -- "manual" --> MAN{"Is Selected Model Available?"}:::stepNode
    MAN -- "Yes" --> USE_MAN["🎯 Use configured selected_model"]:::resolveNode
    MAN -- "No" --> FAIL["⚠️ Raise Resolution Error (Fail-Closed)"]:::failNode
    
    MODE -- "auto" --> SCAN{"Scan Ollama API (127.0.0.1:11434)"}:::stepNode
    SCAN -- "Local Models Found" --> AUTO_LOCAL["🚀 Auto-Select Best Coding Model<br/>(qwen2.5-coder / deepseek-coder)"]:::resolveNode
    SCAN -- "Ollama Offline" --> CLOUD{"Check Cloud API Keys (.env)"}:::stepNode
    
    CLOUD -- "GROQ_API_KEY Set" --> USE_GROQ["⚡ Fallback to Groq llama3-70b"]:::resolveNode
    CLOUD -- "GEMINI_API_KEY Set" --> USE_GEM["⚡ Fallback to Gemini 1.5 Flash"]:::resolveNode
    CLOUD -- "OPENAI_API_KEY Set" --> USE_OAI["⚡ Fallback to OpenAI gpt-4o-mini"]:::resolveNode
    CLOUD -- "No Keys Set" --> OFFLINE["⚠️ Offline Mode (Deterministic Only)"]:::failNode
```

---

## 4. Customizing Allowed Binaries (`ALLOWED_PREFIXES`)

To whitelist additional CLI tools for `safe_exec`, update `ALLOWED_PREFIXES` in `tools/terminal_tools.py`:

```python
ALLOWED_PREFIXES: tuple[str, ...] = (
    "python", "pip", "git", "uvicorn", "npm", "node",
    "pytest", "mypy", "ruff", "cargo", "docker", "ollama",
    "echo", "dir", "ls", "cat", "type", "cls", "clear"
)
```
