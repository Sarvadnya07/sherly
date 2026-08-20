# Changelog

All notable changes to the **Sherly AI** project are documented in this file.

## [2.0.0] - 2026-08-21

### Added
- **Modern React + Tauri Desktop Foundation**: High-performance developer workspace with multi-tab editor, line numbering, terminal runner, and patch review diffs.
- **ChatGPT/Claude-Class Assistant UX**: Markdown code blocks with syntax highlighting, scoped search (`Ctrl+F`), native selection/copy, and stop generation.
- **Local & Multi-Model Intelligence**: Automated Ollama resolver, `qwen2.5-coder:3b` integration, pinned manual mode, and cloud API support.
- **Voice & Realtime Modality**: Low-latency STT via `faster-whisper`, TTS via `pyttsx3`, live transcription display, and instant cancellation.
- **Safety, Approval & Undo Architecture**: Server-authoritative `PolicyEngine`, immutable pending action queue (120s TTL), conflict protection, and deterministic undo.
- **Reliability & Observability**: Boundary correlation IDs (`trace_id`, `request_id`), structural secret redaction, and scoped circuit breakers.
- **Release & Packaging Pipeline**: Automated packaging orchestrator (`scripts/package.py`), SHA-256 release manifests, and GitHub Actions CI/CD workflows.

### Changed
- Refactored backend into structured FastAPI REST and WebSocket event architecture.
- Upgraded configuration schema to `CURRENT_CONFIG_SCHEMA_VERSION = 2` with automatic pre-migration backups (`config.json.bak`).

### Fixed
- Fixed thread-safety race conditions in configuration and action manager queues.
- Fixed pre-write patch conflicts when files are externally modified prior to approval.
- Fixed audio resource leaks with deterministic cleanup on stream termination and process shutdown.
