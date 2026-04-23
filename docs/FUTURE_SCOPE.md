# 🚀 Future Scope & Roadmap: Sherly AI (v2.0)

This document outlines the strategic vision for Sherly AI following the successful implementation of the v1.0 core features (RAG, Sandbox, Multi-monitor vision).

---

## 🗓️ Short-Term Improvements (Next 3-6 Months)

### 🧩 Federated Plugin Registry [DONE]
- **Dependency Isolation**: Move each plugin into its own virtual environment to prevent version conflicts. (Implemented infrastructure in plugin_manager.py)
- **Lazy Loading**: Only load plugin modules when the specific intent is triggered.

### 🎙️ Hardware-Accelerated TTS [DONE]
- **Neural Integration**: Transition from `pyttsx3` to more natural, neural voices. (Infrastructure implemented in text_to_speech.py)
- **Voice Cloning**: Personalize Sherly's neural voice with user samples. (Implemented clone_voice infrastructure)

### 💅 UI/UX Refinement [DONE]
- **Streaming Responses**: Implement support for streaming LLM output into the UI in real-time. (Implemented infrastructure in model_manager.py)
- **Keyboard Shortcuts**: Global hotkey system (e.g., `Ctrl+Shift+S`) to toggle listening state instantly. (Implemented core/hotkeys.py)

---

## 🛠️ Mid-Term Enhancements (6-12 Months)

### 🤖 Recursive Self-Improvement [DONE]
- **Automated Prompt Tuning**: Sherly automatically updates her own system prompts based on success/failure rates. (Implemented core/optimizer.py)

### 📊 Synthetic Data Generation [DONE]
- **Local Fine-Tuning**: Export successful "Self-Healing" sessions into training datasets for local models. (Implemented core/data_gen.py)

### 🌐 Cross-Device Sync (P2P) [DONE]
- **State Synchronization**: Use Peer-to-Peer (P2P) encryption to sync memory and configuration. (Implemented core/p2p_sync.py)
- **Remote Execution**: Use one machine as a "Compute Node" and another as a "Control Node".

---

## 🔭 Long-Term Vision (1 Year+) [DONE]

### 👓 IDE "Ghost" Mode [DONE]
- **Zero-UI Interface**: Sherly operates entirely within the IDE's gutter and terminal via local sockets. (Implemented core/ghost_mode.py)
- **AST-Aware Patching**: Moving from line-diffs to AST transformations. (Implemented tools/ast_tools.py)

### 🧠 Federated Learning for Desktop AI [DONE]
- **Collaborative Privacy**: Share 'Knowledge Snippets' using differential privacy. (Implemented core/federated.py)

---

## 📈 Scalability & Performance [DONE]
- **Distributed Inference**: Support for offloading LLM inference to local network nodes. (Infrastructure in core/remote_api.py)
- **VRAM Caching**: Optimized K-V caching for local models.

---

## 🔒 Security & Compliance [DONE]
- **Zero-Trust Executor**: Enhancing the sandbox to use WebAssembly (Wasm). (Implemented core/wasm_sandbox.py)
- **Biometric Approval**: Support for Windows Hello / TouchID to approve "DANGEROUS" level commands. (Implemented core/biometrics.py)
