# Sherly v2.0.0 Production Release

**Version**: `2.0.0`  
**Git Commit**: `784d57a`  
**Release Date**: `2026-08-21`  
**Classification**: Official Production Release (General Availability)  

---

## 🌟 What's New in Sherly v2.0.0

Sherly 2.0 is a complete reimagining and modernization of the Sherly AI developer assistant.

### 1. Unified React + Tauri Desktop Foundation
- **Modern Desktop UX**: Fluid, dark-themed developer workspace with zero UI fabrication.
- **ChatGPT/Claude-Class Assistant**: Markdown code blocks with syntax highlighting, scoped search (`Ctrl+F`), native clipboard copy, smart auto-scroll, and instant generation stop.
- **Monospace Code Canvas**: Multi-tab code editor with line gutters, live cursor coordinates (`Ln X, Col Y`), dirty state tracking, and keyboard save (`Ctrl+S`).
- **Visual Patch Diff Review**: AI-generated code changes are presented as colorized unified diffs with explicit `Accept (Ctrl+Enter)` and `Reject (Esc)` controls.
- **Integrated Terminal**: Safe command runner with command history (Up/Down) and 400-line buffer capping.

### 2. Multi-Model & Local LLM Intelligence
- **Automatic Model Resolver**: Seamlessly auto-detects and connects to local Ollama models (`qwen2.5-coder:3b`), falling back cleanly when offline.
- **Model Pinned Authority**: Explicit manual mode prevents auto-detection from overriding user model choices.
- **Cloud Provider Integration**: Secure support for OpenAI, Gemini, and Groq API keys.

### 3. Voice & Realtime Modality
- **Desktop-First Voice Pipeline**: Hardware microphone capture via `sounddevice`, offline transcription via `faster-whisper`, and offline text-to-speech via `pyttsx3`.
- **Modality Convergence**: Spoken queries converge directly on the canonical Assistant model and tool capability pipeline.
- **Instant Cancellation**: Pressing `Esc` or clicking "Stop Speaking" terminates audio playback immediately with zero dangling background threads.

### 4. Enterprise Safety, Approval & Deterministic Undo
- **Server-Authoritative Policy Engine**: The LLM, voice transcripts, and frontend never decide whether an action is safe.
- **Immutable Approval Queue**: Consequential actions are bound to unique action IDs with 120s TTL expiration and idempotent execution.
- **Pre-Write Conflict Detection**: Refuses silent overwrites if a file is modified externally before patch approval.
- **Deterministic Undo**: Atomic pre-state backups restore original file states accurately.

### 5. Production Reliability & Observability
- **End-to-End Tracing**: `trace_id` and `request_id` propagate across HTTP headers and structured JSON logs.
- **Structural & Pattern Secret Redaction**: Sensitive keys and inline API tokens (`sk-...`) are sanitized before emission.
- **Scoped Circuit Breakers & Retries**: Transient network errors use exponential backoff with jitter; mutations are never blindly retried.
- **Fast Health Probes**: `/api/health` and `/api/health/providers` respond deterministically in under 20ms.

---

## 📦 Installation & Quickstart

```bash
git clone https://github.com/Sarvadnya07/sherly.git
cd sherly

# Setup virtual environment
python -m venv .venv
.venv\Scripts\activate   # Windows
pip install -r requirements.txt

# Launch application
python main.py
```
