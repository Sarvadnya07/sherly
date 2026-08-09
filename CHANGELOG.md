# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Multi-agent swarm architecture for complex scaffolding tasks.
- Advanced visual UI debugger integration within PySide6 frontend.
- Extended cloud provider fallback option (disabled by default).

### Changed
- Refactored `command_router.py` to support dynamic plugin-based intent resolution.

## [1.15.0] - 2026-08-01

### Added
- Complete RAG (Retrieval-Augmented Generation) integration via ChromaDB for instantaneous project context loading.
- Git-style multi-file patch preview system implemented in `sherly_ui`.
- `undo` functionality for file modifications with atomic state backups.
- Secret redaction layer in `safety_guard.py` to prevent key leaks to the model context.

### Fixed
- Fixed an issue where `faster-whisper` would drop the first second of audio on Windows.
- Resolved memory leak in PySide6 UI during prolonged model execution.

## [1.14.2] - 2026-06-15

### Added
- Initial release of the deterministic router prioritizing safe known intents over LLM generation.
- Desktop UI (PySide6) with voice hotkey (`Ctrl + Shift + S`).

### Security
- Implemented `shlex.split()` for all terminal commands, enforcing `shell=False`.
