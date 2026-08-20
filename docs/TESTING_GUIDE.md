# Sherly AI — Testing Strategy & Verification Guide

**Test Suite Size**: 115 Tests Passing  
**Framework**: PyTest, Vitest, Playwright  

---

## 1. Running Automated Tests

### Python Backend Suite
```bash
# Run all unit and integration tests
pytest tests/ -q

# Run specific test file
pytest tests/test_security.py -v
```

### Packaging & Integrity Verification
```bash
python scripts/package.py --verify
```

---

## 2. Test Suite Architecture

- **`tests/test_security.py`**: Validates SSRF defense, command injection blocking, path traversal rejection, and secret redaction.
- **`tests/test_policy.py`**: Validates action classification (`SAFE`, `CONFIRM`, `DANGEROUS`, `BLOCKED`).
- **`tests/test_action_manager.py`**: Validates 120s TTL expiration, idempotent approval, and deterministic rollback.
- **`tests/test_preview.py`**: Validates pre-write base state conflict detection.
