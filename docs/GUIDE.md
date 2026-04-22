# 🚀 Sherly AI: The Definitive User Guide

Welcome to the future of hands-free development. This guide will take you from installation to mastering Sherly's most advanced autonomous features.

---

## 🛠️ Prerequisites

Before running Sherly, ensure you have the following installed:
1. **Python 3.10+**: The core runtime.
2. **Ollama**: For local LLM inference (Llama 3 or Phi-3 recommended).
3. **Docker Desktop**: Required for the **Hardened Sandbox** execution.
4. **Git**: For version control integration.

---

## 🏁 Quick Start

1. **Clone & Install**:
   ```powershell
   git clone https://github.com/Sarvadnya07/sherly.git
   cd sherly
   pip install -e .
   ```

2. **Initialize Config**:
   ```powershell
   cp .env.example .env
   # Add your API keys (optional) or use local Ollama
   ```

3. **Launch Sherly**:
   ```powershell
   python src/sherly/main.py
   ```

---

## 🎮 Practicing the Features

### 1. 🎙️ Voice Commands (The Core)
Sherly listens for your intent. Try these out loud:
- *"Sherly, scan this project and tell me what it does."*
- *"Sherly, refactor the model_manager to use a singleton pattern."*
- *"Sherly, fix the last error in my terminal."*

### 2. 🛡️ The Intent Firewall
When you ask Sherly to do something dangerous (like `rm -rf`), you will see the **Biometric Approval** or **Confirmation** overlay.
- **Practice**: Ask Sherly to *"delete the temporary logs folder"*. 
- **Observation**: Watch as Sherly identifies the "DANGEROUS" intent and requests your explicit approval.

### 3. 🩹 Self-Healing Loops
If a command fails, Sherly can automatically debug it.
- **Practice**: Create a file with a syntax error and run it.
- **Command**: *"Sherly, run main.py and fix any errors that occur."*
- **Observation**: Sherly will capture the traceback, analyze it via RAG, and apply an **AST-Aware Patch**.

### 4. 👻 Ghost Mode (IDE Integration)
Run Sherly without a UI, directly in your terminal/IDE.
- **Setup**: Start the Ghost server in one terminal: `python src/sherly/core/ghost_mode.py`.
- **Usage**: Send JSON commands via socket (port 5555) to see Sherly respond in the IDE gutter.

### 5. 🌐 P2P Sync Demo
If you have two machines on the same network:
- **Command**: *"Sherly, sync my current session with my laptop node."*
- **Observation**: Sherly generates an encrypted P2P packet using your unique storage key and broadcasts it to the mesh.

---

## 📜 Master Command Reference

| Intent Category | Voice Command Example | Action Taken |
| :--- | :--- | :--- |
| **Analysis** | *"Analyze my project"* | Deep scan & RAG indexing |
| **Dev Ops** | *"Run tests and report failures"* | Executes `pytest` in Sandbox |
| **Security** | *"Sanitize my logs"* | Redacts PII/Secrets via LogSanitizer |
| **UI** | *"Show status overlay"* | Displays the glassmorphism HUD |
| **System** | *"Switch to Llama3 model"* | Hot-swaps the active LLM backend |

---

## 🆘 Troubleshooting
- **Mic not detected?** Check `src/sherly/services/speech_to_text.py` for device indexing.
- **Ollama slow?** Ensure you have enabled GPU acceleration in Ollama settings.
- **Sandbox failed?** Ensure the Docker daemon is running (`docker ps` should work).

---

> [!TIP]
> Use the **Global Hotkey** (`Ctrl+Shift+S`) to toggle Sherly's listening mode instantly without clicking the UI.
