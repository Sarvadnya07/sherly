# Sherly Release Engineering & Packaging Specification (Phase 14)

**Target Version**: 2.0.0  
**Classification**: Production Build & Packaging Pipeline  
**Status**: ACTIVE & PRODUCTION-READY  

---

## 1. Release Pipeline Overview

```text
Source Code
    ↓
Locked Dependencies (requirements.txt, package-lock.json)
    ↓
Python Compilation & PyTest Suite (109+ tests)
    ↓
Frontend Production Build (TypeScript + Vite)
    ↓
Packaging Orchestrator (scripts/package.py)
    ↓
Release Manifest & SHA-256 Checksums
    ↓
GitHub Release / Artifact Distribution
```

---

## 2. Configuration & Database Migration Strategy

1. **Schema Versioning**: `CURRENT_CONFIG_SCHEMA_VERSION = 2`.
2. **Pre-Migration Safety Snapshot**: When an older configuration schema is detected, `config_manager.py` automatically writes a backup copy to `config.json.bak` prior to applying schema migrations.
3. **Idempotency & Rollback**: Migrations are incremental and idempotent. If an invalid or corrupted schema is encountered, the engine rolls back safely to default safe settings without crashing the process.

---

## 3. Platform Verification Status

| Platform | Build Status | Install Status | Runtime Status |
| :--- | :--- | :--- | :--- |
| **Windows 10/11** | **BUILD VERIFIED** | **INSTALL VERIFIED** | **RUNTIME VERIFIED** |
| **macOS (Apple Silicon/Intel)** | **BUILD VERIFIED (CI)** | **NOT TESTED** | **NOT TESTED** |
| **Linux (Ubuntu/Debian)** | **BUILD VERIFIED (CI)** | **NOT TESTED** | **NOT TESTED** |
