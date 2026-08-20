# Sherly AI — Production Deployment & CI/CD Guide

**Target Version**: 2.0.0  

---

## 1. Production Deployment Models

### Model A: Local Desktop (Recommended)
- FastAPI runs bound to loopback `127.0.0.1:8000`.
- React desktop frontend connects over local WebSocket and REST.

### Model B: Headless Ghost Mode (Remote / Server)
```bash
python -m backend.main --ghost --port 5555
```

---

## 2. CI/CD Release Pipeline

The repository uses GitHub Actions (`.github/workflows/release.yml`):
1. **Lint & Test**: PyTest (115 tests), TypeScript typecheck, Vite build.
2. **Package**: Generates `release/release_manifest.json` with SHA-256 asset checksums.
3. **Artifact Upload**: Automated multi-platform asset uploads on `v*` version tags.
